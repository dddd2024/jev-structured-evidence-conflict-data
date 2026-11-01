#!/usr/bin/env python3
"""A461-MECH-M21 R1: CPU freeze of the high-energy readout test (zero model forwards; torch CPU on the M18 features).

M19 (f2256e8): amplifying the held-out *probe* direction at the certificate_action <decide> token was inert, but that
direction carries ~0.6% (L19) / 0.06% (L31) of |h|, so the dose test was weak; in head-input space the conflict
direction is ~orthogonal to the reject - accept gradient. M21 uses the high-energy direction instead: u = the held-out
class-mean difference (mean new - mean BENIGN of the decide-token residual after layer L, over the 16 training groups),
normalised. Two operation families at L in {19, 31}, only at the certificate_action <decide> token:
  gain  h' = h + (gamma - 1) (h.u - c) u, gamma in {8, 32}   (input-dependent; c = training BENIGN mean of h.u)
  push  h' = h + beta |h| u, beta in {0.05, 0.2}              (dose-calibrated, input-independent)
  rand  h' = h + 0.2 |h| v, v a seeded random unit direction  (control for push)
Plain replays of all 620 M18 rows (bitwise == M18). 620 x (1 + 2 x 5) = 6820 calls.
"""
import argparse, collections, hashlib, json, subprocess, sys
from pathlib import Path

import torch

ROOT = (Path.home() / "wjc").resolve()
BLOB_M18_DESIGN = "1998024bffc0e8deee2cbf0d563eafbffad6bfef"
BLOB_M18_MANIFEST = "88f99a1827ad428515a9620408ae74c3545af0db"
BLOB_M18_RAW = "10e04cfadfaba7364abbb2eeb922b92c09ad9ea4"
LAYERS = [19, 31]
GAMMAS = [8.0, 32.0]
BETAS = [0.05, 0.2]
RAND_BETA = 0.2
NAMES = ["emb", "L3", "L7", "L11", "L15", "L19", "L23", "L27", "L31"]
PLAN_CAP = 128

PREREG = {
    "direction": "u_{L,g} = (mean over training-group new rows - mean over training-group BENIGN rows) of the decide-token "
                 "residual after layer L, normalised; training groups = all source groups except g; applied only to "
                 "rows of group g (held out). BENIGN = old / SA / ROUND / OUTSIDER rows not rejected natively (M18)",
    "operations": "only at the <decide> token of the certificate_action row, on the residual output of layer L: gain "
                  "h + (gamma - 1)(h.u - c) u with c = training BENIGN mean of h.u, gamma 8 / 32; push h + beta |h| u, "
                  "beta 0.05 / 0.2; rand h + 0.2 |h| v with v a unit Gaussian direction seeded per row and layer",
    "sets": "as M19: MISSED 84, RECOGNIZED 40, BENIGN 483 (from the replays' native action)",
    "measures": "REPAIR (MISSED -> reject_conflict), FV per benign arm, RECOGNIZED kept, median dA; group-level FV count "
                "with Clopper-Pearson bound; group bootstrap",
    "verdict": "per layer: CAUSAL_SELECTIVE iff some gain gamma has REPAIR >= 0.5 and FV <= 0.05 on every benign arm; "
               "CAUSAL_PUSH_ONLY iff no gain arm qualifies but some push beta has REPAIR >= 0.5 with "
               "REPAIR - FV_max >= 0.30 and rand (beta 0.2) has REPAIR <= REPAIR(push 0.2) - 0.30; "
               "NOT_READABLE iff every gain and push arm has REPAIR < 0.5; else NONSELECTIVE",
    "consistency_gate": "620 replays bitwise == M18; every op row reaches only the certificate_action row (runner); "
                        "conditions as planned; otherwise INCONSISTENT",
    "interpretation_fixed_in_advance": (
        "CAUSAL_SELECTIVE: the conflict information already present at the decide token is usable by the readout "
        "when its own deviation is amplified - an under-weighted readout, shown causally (closes M19's open question). "
        "CAUSAL_PUSH_ONLY: the conflict direction can drive the readout, but only as an input-independent push, which "
        "is not conditional on a conflict being present in the row; the readout reads the direction but the "
        "per-row conflict signal along it is too weak. NOT_READABLE: even a push of 20% of |h| along the conflict "
        "direction does not move the decision - the readout does not read this direction at all (consistent with the "
        "M19 orthogonality). Level S1-S2; not a defence (needs rule-labelled data)"),
}


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m18-design", required=True, type=Path)
    ap.add_argument("--m18-manifest", required=True, type=Path)
    ap.add_argument("--m18-raw", required=True, type=Path)
    ap.add_argument("--m18-captures", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.m18_design) == BLOB_M18_DESIGN and file_blob(a.m18_manifest) == BLOB_M18_MANIFEST
       and file_blob(a.m18_raw) == BLOB_M18_RAW, "pins")
    man = [json.loads(x) for x in a.m18_manifest.read_text("utf8").splitlines() if x.strip()]
    raw = [json.loads(x) for x in a.m18_raw.read_text("utf8").splitlines() if x.strip()]
    ck(len(raw) == len(man) == 620, "620")

    def act(qs):
        q = next(q for q in qs if q["id"] == "certificate_action")
        return q["keys"][max(range(len(q["keys"])), key=lambda i: q["logits"][i])]
    X = {L: [] for L in LAYERS}
    for r in raw:
        f = torch.load(a.m18_captures / r["capture_file"]["name"], weights_only=True)
        ck(sha_file(a.m18_captures / r["capture_file"]["name"]) == r["capture_file"]["sha256"], "capture sha")
        for L in LAYERS:
            X[L].append(f["last"][NAMES.index(f"L{L}")].double())
    X = {L: torch.stack(v) for L, v in X.items()}
    is_new = [r["target_arm"] == "new" for r in raw]
    benign = [r["target_arm"] != "new" and act(r["questions"]) != "reject_conflict" for r in raw]
    grp = [r["source_group"] for r in raw]
    groups = sorted(set(grp))
    ck(len(groups) == 17, "17 groups")
    dirs, cent, energy = {}, {}, {}
    for L in LAYERS:
        for g in groups:
            nw = [i for i in range(len(raw)) if grp[i] != g and is_new[i]]
            bt = [i for i in range(len(raw)) if grp[i] != g and benign[i]]
            dvec = X[L][nw].mean(0) - X[L][bt].mean(0)
            u = dvec / dvec.norm()
            k = f"L{L}|{g}"
            dirs[k] = u.float()
            cent[k] = float((X[L][bt] @ u).mean())
            te = [i for i in range(len(raw)) if grp[i] == g]
            energy[k] = float(((X[L][te] @ u) - cent[k]).abs().median() / X[L][te].norm(dim=1).median())
    rows = []
    for m, r in zip(man, raw):
        base = {k: m[k] for k in ("target_scene", "target_arm", "source_group", "gold_action", "span", "token_ids_sha256",
                                  "state_len", "anchor_stage_a_fi")}
        g = m["source_group"]
        rows.append(dict(base, condition=f"replay_{m['target_arm']}", op=None, replay_of_m18=m["forward_index"]))
        for L in LAYERS:
            k = f"L{L}|{g}"
            for gm in GAMMAS:
                rows.append(dict(base, condition=f"gain_L{L}_g{int(gm)}", replay_of_m18=None,
                                 op={"layer": L, "kind": "gain", "gamma": gm, "dir": "meandiff", "key": k, "c": cent[k]}))
            for b in BETAS:
                rows.append(dict(base, condition=f"push_L{L}_b{int(b * 100):02d}", replay_of_m18=None,
                                 op={"layer": L, "kind": "push", "beta": b, "dir": "meandiff", "key": k}))
            seed = int(hashlib.sha256(f"A461_M21_RAND|L{L}|{m['target_scene']}|{m['target_arm']}".encode()).hexdigest()[:8], 16)
            v = torch.randn(X[L].shape[1], generator=torch.Generator().manual_seed(seed), dtype=torch.float64)
            rk = f"R|L{L}|{m['target_scene'][:12]}|{m['target_arm']}"
            dirs[rk] = (v / v.norm()).float()
            rows.append(dict(base, condition=f"rand_L{L}_b{int(RAND_BETA * 100):02d}", replay_of_m18=None,
                             op={"layer": L, "kind": "push", "beta": RAND_BETA, "dir": "random", "key": rk}))
    n = len(rows)
    plan = [PLAN_CAP] * (n // PLAN_CAP) + ([n % PLAN_CAP] if n % PLAN_CAP else [])
    for i, r in enumerate(rows):
        r.update(forward_index=i + 1, run=i // PLAN_CAP + 1)
    ck(n == 6820 and collections.Counter(r["condition"].split("_")[0] for r in rows)
       == {"replay": 620, "gain": 2480, "push": 2480, "rand": 1240}, "rows")
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    dp = out / "m21_directions.pt"
    with dp.open("xb") as fh:
        torch.save({k: v.contiguous() for k, v in sorted(dirs.items())}, fh)
    design = {"schema": "JEV_A461_MECH_M21_READOUT_MEANDIFF_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M21_FORWARD",
              "inputs": {"m18_design_blob": BLOB_M18_DESIGN, "m18_manifest_blob": BLOB_M18_MANIFEST,
                         "m18_raw_blob": BLOB_M18_RAW},
              "directions_file": {"name": dp.name, "sha256": sha_file(dp), "keys": len(dirs)},
              "layers": LAYERS, "gammas": GAMMAS, "betas": BETAS, "rand_beta": RAND_BETA, "groups": groups,
              "centres": cent, "held_out_relative_deviation_median": energy, "plan": plan, "total": n,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M21 forwards; {n} calls / {len(plan)} batches under the standing GPU authorization"}
    with (out / "m21_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m21_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for nm in ("m21_design.json", "m21_manifest.jsonl", "m21_directions.pt"):
            f.write(sha_file(out / nm) + "  " + nm + "\n")
    print(json.dumps({"rows": n, "batches": len(plan), "directions": len(dirs),
                      "rel_dev_median": {L: sorted(v for k, v in energy.items() if k.startswith(f"L{L}|"))[8] for L in LAYERS},
                      "manifest_blob": file_blob(out / "m21_manifest.jsonl"),
                      "design_blob": file_blob(out / "m21_design.json"), "directions_sha256": sha_file(dp)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
