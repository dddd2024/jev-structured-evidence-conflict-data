# A461-PSMI V1/V2：并行Agent协议独立静态审查、旧24份原生输入的Gold影子核验与三个执行缺口

**时间**：2026-10-25 America/New_York。**独立增量文件，不修改另一Agent的协议、源数据、审查决定和执行脚本。** 同名JSON保存机器可审计的SHA、逐编号资格/Oracle测试和停止条件。本报告不是正式G0：无SecJev全DEV读取、无原生token encode、无双Oracle独立实现、无GPU、无模型请求。

## 1. 并行Agent提交变化已经纳入，不再重复设计

- A461新靶向G−1：`5871f1f6...`，`NOVELTY_DELTA_TESTABLE`，**只放行CPU G0**，不批准GPU。不能追认02:38:42Z首次冻结的旧候选协议，但可用于后来新V1。
- 新正式G0协议：`research/experiments/2026-10-25_A461_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE_PROTOCOL_V1.json`，blob `2519620e105bd8fadcae17fb20b1e6026608b0c5`，commit `20898b807...`（04:08:05Z），时间顺序晚于G−1，合规。
- 随后的V2增补：`research/experiments/2026-10-25_A461_PSMI_CPU_GATE_AMENDMENT_V2_ENDPOINTS_AND_CHRONOLOGY.json`，blob `470349015b8d13c831db4afe3268187e9feb9871`，commit `311b349064...`（04:10:06Z）。另一Agent已主动**纳入我们此前发现的三端点区分**，追加了**LANL_L3A_RISK_NONREGRESSION**，并纠正旧候选协议的G−1时序解读。此前关于缺少LANL Gold不变分支的批评已解决，不能再将其报告成当前漏洞。
- 新Runbook路径：`research/experiments/2026-10-25_A461_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE_RUNBOOK.md`。它指向两个将在 `research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/` 下提供的CPU脚本；**审查时这两个脚本均在GitHub返回404**，因此不能声称已经执行或可照Runbook直接启动。

## 2. 对旧A428已冻结原生请求的影子可行性检查（不是G0）

只读旧`A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0A_REAL_20261023/frozen_model_inputs.jsonl`（24条，blob`13adf301dd67c5cc787c72b4b9ace695c52fef4e`）及旧G2独立Gold/预测（blob`f02741bb8cfea2f45c1c73c435d90f8cb064cd6b`），用单独简单来源规则从state重算12条Twins原始Gold，**12/12与旧Gold完全一致**。随后按新版实验V1的新增投票条件在内存中构造**静态规则增量的必要条件检查**（未使用独立第二Oracle、原生decoder、tokenizer或真实性/来源控制审查）：

| Twins条件 | 旧输入中满足者 | 原Gold→拟新Gold | 旧输入ID |
|---|---:|---|---|
| T1合法新增投票跨quorum | 1条 / 1个来源run组 | wait→accept | `A428_001` |
| T2已有候选支持者投另一现有块 | 4条 / 4个组 | wait或accept→reject_conflict | `A428_001,004,005,006` |
| T3已有真实冲突后新增合法候选票 | 4条 / 4个组 | reject_conflict→reject_conflict | `A428_007,008,009,010` |

9个“分支候选”涉及8条独立旧scene，`A428_001`同时满足T1、T2，不能按9个独立组统计。原始输入具有所需的`received_messages`字段、`validator_set`和`decision_time`；在简单source-local规则运算中，按确定性选择的新message不会触发预期外的C/Q变化，但**不意味着新message已有真实签名或符合更强部署来源证明**。这种小集合的静态影子核对只说明V1三个Twins分支在已归档的旧原生记录里有结构支持，不能代替797条原始DEV、双路径Gold、token核验。

对于旧的12条LANL FP32输入，独立source-local规则核算原始triage与12/12旧Gold一致。V2新增加L3A（Gold保持investigate、添加一次真实同窗失败）时，若沿用固定条件`R_old=1`、`older_summary.failed_attempts=0`、目的地已知、无时间重复，可找到**3条旧输入**：`A428_017, A428_018, A428_020`，覆盖`lanl:day:48,day:49`两组。简单规则内存模拟选择新合法秒数149、152、151时三者Gold都保持investigate。旧`A428_019`存在重复300秒，不满足V2明确禁止同秒的准入条件。**这是3条旧场景的单路径静态影子样例，不是3对已双Oracle验证的G0实验，不能把同组重复当新来源。** 历史整个DEV的77条原Gold investigate仍须按完整G0执行规则独立检验。

## 3. G0执行前实际剩余的三个技术/科研合同问题

### QA-1：N1被称为长度匹配，但目前仅结构匹配

V1 `negative_controls.N1_NEUTRAL_APPEND`承诺对每个实验臂添加“same-shape”中性事件；`N3_NATIVE_TOKEN_AUDIT`会记录token数/SHA，但协议对N1与真正的风险增量并未设置`equal native token count`的硬判定或`STOP_UNMATCHED_NEUTRAL_CONTROL`。例如：
- Twins-T1中新投票者在`validator_set`内，中性臂却使用集合外作者，两者字符/词元可能不同；
- LANL-L1合法新失败LogOn的中性臂为`Success` LogOn，即使结构同形，`Fail`与`Success`token长度并未事先证明相等；
- Twins-T3中性增量为`kind=proposal`而主臂为`vote`，同样不能把JSON字段结构一致等同于token等长。

而 G−1 `NOVELTY_DELTA_TESTABLE` 的独立竞争对照明确要求与**matched-length neutral events**比较。故建议：G0可全部先CPU渲染；但必须**逐臂标记** `N1_TOKEN_COUNT_MATCHED=true/false`、真正的token位置差异，必要时尝试事先规定的中性作者/数值选择算法配平；不匹配者只能作为不配平探索，**严禁进入针对One Word Opens the Gate等近似先例的严格因果特异性比较**。是否STOP整个GPU取决于匹配后每族剩余eligible配对数，需预先确定而不能看到预测后再筛选。N2“同位数字宽”同样不保证native token相等（已知A428_021 vs024差2 token）。

### QA-2：中性与时间负对照的具体生成算法仍存在自由度

协议对主处理臂冻结了作者/块/时间选择规则，但N1的“author not in validator_set / non-supporter valid author / proposal”等文案没有冻结**确切字符串、身份优先序/截断规则**，N2“other unused in-window values preserving ordering and digit width where possible”没有确定候选集合、选值tie-break与失败处置。双Agent可以据此产生不同的token、来源验证和结果，难以逐blob一致回读。建议在真正代码提交前用**预注册确定性控制构造器**规范化，并保存每个选择的理由/候选集合；不用修改已冻结V1文本，可由明确引用V1/V2的新增执行QA工件记录，不得后见模型结果才调整。

### QA-3：目前Runbook缺少两份它引用的可执行文件

检查GitHub main(`311b3490644d07df07b41cf1530cd35e600320bf`)时：
- `research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/A461_psmi_counterfactual_cpu_gate_v1.py` → 404
- `research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/A461_psmi_independent_gate_verifier_v1.py` → 404

另一Agent可能还在本地开发；此结论仅对**当前已经提交的GitHub main**成立，不能推断对方放弃任务或永远无法执行。新G0必须先保证主程序+独立验证者都提交并有可复核SHA、局部自检PASS，再从`~/wjc`在一致的main上以CPU-only真正执行。不得在Runbook存在的情况下直接汇报G0已经完成。

## 4. GPU预算/优先级

A461当前G−1已允许CPU，**正式V1/V2设计存在且最新V2补齐严格非回归**。但是G0本轮尚未执行，验证通过的新source-native双Oracle pair=0，批准GPU时数=0。拟议128个原生forward只是后续条件预算，并非当前授权。若要以N1/N2负对照严格比较两族错误，应在冻结pilot之前按每个scene几次actual forwards计算容量/统计功效；不允许将若干旧A428相近模板当成未来独立复现或校准当前研究测试集。

下一步优先：等待/检查并行Agent的G0代码，执行前独立QA其N1/N2确定性、native token匹配和两路径Gold；随后关注真正RUN CPU证据和双端归档，避免我方抢写另Agent所有权的`research/rounds/A461...`路径。若G0证实没有足够合法配对或没有匹配N1，不应为了提高GPU使用而跳过硬门。

**本轮资源**：仅解析24条已冻结A428旧原生输入并做内存中单路径规则模拟，模型/本地服务器/新原始DEV/TRAIN/CAL/TEST读取为0，GPU0；此文件存GitHub新增analysis路径及独立回读。不声称学校服务器或GPT Library双端备份已完成。
