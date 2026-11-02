from pathlib import Path
import json
from collections import Counter
p=Path.home()/'wjc/a461-g5-minimal-patch-pilot-20261025-v1/M23K_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m23k.jsonl'
rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
print('total',len(rows),'arms',Counter(x['target_arm'] for x in rows),'conditions',Counter(x['condition'] for x in rows))
for col in ('target_scene','source_group','token_ids_sha256'):
 print(col,'unique',len({x[col] for x in rows}),'top',Counter(x[col] for x in rows).most_common(4))
for i,x in enumerate(rows[:4]):
 print(i,x['target_arm'],x['target_scene'][:16],x['source_group'],x['gold_action'],x.get('condition'),x.get('run'))
