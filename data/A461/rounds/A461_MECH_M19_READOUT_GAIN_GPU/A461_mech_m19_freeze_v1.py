#!/usr/bin/env python3
"""A461-MECH-M19 R1: CPU freeze of the readout-gain test (zero model forwards; torch CPU on the M18 features).

M18 (c56729c): in the 84 scenes where kev-4B accepts a lawful equivocation, the conflict is linearly decodable at
the decision position of the certificate_action row (held-out probe AUROC 0.999 after layer 19, 0.990 after layer 31),
yet the pointer head maps that state to accept. M19 asks whether the encoded feature is causally usable by the readout:
amplify each row's own deviation along the held-out probe direction u at the <decide> token of the certificate_action
row only, h' = h + (gamma - 1) (h.u - c) u, after layer L in {19, 31}, gamma in {2, 4, 8}; c = the training groups'
BENIGN mean of h.u. Input-dependent: rows near the benign mean barely move. Control: the same operation along a random
unit direction (seeded per row) with its own benign-mean centre, gamma 8. Directions are fit here, per held-out
source group, with the M18 probe spec on the other 16 groups (the same held-out discipline as M18), and written to a
pinned directions file. Plain replays of all 620 M18 rows (bitwise == M18) add the final-norm states at the decide
token and the option tokens of the certificate_action row for the readout geometry.
620 + 620 x 8 = 5580 calls.
"""
import argparse, collections, hashlib, json, subprocess, sys
from pathlib import Path

import torch

ROOT = (Path.home() / "wjc").resolve()
BLOB_M18_DESIGN = "1998024bffc0e8deee2cbf0d563eafbffad6bfef"
BLOB_M18_MANIFEST = "88f99a1827ad428515a9620408ae74c3545af0db"
BLOB_M18_RAW = "10e04cfadfaba7364abbb2eeb922b92c09ad9ea4"
LAYERS = [19, 31]
GAMMAS = [2.0, 4.0, 8.0]
RAND_GAMMA = 8.0
NAMES = ["emb", "L3", "L7", "L11", "L15", "L19", "L23", "L27", "L31"]
PLAN_CAP = 128

PREREG = {
    "operation": "at the <decide> token of the certificate_action row only (other rows and positions untouched), on "
                 "the residual output of decoder layer L: h' = h + (gamma - 1) * (h . u - c) * u, u a unit direction, "
                 "c = mean of h . u over the training groups' BENIGN rows (M18 definition); gamma = 1 is the identity",
    "directions": "PROBE u_{L,g}: the M18 probe (standardised L2 logistic, C = 1, LBFGS float64, 200 iterations) on the "
                  "LAST_RESID_L features of all rows outside source group g; u = (w / sd) normalised in raw space; "
                  "applied only to rows of group g (held out). RANDOM: a unit Gaussian direction seeded by "
                  "sha256(forward identity), with its own c from the same training BENIGN rows",
    "arms": "per M18 row: replay (no op; bitwise == M18 raw) + PROBE at L19 and L31 x gamma 2 / 4 / 8 + RANDOM at L19 and "
            "L31 x gamma 8",
    "sets": "MISSED = new rows whose M18 native action is not reject_conflict (84); RECOGNIZED = new rows that are "
            "rejected (40); BENIGN = old / SA / ROUND / OUTSIDER rows not rejected natively (483); NATIVE_FV = the 13 "
            "near-miss rows kev-4B already rejects (reported)",
    "measures": "REPAIR(arm) = share of MISSED rows whose action becomes reject_conflict; FV(arm) = share of BENIGN "
                "rows whose action becomes reject_conflict, overall and per arm (old, SA, ROUND, OUTSIDER); group-level: "
                "number of groups with >= 1 false veto and its Clopper-Pearson one-sided 95% bound; percentile "
                "group-bootstrap CIs (10000)",
    "verdict_readout": "per layer L: READOUT_GAIN_REPAIRS iff for some gamma in {2, 4, 8} PROBE has REPAIR >= 0.5 and FV "
                       "<= 0.05 on every benign arm, and RANDOM at gamma 8 has REPAIR <= 0.10; READOUT_GAIN_NONSELECTIVE "
                       "iff some PROBE gamma has REPAIR >= 0.5 but every such gamma has FV > 0.05 on some arm; "
                       "READOUT_GAIN_INERT iff PROBE REPAIR < 0.5 at every gamma; RANDOM_ALSO_REPAIRS iff RANDOM gamma 8 "
                       "REPAIR > 0.10 (reported with the verdict)",
    "consistency_gate": "all 620 replay rows bitwise == the M18 raw rows; every op row records |delta h| at the decide "
                        "token only (other rows' logits equal the replay's bitwise); gamma and direction as planned; "
                        "otherwise INCONSISTENT",
    "interpretation_fixed_in_advance": (
        "READOUT_GAIN_REPAIRS at L31 (the head's input layer): the conflict feature already present in the missed "
        "scenes is causally usable by the pointer head; the miss is an under-weighted readout of a present feature "
        "(H-READ, causal at the readout), not a missing representation. At L19 only: usable through the remaining "
        "layers. NONSELECTIVE: amplifying the direction pushes benign rows to reject too, so it is not a clean "
        "conflict feature for the head. INERT: decodable but not usable along this direction (decodability without "
        "use). Level S1-S2 (an artificial intervention on the native action); not a defence: the operation needs the "
        "held-out probe, i.e. rule-labelled data"),
    "always_reported": "REPAIR, FV per arm, RECOGNIZED retention, NATIVE_FV rows, median dA, per group; the readout "
                       "geometry from the replays: cosine between u_L31 (through the final norm, linearised at each "
                       "row) and the head's reject - accept query-side direction, per row, MISSED vs BENIGN",
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


def fit_probe(X, y):   # the M18 probe spec (A461_mon_m18_analysis_v1.py, blob da541fdb)
    mu, sd = X.mean(0), X.std(0).clamp_min(1e-6)
    Z = (X - mu) / sd
    w = torch.zeros(Z.shape[1], dtype=torch.float64, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([w, b], max_iter=200, line_search_fn="strong_wolfe")
    yy = y.double()

    def closure():
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(Z @ w + b, yy, reduction="sum") + 0.5 * (w @ w)
        loss.backward()
        return loss
    opt.step(closure)
    return w.detach() / sd


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
    torch.set_num_threads(16)
    man = [json.loads(x) for x in a.m18_manifest.read_text("utf8").splitlines() if x.strip()]
    raw = [json.loads(x) for x in a.m18_raw.read_text("utf8").splitlines() if x.strip()]
    ck(len(raw) == len(man) == 620 and all(r["forward_index"] == m["forward_index"] for r, m in zip(raw, man)), "620")

    def act(qs):
        q = next(q for q in qs if q["id"] == "certificate_action")
        return q["keys"][max(range(len(q["keys"])), key=lambda i: q["logits"][i])]
    feats = {L: [] for L in LAYERS}
    for r in raw:
        f = torch.load(a.m18_captures / r["capture_file"]["name"], weights_only=True)
        ck(sha_file(a.m18_captures / r["capture_file"]["name"]) == r["capture_file"]["sha256"] and f["names"] == NAMES,
           f"capture {r['forward_index']}")
        for L in LAYERS:
            feats[L].append(f["last"][NAMES.index(f"L{L}")].double())
    X = {L: torch.stack(v) for L, v in feats.items()}
    y = torch.tensor([r["gold_action"] == "reject_conflict" for r in raw])
    actn = [act(r["questions"]) for r in raw]
    benign = [r["target_arm"] != "new" and actn[i] != "reject_conflict" for i, r in enumerate(raw)]
    grp = [r["source_group"] for r in raw]
    groups = sorted(set(grp))
    ck(len(groups) == 17, "17 groups")
    dirs, cent = {}, {}
    for L in LAYERS:
        for g in groups:
            tr = [i for i in range(len(raw)) if grp[i] != g]
            w = fit_probe(X[L][tr], y[tr])
            u = w / w.norm()
            bt = [i for i in tr if benign[i]]
            dirs[f"L{L}|{g}"] = u.float()
            cent[f"L{L}|{g}"] = float((X[L][bt] @ u).mean())
    rows = []
    for m, r in zip(man, raw):
        base = {k: m[k] for k in ("target_scene", "target_arm", "source_group", "gold_action", "span", "token_ids_sha256",
                                  "state_len", "anchor_stage_a_fi")}
        rows.append(dict(base, condition=f"replay_{m['target_arm']}", op=None, replay_of_m18=m["forward_index"]))
        for L in LAYERS:
            g = m["source_group"]
            for gm in GAMMAS:
                rows.append(dict(base, condition=f"probe_L{L}_g{int(gm)}", replay_of_m18=None,
                                 op={"layer": L, "gamma": gm, "dir": "probe", "key": f"L{L}|{g}", "c": cent[f"L{L}|{g}"]}))
        for L in LAYERS:
            g = m["source_group"]
            seed = int(hashlib.sha256(f"A461_M19_RAND|L{L}|{m['target_scene']}|{m['target_arm']}".encode()).hexdigest()[:8], 16)
            gen = torch.Generator().manual_seed(seed)
            v = torch.randn(X[L].shape[1], generator=gen, dtype=torch.float64)
            v = v / v.norm()
            tr = [i for i in range(len(raw)) if grp[i] != g and benign[i]]
            key = f"R|L{L}|{m['target_scene'][:12]}|{m['target_arm']}"
            dirs[key] = v.float()
            rows.append(dict(base, condition=f"random_L{L}_g{int(RAND_GAMMA)}", replay_of_m18=None,
                             op={"layer": L, "gamma": RAND_GAMMA, "dir": "random", "key": key,
                                 "c": float((X[L][tr] @ v).mean())}))
    n = len(rows)
    plan = [PLAN_CAP] * (n // PLAN_CAP) + ([n % PLAN_CAP] if n % PLAN_CAP else [])
    for i, r in enumerate(rows):
        r.update(forward_index=i + 1, run=i // PLAN_CAP + 1)
    ck(n == 5580 and collections.Counter(r["condition"].split("_")[0] for r in rows) == {"replay": 620, "probe": 3720,
                                                                                       "random": 1240}, "rows")
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    dp = out / "m19_directions.pt"
    with dp.open("xb") as fh:
        torch.save({k: v.contiguous() for k, v in sorted(dirs.items())}, fh)
    design = {"schema": "JEV_A461_MECH_M19_READOUT_GAIN_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M19_FORWARD",
              "inputs": {"m18_design_blob": BLOB_M18_DESIGN, "m18_manifest_blob": BLOB_M18_MANIFEST,
                         "m18_raw_blob": BLOB_M18_RAW},
              "directions_file": {"name": dp.name, "sha256": sha_file(dp), "keys": len(dirs)},
              "layers": LAYERS, "gammas": GAMMAS, "random_gamma": RAND_GAMMA, "groups": groups,
              "centres": cent, "plan": plan, "total": n, "preregistered_analysis": PREREG,
              "gpu_status": f"0 M19 forwards; {n} calls / {len(plan)} batches under the standing GPU authorization"}
    with (out / "m19_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m19_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for nm in ("m19_design.json", "m19_manifest.jsonl", "m19_directions.pt"):
            f.write(sha_file(out / nm) + "  " + nm + "\n")
    print(json.dumps({"rows": n, "plan": plan, "directions": len(dirs),
                      "manifest_blob": file_blob(out / "m19_manifest.jsonl"),
                      "design_blob": file_blob(out / "m19_design.json"), "directions_sha256": sha_file(dp)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
