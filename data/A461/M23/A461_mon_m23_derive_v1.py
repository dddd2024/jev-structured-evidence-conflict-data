#!/usr/bin/env python3
"""Derive the M23 runners and self-tests from the M18 (kev-4B) and M22 (SecJev-0.8B) ones. Deterministic text edits;
every replaced span must occur exactly once (after the stage-name rename).

  python A461_mon_m23_derive_v1.py <rounds dir> <manifest blob k> <design blob k> <manifest blob s> <design blob s> <outdir>

Changes vs the parents: stage name, run / ledger roots, pins, the 248-call plan [128, 120]; a new arm TWIN whose state
is the new arm's with the appended author's partner vote moved to a non-candidate round (design `partner_edit`, checked
field by field against the corpus state); TWIN rows have no Stage-A anchor (as ROUND / OUTSIDER in the parents). Hooks,
gate, ledger, model load and per-forward body are unchanged. Self-tests: 248 rows, arms {new, TWIN}, and the span test
now requires the emb-layer span mean of new == TWIN (byte-identical span) while the full token sequence differs."""
import io, sys
from pathlib import Path

rounds, mk, dk, ms, ds, outdir = sys.argv[1:7]
R, O = Path(rounds), Path(outdir)
PAR = {"k": ("A461_MON_M18_SPAN_MONITOR_GPU", "m18", "M18", mk, dk),
       "s": ("A461_MON_M22_SECJEV_REPLICATION_GPU", "m22", "M22", ms, ds)}

for k, (pdir, lo, up, mblob, dblob) in PAR.items():
    new_lo, new_up = f"m23{k}", f"M23{k.upper()}"
    # ---- runner ----
    s = io.open(R / pdir / f"A461_mon_{lo}_runner_v1.py", encoding="utf8").read()

    def rep(a, b, cnt=1):
        global s
        assert s.count(a) == cnt, (k, s.count(a), a[:90])
        s = s.replace(a, b)
    old_stage = [x for x in s.splitlines() if x.startswith("STAGE = ")][0]
    rep(old_stage, 'STAGE = "A461_MON_M23_TWIN_PROBE_GPU"')
    s = s.replace(lo, new_lo).replace(up, new_up)
    rep('#!/usr/bin/env python3\n"""', f'#!/usr/bin/env python3\n"""A461-MON-M23 ({new_up}) runner: derived from the {up} runner by A461_mon_m23_derive_v1.py - the same\nread-only captures on 124 new rows (bitwise Stage-A anchors) and 124 same-span TWIN rows (partner vote moved to a\nnon-candidate round; Gold not reject_conflict). Parent docstring follows.\n')
    mline = [x for x in s.splitlines() if x.startswith("BLOB_MANIFEST = ")][0]
    dline = [x for x in s.splitlines() if x.startswith("BLOB_DESIGN = ")][0]
    rep(mline, f'BLOB_MANIFEST = "{mblob}"')
    rep(dline, f'BLOB_DESIGN = "{dblob}"')
    rep("FROZEN_BATCHES = [128, 128, 128, 128, 108]", "FROZEN_BATCHES = [128, 120]")
    rep("FROZEN_TOTAL = 620", "FROZEN_TOTAL = 248")
    rep('"gpu approval must be exactly 620 calls / [128, 128, 128, 128, 108]"', '"gpu approval must be exactly 248 calls / [128, 120]"')
    rep('ARMS = ("old", "new", "SA", "ROUND", "OUTSIDER")', 'ARMS = ("new", "TWIN")')
    rep('''                msg = (roster[s]["declared_edit_new"]["message"] if arm == "new" else''',
        '''                msg = (roster[s]["declared_edit_new"]["message"] if arm in ("new", "TWIN") else''')
    rep('''                st["received_messages"].append(dict(msg))''',
        '''                if arm == "TWIN":   # M23: move the appended author's partner vote to a non-candidate round
                    pe = x["partner_edit"]
                    pm = st["received_messages"][pe["index"]]
                    ck(pm == pe["original"] and pm.get("kind") == "vote" and pm.get("author") == msg["author"]
                       and pm.get("round") == st["candidate_round"] == pe["from"]
                       and pm.get("block") == st["candidate_block"] and pe["field"] == "round"
                       and pe["to"] != st["candidate_round"]
                       and sum(1 for q in st["received_messages"] if q.get("kind") == "vote"
                               and q.get("author") == msg["author"] and q.get("round") == st["candidate_round"]
                               and q.get("block") == st["candidate_block"]) == 1, f"TWIN partner edit {s[:8]}")
                    pm["round"] = pe["to"]
                st["received_messages"].append(dict(msg))''')
    rep('''                ck(arm in ("ROUND", "OUTSIDER"), f"missing Stage-A anchor {m['forward_index']}")''',
        '''                ck(arm == "TWIN", f"missing Stage-A anchor {m['forward_index']}")''')
    io.open(O / f"A461_mon_{new_lo}_runner_v1.py", "w", encoding="utf8", newline="\n").write(s)

    # ---- self-test ----
    s = io.open(R / pdir / f"A461_mon_{lo}_selftest_v1.py", encoding="utf8").read()
    old_stage = [x for x in s.splitlines() if x.startswith("STAGE = ")][0]
    rep(old_stage, 'STAGE = "A461_MON_M23_TWIN_PROBE_GPU"')
    s = s.replace(lo, new_lo).replace(up, new_up)
    rep('#!/usr/bin/env python3\n"""', f'#!/usr/bin/env python3\n"""A461-MON-M23 ({new_up}) self-test, derived from the {up} one by A461_mon_m23_derive_v1.py: 248 rows, arms\n{{new, TWIN}}; the span test requires the emb-layer span mean of new == TWIN (byte-identical span) while the full\ntoken sequences differ. Parent docstring follows.\n')
    rep('and arms == {k: 124 for k in ("old", "new", "SA", "ROUND", "OUTSIDER")} and xr <= 1e-4,',
        'and arms == {k: 124 for k in ("new", "TWIN")} and xr <= 1e-4,')
    rep('guarded("fake_full_path_620_rows_and_feature_files", t_full)', 'guarded("fake_full_path_248_rows_and_feature_files", t_full)')
    rep('''        diff, olds = 0, 0
        for s in {x["target_scene"] for x in x2}:
            fn = torch.load(d2 / by[(s, "new")]["capture_file"]["name"], weights_only=True)
            fr = torch.load(d2 / by[(s, "ROUND")]["capture_file"]["name"], weights_only=True)
            diff += bool((fn["span_mean"][0] != fr["span_mean"][0]).any())
            olds += by[(s, "old")]["span"][1] - by[(s, "old")]["span"][0] == 33
        return (diff == 124 and olds == 124,
                f"emb-layer span mean of new != ROUND in {diff}/124 scenes (round token inside the span); old arm "
                f"spans are the 33-token last item in {olds}/124")''',
        '''        same, tokdiff = 0, 0
        for s in {x["target_scene"] for x in x2}:
            fn = torch.load(d2 / by[(s, "new")]["capture_file"]["name"], weights_only=True)
            ft = torch.load(d2 / by[(s, "TWIN")]["capture_file"]["name"], weights_only=True)
            same += bool(torch.equal(fn["span_mean"][0], ft["span_mean"][0]))
            tokdiff += by[(s, "new")]["token_ids_sha256"] != by[(s, "TWIN")]["token_ids_sha256"]
        return (same == 124 and tokdiff == 124,
                f"emb-layer span mean of new == TWIN in {same}/124 scenes (byte-identical span); full token "
                f"sequences differ in {tokdiff}/124")''')
    io.open(O / f"A461_mon_{new_lo}_selftest_v1.py", "w", encoding="utf8", newline="\n").write(s)
print("ok")
