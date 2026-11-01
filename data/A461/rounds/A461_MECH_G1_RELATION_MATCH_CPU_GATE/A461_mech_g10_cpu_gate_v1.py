#!/usr/bin/env python3
"""A461-MECH-G1.0 CPU gate V1 (zero model loads, zero forwards; tokenizer-only).

Preregistration: PREREG_G10_V1.md (same directory). Three parts:
  I   identity: recover all 172 Stage-A roster states from the raw corpus,
      recompute both oracles and re-encode old/new/SA token ids
  II  single-field witness counterfactuals (OK_ALT, ROUND, NONSUP, LATE,
      OUTSIDER) for the 22 K-C scenes under the frozen-width token gate
  III host-coordinate role audit of the 104 K-C cross-group cells
"""
import argparse, collections, gzip, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
KEV_SRC = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_KC_DESIGN = "cd4cd9e5632cfa1b8aa476b94a332e3705af2f0f"
BLOB_KC_RAW = "19d3a06c27953b1f2b4dcd2770394d28741a69fd"
BLOB_G5V2_PAIRS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
ADMIT_DONOR_GROUPS, ADMIT_HOSTS = 10, 6
BLOCKING_CELLS = ("OK_ALT", "ROUND", "NONSUP")


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def git_blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def load_blob(d, sha):
    b = (d / sha).read_bytes()
    ck(git_blob_sha(b) == sha, f"blob digest {sha}")
    return b.decode("utf8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blobs", required=True, type=Path, help="dir holding frozen git blobs named by sha")
    ap.add_argument("--helper", required=True, type=Path, help="A461_g5_g2_stage_a_cpu_freeze_v1.py")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve(strict=False)
    ck(str(out).startswith(str(ROOT)) and out.parent.is_dir() and not out.exists(), "out dir")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1")
    sys.path.insert(0, str(a.helper.parent))
    import importlib.util
    spec = importlib.util.spec_from_file_location("stage_a", a.helper)
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    canon, hids, oracle1, oracle2 = sa.canon, sa.hids, sa.oracle1, sa.oracle2
    ck(sa.sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    receipt = {"schema": "JEV_A461_MECH_G10_CPU_GATE_RECEIPT_V1", "status": "INCOMPLETE",
               "gpu_forwards": 0, "model_loads": 0, "tokenizer_loads": 0,
               "script_sha256": sa.sha_file(Path(__file__).resolve()),
               "helper_sha256": sa.sha_file(a.helper),
               "frozen_inputs": {"corpus_sha256": CORPUS_SHA, "roster": BLOB_ROSTER, "kc_design": BLOB_KC_DESIGN,
                                 "kc_raw": BLOB_KC_RAW, "g5v2_pairs": BLOB_G5V2_PAIRS}}
    out.mkdir(mode=0o700)

    roster = json.loads(load_blob(a.blobs, BLOB_ROSTER))["candidates"]
    design = json.loads(load_blob(a.blobs, BLOB_KC_DESIGN))
    raw = [json.loads(x) for x in load_blob(a.blobs, BLOB_KC_RAW).splitlines() if x.strip()]
    q_tw = json.loads(load_blob(a.blobs, BLOB_G5V2_PAIRS).splitlines()[0])["native_request"]["questions"]
    ck(len(roster) == 172 and len(raw) == 417, "census")
    R = {c["scene_sha256"]: c for c in roster}

    sys.path.insert(0, str(KEV_SRC))
    from transformers import AutoTokenizer
    from kev.api import SystemOneRequest, to_record
    from kev.model import encode
    tok = AutoTokenizer.from_pretrained(str(BASE))
    receipt["tokenizer_loads"] = 1

    def enc_state(state):
        rendered, _ = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
        e = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
        ck(not e["state_truncated"], "truncated")
        return e

    def branch_segs(e):
        seg, cur, segs = e["seg"], e["seg"].count(0), []
        while cur < len(seg):
            end = cur
            while end < len(seg) and seg[end] == seg[cur]:
                end += 1
            segs.append(hids(e["ids"][cur:end]))
            cur = end
        return segs

    def with_msg(st, m):
        s = json.loads(canon(st))
        s["received_messages"].append(dict(m))
        return s

    def gold(st):
        g1, sup = oracle1(st)
        g2 = oracle2(st)
        return (g1 if g1 == g2 else None), sup

    # corpus census + scene recovery
    scenes, census = {}, collections.Counter()
    for line in gzip.open(CORPUS, "rt", encoding="utf8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec["_meta"].get("source") != "twins_streamlet":
            continue
        st = rec["state"]
        scenes[hashlib.sha256(canon(st).encode("utf8")).hexdigest()] = st
        census["states"] += 1
        for m in st["received_messages"]:
            if m.get("kind") != "vote":
                continue
            census["votes"] += 1
            if isinstance(m.get("received"), (int, float)) and m["received"] > st["decision_time"]:
                census["votes_after_deadline"] += 1
            if m.get("author") not in st["validator_set"]:
                census["votes_non_validator_author"] += 1
            if m.get("round") != st["candidate_round"]:
                census["votes_non_candidate_round"] += 1
    receipt["corpus_census"] = dict(census)

    # Part I
    ident, enc_cache = [], {}
    for c in roster:
        sh = c["scene_sha256"]
        row = {"scene_sha256": sh, "found": sh in scenes}
        if row["found"]:
            st = scenes[sh]
            arms = {"old": st, "new": with_msg(st, c["declared_edit_new"]["message"]),
                    "SA": with_msg(st, c["declared_edit_sa"]["message"])}
            row["oracle_ok"] = all(gold(arms[k])[0] == c["oracle_" + k.lower()] for k in arms)
            encs = {k: enc_state(v) for k, v in arms.items()}
            row["token_sha_ok"] = all(hids(encs[k]["ids"]) == c["token_ids_sha256"][k] for k in arms)
            enc_cache[sh] = encs
        ident.append(row)
    kc_donors = [d for d, _ in design["selection"]["replication_donors"]]
    kc_hosts = sorted({x["host"] for x in raw if x["host"]})
    ck(len(kc_hosts) == 8, "8 hosts")
    group = {c["scene_sha256"]: c["source_group"] for c in roster}
    kc_scenes = kc_donors + kc_hosts
    id_fail = [r for r in ident if not (r["found"] and r.get("oracle_ok") and r.get("token_sha_ok"))]
    kc_id_fail = [r for r in id_fail if r["scene_sha256"] in kc_scenes]
    receipt["part_I"] = {"scenes": len(ident), "pass": len(ident) - len(id_fail),
                         "fail": [r["scene_sha256"][:12] for r in id_fail],
                         "kc_scenes": len(kc_scenes), "kc_fail": len(kc_id_fail)}

    # Part II
    def variant(st, c, field, values, want):
        base = c["declared_edit_new"]["message"]
        o = enc_cache[c["scene_sha256"]]["old"]
        o_ids = o["ids"][:o["seg"].count(0)]
        bsegs = branch_segs(o)
        W = c["frozen_width"]
        tried = 0
        for v in values:
            m = dict(base)
            m[field] = v
            if m == base:
                continue
            s = with_msg(st, m)
            g, _ = gold(s)
            if g is None or g != want:
                continue
            tried += 1
            e = enc_state(s)
            ids = e["ids"][:e["seg"].count(0)]
            z = 0
            while z < min(len(o_ids), len(ids)) and o_ids[z] == ids[z]:
                z += 1
            span = [z, len(ids) - (len(o_ids) - z)]
            if len(ids) - len(o_ids) != W or ids[span[1]:] != o_ids[z:] or branch_segs(e) != bsegs:
                continue
            return {"ok": True, "field": field, "value": v, "message": m, "gold": g, "span": span,
                    "token_ids_sha256": hids(e["ids"]), "gold_ok_values_tried": tried}
        return {"ok": False, "field": field, "gold_ok_values_tried": tried}

    def near(vals, ref):
        return sorted(vals, key=lambda v: (abs(v - ref) if isinstance(v, (int, float)) and isinstance(ref, (int, float))
                                           else 0, str(v)))

    cf = {}
    for sh in kc_scenes:
        c, st = R[sh], scenes[sh]
        base = c["declared_edit_new"]["message"]
        _, sup = gold(st)
        g_new, g_old = c["oracle_new"], c["oracle_old"]
        vs = st["validator_set"]
        rounds_seen = {m.get("round") for m in st["received_messages"] if isinstance(m.get("round"), int)}
        rnd = st["candidate_round"]
        round_vals = near(sorted(r for r in rounds_seen | {rnd - 1, rnd + 1, rnd + 2} if r != rnd and r >= 0), rnd)
        dt = st["decision_time"]
        late_vals = [round(dt + d, 2) for d in (1.0, 2.0, 0.5, 0.1, 0.01, 3.0, 5.0, 10.0)]
        lab = sorted(vs)[0]
        prefix = "".join(ch for ch in lab if not ch.isdigit())
        outsiders = [f"{prefix}{k}" for k in range(len(vs), len(vs) + 12) if f"{prefix}{k}" not in vs]
        cf[sh] = {
            "group": group[sh], "role": "donor" if sh in kc_donors else "host", "frozen_message": base,
            "OK_ALT": variant(st, c, "author", sorted(set(sup) - {base["author"]}), g_new),
            "ROUND": variant(st, c, "round", round_vals, g_old),
            "NONSUP": variant(st, c, "author", sorted(set(vs) - set(sup)), g_old),
            "LATE": variant(st, c, "received", late_vals, g_old),
            "OUTSIDER": variant(st, c, "author", outsiders, g_old)}
    cover = {}
    for cell in ("OK_ALT", "ROUND", "NONSUP", "LATE", "OUTSIDER"):
        dg = {cf[d]["group"] for d in kc_donors if cf[d][cell]["ok"]}
        hs = [h for h in kc_hosts if cf[h][cell]["ok"]]
        cover[cell] = {"donor_groups": len(dg), "donor_groups_of": 14, "hosts": len(hs), "hosts_of": 8,
                       "missing_donors": [d[:12] for d in kc_donors if not cf[d][cell]["ok"]],
                       "missing_hosts": [h[:12] for h in kc_hosts if not cf[h][cell]["ok"]]}
    receipt["part_II_coverage"] = cover

    # Part III
    def ra(qs):
        q = {x["id"]: x for x in qs}
        cl, al = q["conflicting_vote"], q["certificate_action"]
        M = cl["logits"][cl["keys"].index("true")] - cl["logits"][cl["keys"].index("false")]
        L = dict(zip(al["keys"], al["logits"]))
        A = L["reject_conflict"] - max(L["accept"], L["wait"])
        return M, A, (M > 0 and A > 0)

    by = collections.defaultdict(dict)
    for x in raw:
        if x["donor"] and x["cross_group"] and x["source_kind"] in ("main", "sasham", "doserand"):
            by[(x["donor"], x["host"])][x["source_kind"]] = ra(x["questions"])
    cells = []
    for (d, h), arms in sorted(by.items()):
        ck(set(arms) == {"main", "sasham", "doserand"}, "arm triple")
        md, sth = R[d]["declared_edit_new"]["message"], scenes[h]
        hm = R[h]["declared_edit_new"]["message"]
        gs, _ = gold(with_msg(sth, md))
        _, hsup = gold(sth)
        dn, hn = enc_cache[d]["new"], enc_cache[h]["new"]
        dsp, hsp = R[d]["appended_span_in_state"]["new"], R[h]["appended_span_in_state"]["new"]
        dt_ids, ht_ids = dn["ids"][dsp[0]:dsp[1]], hn["ids"][hsp[0]:hsp[1]]
        cells.append({
            "donor": d[:12], "host": h[:12], "donor_group": group[d], "host_group": group[h],
            "specific_joint": arms["main"][2] and not arms["sasham"][2] and not arms["doserand"][2],
            "dM_main_minus_dose": arms["main"][0] - arms["doserand"][0],
            "gold_sub_conflict": bool(gs and gs["conflicting_vote"]),
            "author_in_host_validators": md["author"] in sth["validator_set"],
            "author_is_host_supporter": md["author"] in hsup,
            "round_eq_host_candidate": md["round"] == sth["candidate_round"],
            "block_neq_host_candidate": md["block"] != sth["candidate_block"],
            "received_within_host_deadline": md["received"] <= sth["decision_time"],
            "same_author_label_as_host_msg": md["author"] == hm["author"],
            "same_block_label_as_host_msg": md["block"] == hm["block"],
            "span_len_equal": len(dt_ids) == len(ht_ids),
            "span_positions_differing": sum(1 for p, q in zip(dt_ids, ht_ids) if p != q)})
    ck(len(cells) == 104, "104 cross cells")

    def strat(key):
        res = {}
        for val in (True, False):
            sub = [c for c in cells if c[key] == val]
            sj = [c for c in sub if c["specific_joint"]]
            dms = sorted(c["dM_main_minus_dose"] for c in sub)
            res[str(val)] = {"cells": len(sub), "specific_joint": len(sj),
                             "donor_groups": len({c["donor_group"] for c in sub}),
                             "hosts": len({c["host"] for c in sub}),
                             "sj_donor_groups": len({c["donor_group"] for c in sj}),
                             "median_dM_main_minus_dose": dms[len(dms) // 2] if dms else None}
        return res
    keys = ["gold_sub_conflict", "author_in_host_validators", "author_is_host_supporter", "round_eq_host_candidate",
            "block_neq_host_candidate", "received_within_host_deadline", "same_author_label_as_host_msg",
            "same_block_label_as_host_msg"]
    receipt["part_III"] = {"cells": 104, "specific_joint": sum(c["specific_joint"] for c in cells),
                           "strata": {k: strat(k) for k in keys},
                           "span_len_equal": sum(c["span_len_equal"] for c in cells),
                           "span_positions_differing_hist": dict(collections.Counter(c["span_positions_differing"] for c in cells))}

    admit = (not kc_id_fail and all(cover[k]["donor_groups"] >= ADMIT_DONOR_GROUPS and cover[k]["hosts"] >= ADMIT_HOSTS
                                    for k in BLOCKING_CELLS))
    receipt["verdict"] = "G10_ADMITTED_FOR_M1_DESIGN" if admit else "G10_NOT_ADMITTED"
    receipt["status"] = "COMPLETE"
    for name, obj in (("identity.json", ident), ("counterfactuals.json", cf), ("kc_role_cells.json", cells),
                      ("receipt.json", receipt)):
        sa.save(out / name, obj)
    print(json.dumps(receipt, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
