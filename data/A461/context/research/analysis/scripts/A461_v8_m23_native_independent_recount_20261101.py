#!/usr/bin/env python3
from collections import Counter, defaultdict
from pathlib import Path
import json, hashlib, math
WORK=Path.home()/'wjc'/'a461-g5-minimal-patch-pilot-20261025-v1'
OUT=Path.home()/'wjc'/'a461_closeout_20261101'
PKG=OUT/'repo_snapshot/research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/PAPER_CLAIM_PACKAGE_V8'
expected=json.loads((PKG/'numbers_mech_v5.json').read_text(encoding='utf-8'))['M23']['models']
result={'github_commit':'937fdd4c5e22f231f3d4acf05eb41b80c784c7cb','type':'independent CPU raw-logit recount; not model replication','models':{}}
scenes=[]
for model in ('k','s'):
    path=WORK/f'M23{model.upper()}_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m23{model}.jsonl'
    data=path.read_bytes()
    rows=[json.loads(x) for x in data.splitlines() if x.strip()]
    pair=defaultdict(dict)
    arm_counts=Counter(); confusion=Counter(); predicted={'new':Counter(),'twin':Counter()}
    fv_groups=set(); groups=set(); margin_bad=0
    for row in rows:
        a=row['target_arm'].lower(); sid=row['target_scene']; group=row['source_group']
        assert a in ('new','twin') and a not in pair[sid]
        qs={q['id']:q for q in row['questions']}
        q=qs['certificate_action']; assert q['keys']==['accept','reject_conflict','wait']
        p=q['keys'][max(range(3),key=lambda i:q['logits'][i])]
        c=qs['conflicting_vote']
        assert c['keys']==['false','true']
        if not math.isclose(row['M'],c['logits'][1]-c['logits'][0],abs_tol=2e-5): margin_bad+=1
        pair[sid][a]=(row['gold_action'],p,group)
        arm_counts[a]+=1; predicted[a][p]+=1; groups.add(group)
        if a=='twin':
            confusion[f"{row['gold_action']}->{p}"]+=1
            if p=='reject_conflict':fv_groups.add(group)
    assert len(rows)==248 and arm_counts=={'new':124,'twin':124}
    assert len(pair)==124 and len(groups)==17 and margin_bad==0
    assert all(set(v)=={'new','twin'} for v in pair.values())
    assert all(v['new'][0]=='reject_conflict' and v['twin'][0] in ('accept','wait') and v['new'][2]==v['twin'][2] for v in pair.values())
    assert Counter(v['twin'][0] for v in pair.values())=={'accept':102,'wait':22}
    rejected={sid for sid,v in pair.items() if v['new'][1]=='reject_conflict'}
    both=sum(pair[sid]['twin'][1]=='reject_conflict' for sid in rejected)
    ex=expected[model]
    assert dict(confusion)==ex['twin_confusion']
    assert dict(predicted['twin'])==ex['twin_pred_totals']
    assert len(rejected)==ex['native']['new_rejected']
    assert predicted['twin']['reject_conflict']==ex['native']['twin_false_veto']
    assert both==ex['native']['twin_rejected_where_new_recognized']
    assert len(fv_groups)==ex['twin_fv_groups']
    scenes.append(set(pair))
    result['models'][model]={
      'raw_sha256':hashlib.sha256(data).hexdigest(),'rows':len(rows),
      'new_rows':arm_counts['new'],'twin_rows':arm_counts['twin'],
      'groups':len(groups),'new_prediction':dict(predicted['new']),
      'twin_prediction':dict(predicted['twin']),
      'twin_gold_prediction':dict(sorted(confusion.items())),
      'new_rejected':len(rejected),'twin_false_veto':predicted['twin']['reject_conflict'],
      'twin_false_veto_groups':len(fv_groups),
      'twin_rejected_given_new_rejected':both,'margin_mismatch':margin_bad,
      'committed_v8_counts_match':True}
assert scenes[0]==scenes[1]
result['same_124_scenes_between_models']=True
result['status']='PASS'
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'INDEPENDENT_M23_RECOUNT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
k=result['models']['k'];s=result['models']['s']
lines=['# A461 V8 M23 独立原始数据计数复核','',
'状态：PASS（限于 CPU 统计复核，不是独立模型重复实验）。直接从每个模型 248 行原始 JSONL 的三个动作 logits 重新取 argmax，不调用作者分析脚本。','',
'| 指标 | kev-4B | SecJev-0.8B |','|---|---:|---:|',
f"| 新冲突被拒绝 | {k['new_rejected']}/124 | {s['new_rejected']}/124 |",
f"| 合法 twin 错误拒绝 | {k['twin_false_veto']}/124 | {s['twin_false_veto']}/124 |",
f"| 错误拒绝涉及来源组 | {k['twin_false_veto_groups']}/17 | {s['twin_false_veto_groups']}/17 |",
f"| 在 new 已被拒绝时仍误拒 twin | {k['twin_rejected_given_new_rejected']}/{k['new_rejected']} | {s['twin_rejected_given_new_rejected']}/{s['new_rejected']} |",'',
'两模型覆盖相同的 124 个场景；twin Gold 为 accept 102、wait 22。全部三动作 Gold × prediction 混淆计数与 V8 numbers_mech_v5.json 一致；M margin 复算零差异。','',
'本项不证明独立实验重复、自然内部机制或跨任务泛化。不启动新 GPU，不修改冻结数据。完整哈希和混淆矩阵见 INDEPENDENT_M23_RECOUNT.json。']
(OUT/'INDEPENDENT_M23_RECOUNT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('PASS',json.dumps({m:{z:v for z,v in val.items() if z in ('rows','new_rejected','twin_false_veto','twin_false_veto_groups','twin_rejected_given_new_rejected')} for m,val in result['models'].items()}))
