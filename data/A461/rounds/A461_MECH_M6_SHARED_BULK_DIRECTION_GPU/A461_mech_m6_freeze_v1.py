#!/usr/bin/env python3
"""A461-MECH-M6 R1: CPU freeze of the shared-component tests of the L11 BULK write of kev-4B
(zero model forwards; tokenizer only, for the key classes).

M5 (695f4fe): the donor-minus-host BULK direction (BULK = OTHER_ITEMS + CONTEXT key-class contributions of the
L11 span write) rescaled to the full patch's size repairs 48/104 round-specifically while a random direction of
that size repairs 1 (BULK_DIRECTION), and the donor's BULK part can be replaced by a third donor's (51/51,
XD_HOLDS). M6 asks whether that component is SHARED across donors and LOW-RANK. All arms target host new; the
pools never contain the cell's donor nor the donor of the host's own group.
  P  pooled means: meanD_host  = host  - host_B  + mean_{p in Pool_D} p_B(src)
                   meanD_donor = donor - donor_B + mean_{p in Pool_D} p_B(src)
                   meanH_host  = host  - host_B  + mean_{h' in Pool_H} h'_B(src)   (null: other hosts' BULK)
     Pool_D = the 12 donors from neither the donor's nor the host's group; Pool_H = the other hosts outside the
     donor's group; src = the source's arm (new / ROUND)
  L  low rank: lr_k = host + U_k U_k^T (donor_B - host_B), U_k = top-k right singular vectors of the uncentred
     row-0 BULK contributions of Pool_D (both arms, all 31 span positions), k in 1, 4, 16, 64
  N  matched random subspace: rand_k = host + Q_k Q_k^T delta_B rescaled per row and span position to
     ||U_k U_k^T delta_B|| (Q_k a seeded orthonormal random k-frame, fixed per cell), k in 4, 16, 64
`full` = the M3 all-heads patch (bitwise anchor, 51); `xdonor_BULK` = the M5 third-donor arm (bitwise anchor of
the M5 rows, 51). 44 captures + 104 x 12 x 2 = 2540 calls in 19 x 128 + 108.
"""
import argparse, collections, gzip, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
WORK = ROOT / "a461-g5-minimal-patch-pilot-20261025-v1"
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_M1_DESIGN = "f3852efc21e7b55fdc1b7370a867454730422913"
BLOB_M1_RAW = "298c7cdfab634cd6a6a9122fac90d41c87219c21"
BLOB_G10_CF = "06ee06d7942b9f1a5f09c35777d5da1149655e4d"
BLOB_M3_DESIGN = "7445c13bc36c45324b54c3b4ea2fcbee0c37fe77"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M4_DESIGN = "7ec989c0f70d3fcead4b64b035a32b6655110575"
BLOB_M5_DESIGN = "26126568cce05db149d815b2faf3090e5e84c27b"
BLOB_M5_RAW = "f03ce4e96e6eb4ea76b43d9627bad62c87ca8c4d"
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
N_HEADS, N_KV = 16, 4
SOURCES = ("new", "ROUND")
BASE = ("PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT")
BULK = ["OTHER_ITEMS", "CONTEXT"]
KS = [1, 4, 16, 64]
RAND_KS = [4, 16, 64]
# (name, op, classes, extra): pool base = whose remainder is kept; pool = which captures are averaged
ARMS = ([("full", "full", [], {}), ("xdonor_BULK", "xdonor", BULK, {}),
         ("meanD_host", "pool", BULK, {"base": "target", "pool": "donors"}),
         ("meanD_donor", "pool", BULK, {"base": "source", "pool": "donors"}),
         ("meanH_host", "pool", BULK, {"base": "target", "pool": "hosts"})]
        + [(f"lr{k}", "lowrank", BULK, {"k": k}) for k in KS]
        + [(f"rand{k}", "randsub", BULK, {"k": k}) for k in RAND_KS])
PLAN = [128] * 19 + [108]

PREREG = {
    "readouts": "M = conflict margin; A = logit(reject_conflict) - max(accept, wait); JOINT = M > 0 and A > 0; "
                "dM = M(patch) - M(in-run capture of host new)",
    "units": "the 104 cross-group cells of M1-M5; cells share donors and hosts, and the pooled-mean arms vary with "
             "the donor only through the pool exclusion (effectively 8 hosts), so counts are descriptive decision "
             "rules, not independent tests; per-host S is always reported",
    "S": "S(arm) = #cells where the donor-new-source patch is JOINT and the donor-ROUND-source patch of the same arm "
         "is not (target host new)",
    "SPEC": "SPEC iff dM_main > dM_round in >= 75% of cells AND in a majority of cells for >= 10 of 14 donor groups",
    "SUF": "SUF(arm) iff S(arm) >= 1/2 S(full) and SPEC(arm)",
    "consistency_gate": "full = the M3 all-heads patch: its 208 rows equal M3's bitwise and S(full) = 51; "
                        "xdonor_BULK = the M5 third-donor arm: its 208 rows equal M5's bitwise and S = 51 (GPU, "
                        "checked in the run); otherwise verdict INCONSISTENT_WITH_M3_M5 and no claim",
    "size_gate": "for every rand_k row, ||patch - host|| per row and span position equals ||U_k U_k^T delta_B|| "
                 "within 1e-3 relative (fail-closed in the runner); the energy fraction ||U_k U_k^T delta_B|| / "
                 "||delta_B|| is recorded in every lr_k and rand_k row",
    "shared_verdict": "SHARED_DONOR_COMPONENT if SUF(meanD_host) and not SUF(meanH_host); GENERIC_CONTEXT_SHIFT if "
                      "SUF(meanD_host) and SUF(meanH_host); SHARED_NEEDS_DONOR_REST if not SUF(meanD_host) and "
                      "SUF(meanD_donor); NOT_SHARED_BY_AVERAGE otherwise",
    "lowrank_verdict": "k* = the smallest k in 1, 4, 16, 64 with SUF(lr_k); null arm = rand_max(k*, 4); NULL holds "
                       "iff S(null) <= 5 and not SPEC(null). LOWRANK:k* if k* exists and NULL holds; "
                       "LOWRANK_UNRESOLVED:k* if k* exists and NULL fails; NOT_LOWRANK_LE64 if no k*",
    "interpretation_fixed_in_advance": "SHARED_DONOR_COMPONENT: one averaged donor BULK contribution, from donors "
        "other than the cell's own, gives hosts the round-specific repair while the averaged BULK of other hosts "
        "does not: a donor-like shared component, not scene content. GENERIC_CONTEXT_SHIFT: any averaged context "
        "read works, so the M5 'donor-like' reading is not supported. SHARED_NEEDS_DONOR_REST: the averaged "
        "component works only together with the rest of the donor's write. NOT_SHARED_BY_AVERAGE: averaging "
        "destroys what a single third donor carries (M5 XD_HOLDS), e.g. donors agree in subspace but not in sign "
        "or position pattern. LOWRANK:k: the repairing part of delta_B lies in a k-dimensional subspace learned "
        "from other donors, and a random k-subspace of the same size does not repair. The pooled means change "
        "the host by their own size (not matched); their change norms relative to the full patch are reported. "
        "The subspace is fit on both arms (new and ROUND) of the pool donors, so round-specificity of lr_k comes "
        "from the cell's own delta_B, not from the basis",
    "always_reported": "S, SPEC, J_main, J_round and median dM per arm; per host; leave-one-donor-group-out of "
                       "both verdicts; energy fraction of lr_k / rand_k; change norm of every arm relative to the "
                       "full patch; all nulls",
}

def ck(v, m):
    if not v:
        raise RuntimeError(m)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def ranges(idx):
    """sorted index list -> [[lo, hi), ...]"""
    out = []
    for i in idx:
        if out and out[-1][1] == i:
            out[-1][1] = i + 1
        else:
            out.append([i, i + 1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--roster", required=True, type=Path)
    ap.add_argument("--m1-design", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--m3-design", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m4-design", required=True, type=Path)
    ap.add_argument("--m5-design", required=True, type=Path)
    ap.add_argument("--m5-raw", required=True, type=Path)
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.m1_design) == BLOB_M1_DESIGN
       and file_blob(a.m1_raw) == BLOB_M1_RAW and file_blob(a.m3_design) == BLOB_M3_DESIGN
       and file_blob(a.m3_raw) == BLOB_M3_RAW and file_blob(a.m4_design) == BLOB_M4_DESIGN and file_blob(a.g10_counterfactuals) == BLOB_G10_CF
       and file_blob(a.m5_design) == BLOB_M5_DESIGN and file_blob(a.m5_raw) == BLOB_M5_RAW, "pins")
    spec = importlib.util.spec_from_file_location("sa", WORK / "A461_g5_g2_stage_a_cpu_freeze_v1.py")
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    ck(sha_file(sa.CORPUS) == sa.CORPUS_SHA, "corpus pin")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    m1 = json.loads(a.m1_design.read_text("utf8"))
    m3 = json.loads(a.m3_design.read_text("utf8"))
    m4 = json.loads(a.m4_design.read_text("utf8"))
    m5 = json.loads(a.m5_design.read_text("utf8"))
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    m3raw = [json.loads(x) for x in a.m3_raw.read_text("utf8").splitlines() if x.strip()]
    m5raw = [json.loads(x) for x in a.m5_raw.read_text("utf8").splitlines() if x.strip()]
    donors, hosts = m1["selection"]["donors"], m1["selection"]["hosts"]
    ck(len(donors) == 14 and len(hosts) == 8 and m3["selection"] == {"donors": donors, "hosts": hosts}, "selection")
    gd, gh = dict(donors), dict(hosts)
    m1_cap = {(x["target_scene"], x["target_arm"]): x["forward_index"] for x in m1raw if x["capture"]}
    m3_all = {(x["donor"], x["host"], x["source_kind"]): x["forward_index"] for x in m3raw
              if x["patch"] and x["patch"]["arm"] == "all"}
    ck(len(m3_all) == 208, "208 M3 all-heads rows")
    m5_xd = {(x["donor"], x["host"], x["source_kind"]): x for x in m5raw
             if x["patch"] and x["patch"]["arm"] == "xdonor_BULK"}
    ck(len(m5_xd) == 208 and m5["selection"] == m3["selection"], "208 M5 xdonor rows")

    # ---------- key classes (tokenizer only) ----------
    repo = a.repo_root.expanduser().resolve(strict=True)
    g5_full = subprocess.run(["git", "-C", str(repo), "rev-parse", BLOB_G5V2], capture_output=True, text=True,
                             check=True).stdout.strip()
    q_tw = json.loads(subprocess.run(["git", "-C", str(repo), "cat-file", "blob", g5_full], capture_output=True,
                                     text=True, check=True).stdout.splitlines()[0])["native_request"]["questions"]
    sys.path.insert(0, str(ROOT / "kev08b-smoke-20261001-153041/code"))
    from transformers import AutoTokenizer
    from kev.api import SystemOneRequest, to_record
    from kev.model import encode
    tok = AutoTokenizer.from_pretrained(str(ROOT / "kev4b-assets-20261002/base"))
    need = set(gd) | set(gh)
    scenes = {}
    for line in gzip.open(sa.CORPUS, "rt", encoding="utf8"):
        if line.strip():
            rec = json.loads(line)
            if rec["_meta"].get("source") == "twins_streamlet":
                sh = hashlib.sha256(sa.canon(rec["state"]).encode("utf8")).hexdigest()
                if sh in need:
                    scenes[sh] = rec["state"]
    ck(set(scenes) == need, "scene recovery")

    def span(s, arm):
        return roster[s]["appended_span_in_state"]["new"] if arm == "new" else cf[s]["ROUND"]["span"]

    def classes(s, arm):
        msg = roster[s]["declared_edit_new"]["message"] if arm == "new" else cf[s]["ROUND"]["message"]
        st = json.loads(sa.canon(scenes[s]))
        st["received_messages"].append(dict(msg))
        rendered, _ = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(sa.canon(st))}))
        e = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
        ck(not e["state_truncated"], "truncated")
        tid = sa.hids(e["ids"])
        want = roster[s]["token_ids_sha256"]["new"] if arm == "new" else cf[s]["ROUND"]["token_ids_sha256"]
        ck(tid == want, f"token gate {s[:8]}:{arm}")
        ids = e["ids"][:e["seg"].count(0)]
        dec = [tok.decode([t]) for t in ids]
        starts = [p for p in range(len(ids) - 2) if dec[p] == " " and dec[p + 1] == " -" and dec[p + 2] == " author"]
        msgs = st["received_messages"]
        ck(len(starts) == len(msgs), f"item starts {len(starts)} != messages {len(msgs)} at {s[:8]}:{arm}")
        s0, s1 = span(s, arm)
        ck(starts[-1] == s0, f"last item != span at {s[:8]}:{arm}")
        items = list(zip(starts, starts[1:] + [s1]))
        for (p, q), m in zip(items, msgs):
            txt = "".join(dec[p:q])
            ck(all(f"{k}: {m[k]}" in txt for k in ("author", "block", "kind")), f"item text at {s[:8]}:{arm}:{p}")
        rnd, A = st["candidate_round"], msg["author"]
        allowed = set(st["validator_set"])
        base = roster[s]["declared_edit_new"]["message"]
        partner, peers, other, pmsg = [], [], [], None
        for (p, q), m in zip(items[:-1], msgs[:-1]):
            if (m.get("kind") == "vote" and m.get("round") == rnd and m.get("author") == A
                    and m.get("block") != base["block"] and m.get("author") in allowed
                    and isinstance(m.get("received"), (int, float)) and m["received"] <= st["decision_time"]):
                partner.append([p, q])
                pmsg = m
            elif m.get("kind") == "vote" and m.get("round") == rnd and m.get("author") != A:
                peers.append([p, q])
            else:
                other.append([p, q])
        ck(len(partner) == 1 and partner[0][1] - partner[0][0] == 33, f"partner at {s[:8]}:{arm}")
        ck(other, f"no OTHER_ITEMS at {s[:8]}:{arm}")
        used = {k for lo, hi in partner + peers + other + [[s0, s1]] for k in range(lo, hi)}
        cls = {"PARTNER": partner, "ROUND_PEERS": peers, "OTHER_ITEMS": other, "SELF": [[s0, s1]],
               "CONTEXT": ranges([k for k in range(s1) if k not in used])}
        cover = sorted(k for v in cls.values() for lo, hi in v for k in range(lo, hi))
        ck(cover == list(range(s1)), f"classes do not partition the keys < span end at {s[:8]}:{arm}")
        mk = m4["key_classes"][f"{arm}:{s[:12]}"]
        ck(mk["classes"] == cls and mk["token_ids_sha256"] == tid, f"M4 key classes differ at {s[:8]}:{arm}")
        mc = m3["token_classes"][f"{arm}:{s[:12]}"]
        ck(mc["partner"] == partner and mc["round_peers"] == peers and mc["span"] == [s0, s1]
           and mc["token_ids_sha256"] == tid, f"M3 token classes differ at {s[:8]}:{arm}")
        ck(m5["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M5 key classes differ at {s[:8]}:{arm}")
        return {"span": [s0, s1], "classes": cls, "state_len": len(ids), "token_ids_sha256": tid,
                "partner_token_ids": ids[partner[0][0]:partner[0][1]], "partner_message": pmsg, "author": A}

    key_classes = {}
    rows = []

    def add(**kw):
        n = len(rows)
        rows.append(dict(forward_index=n + 1, run=n // 128 + 1, **kw))

    for kind, sel in (("donor", donors), ("host", hosts)):
        for s, _g in sel:
            for arm in SOURCES:
                tag = f"{arm}:{s[:12]}"
                key_classes[tag] = classes(s, arm)
                add(phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm,
                    source_kind=kind,
                    capture={"tag": tag, "span": span(s, arm), "rows": "all", "save": True, "layer": HEAD_LAYER,
                             "classes": key_classes[tag]["classes"], "partner": key_classes[tag]["classes"]["PARTNER"][0]},
                    bitwise_vs_m1=m1_cap.get((s, arm)))
    ck(sum(1 for r in rows if r["bitwise_vs_m1"]) == 36, "36 M1 bitwise anchors")
    dlist = [d for d, _ in donors]
    third_of, pools = {}, {}
    hlist = [h for h, _ in hosts]
    for d, _ in donors:
        for h, _ in hosts:
            if gd[d] == gh[h]:
                continue
            k = dlist.index(d)
            third = next(t for t in dlist[k + 1:] + dlist[:k] if gd[t] not in (gd[d], gh[h]))
            ck(m5["third_donor"][f"{d[:12]}|{h[:12]}"] == third, "third donor != M5")
            third_of[f"{d[:12]}|{h[:12]}"] = third
            pool_d = [t for t in dlist if gd[t] not in (gd[d], gh[h])]
            pool_h = [t for t in hlist if t != h and gh[t] != gd[d]]
            ck(len(pool_d) == 12 and d not in pool_d and pool_h and h not in pool_h, "pools")
            pools[f"{d[:12]}|{h[:12]}"] = {"donors": [t[:12] for t in pool_d], "hosts": [t[:12] for t in pool_h]}
            for arm, op, cl, ex in ARMS:
                for src in SOURCES:
                    sk = "main" if src == "new" else "round"
                    patch = {"layer": HEAD_LAYER, "arm": arm, "op": op, "classes": cl, "span": span(h, "new"),
                             "source": f"{src}:{d[:12]}", "target": f"new:{h[:12]}", "rows": "all"}
                    if op == "xdonor":
                        patch["third"] = f"{src}:{third[:12]}"
                        mx = m5_xd[(d, h, sk)]["patch"]
                        ck(mx["third"] == patch["third"] and mx["source"] == patch["source"]
                           and mx["span"] == patch["span"], "M5 xdonor wiring")
                    if op == "pool":
                        patch["base"] = ex["base"]
                        patch["pool"] = [f"{src}:{t[:12]}" for t in (pool_d if ex["pool"] == "donors" else pool_h)]
                    if op in ("lowrank", "randsub"):
                        patch["k"] = ex["k"]
                        patch["basis_pool"] = [f"{a_}:{t[:12]}" for t in pool_d for a_ in SOURCES]
                    if op == "randsub":
                        patch["seed"] = int(hashlib.sha256(f"A461_M6_RANDSUB|{ex['k']}|{d}|{h}".encode()).hexdigest()[:8], 16)
                    add(phase="patch", condition=f"patch_m6_{arm}_{sk}", direction="repair", scope="all",
                        source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                        target_arm="new", patch=patch,
                        bitwise_vs_m3=m3_all[(d, h, sk)] if op == "full" else None,
                        bitwise_vs_m5=m5_xd[(d, h, sk)]["forward_index"] if op == "xdonor" else None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * len(ARMS) * 2 == 2496, "104 x 12 x 2 patches")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m3")) == 208, "208 M3 bitwise anchors")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m5")) == 208, "208 M5 bitwise anchors")
    design = {"schema": "JEV_A461_MECH_M6_SHARED_BULK_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M6_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader); L11 = Qwen3.5 full attention, "
                       "16 query heads x 256 in 4 KV groups, output gate, o_proj without bias",
              "inputs": {"roster_blob": BLOB_ROSTER, "m1_design_blob": BLOB_M1_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                         "m3_design_blob": BLOB_M3_DESIGN, "m3_raw_blob": BLOB_M3_RAW, "m4_design_blob": BLOB_M4_DESIGN,
                         "m5_design_blob": BLOB_M5_DESIGN, "m5_raw_blob": BLOB_M5_RAW,
                         "g10_counterfactuals_blob": BLOB_G10_CF, "g5v2_questions_blob": g5_full,
                         "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV, "base_classes": list(BASE),
              "arms": [[n, op, cl, ex] for n, op, cl, ex in ARMS], "ks": KS, "rand_ks": RAND_KS, "bulk": BULK,
              "third_donor": third_of, "pools": pools,
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "key_classes": key_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M6 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m6_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m6_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m6_design.json", "m6_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 2496,
                      "class_sizes": {t: {k: sum(hi - lo for lo, hi in v) for k, v in c["classes"].items()}
                                      for t, c in list(key_classes.items())[:3]},
                      "manifest_blob": file_blob(out / "m6_manifest.jsonl"),
                      "design_blob": file_blob(out / "m6_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
