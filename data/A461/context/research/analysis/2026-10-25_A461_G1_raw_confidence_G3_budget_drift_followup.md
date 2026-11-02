# A461 G1 原生概率结构复算、同旧状态双编辑案例与 G3 预算不可达门审计

日期：2026-10-25。性质：基于 GitHub 归档的 **103 条真实 SecJev-0.8B FP32 logits** 的二次定量分析，以及 G3 冻结构造器、推理脚本和准入回据的静态一致性核查。**没有新的 GPU forward、服务器实验、TEST/CAL 读取或白盒干预。**

机器可读逐组原生派生值：[`2026-10-25_A461_G1_raw_confidence_G3_budget_drift_followup.json`](2026-10-25_A461_G1_raw_confidence_G3_budget_drift_followup.json)。

## A. 冻结输入和独立重算口径

- `G1_REAL_20261025/raw_native_logits_103_requests.jsonl` Git blob SHA `5b4a6903171d0a5848162a335530492f6e1a6046`，103 行；原生角色 34 old + 31 treatment + 14 N1B + 17 N1 + 3 N2 + 4 replay。
- `G0_REAL_20261025/pair_rows.jsonl` Git blob SHA `24526c643434544b9a02587abc2d57e2c13ef627`，65 行（原始old/new配对），其中31个主实验配对。
- `G0_N1B_REAL_20261025/n1b_rows.jsonl` Git blob SHA `02342e1dc0a188dd7390d0fd911710d29622a358`，14 条。
- 解析各行 `questions[]` 中 `keys/probs/logits`；treatment 按冻结G0 `row_id`、old按`pair_key:old`、N1B按另存 `row_id` 关联。概率来自模型在固定候选菜单上的 softmax，**不是经过外部校准的真实世界置信度**。
- 本轮沿用仓库正式G2勘误与G−1文献前置决策；只是旧实验复算，未新开研究方向。

## B. 新增冲突错误不只是 argmax 轻微未翻转

| T2 run | 新增冲突 Gold | 模型冲突为true概率 | 错误动作 | Gold动作 |
|---|---|---:|---|---|
|100|true|0.157098|accept|reject_conflict|
|101|true|0.000260|wait|reject_conflict|
|105|true|0.000077|wait|reject_conflict|
|114|true|0.003280|wait|reject_conflict|
|121|true|0.010938|wait|reject_conflict|
|125|true|0.000012|accept|reject_conflict|

T2真实新状态：冲突问题正确 **0/6**，其中 **5/6** 对错误标签 `false` 的模型softmax概率至少0.98；正确 `true` 的概率中位数 **0.001770**、平均值 0.028611（明显受 run100 影响）。这否定了“六个问题都只是argmax略低于阈值”这一解释，但不排除其神经特征部分存在。因6组是定向选取DEV，不可把0/6当未见总体参数；即使错误地将它们视作6次独立同分布伯努利，0/6成功的双侧95% Clopper–Pearson上界仍约0.459，不能断言总体成功率为零。

T3既有冲突 4 个真实新状态，冲突true概率为 [0.003075, 0.719921, 0.999647, 0.999928]，argmax识别正确 **3/4**；这也不是4/4。三个同run组105/114/125呈现T2漏识别、T3识别，但**T2和T3使用不同旧状态**，同run并不等于同state严格配对，不能宣称已证明神经层面的增量更新机制。

## C. 新增可用的同一旧状态对照：run121 的 T1 与 T2

在 run121，Twins T1（增加quorum相关投票）与T2（新增同作者异块冲突）两套旧状态的原生token SHA严格相同，均为
`6b00dc076ca01beb5bcf5443cba46699b44efcc6966d7cbf45fb8d70f5092ac4`。同run的其他T1/T2/T3旧状态token SHA通常不同；在本轮逐组检查的16个Twins主轴里，仅 **run121 T1/T2** 具有该严格同旧状态证据。

- old：冲突概率0.000873、quorum成立概率0.007422、动作为wait（wait概率0.98077）。
- T1处理：quorum成立概率升为0.565320并选true（正确），但动作仍选择wait（wait概率0.79009，Gold为accept）；单独问题行的输出跨问题不一致。
- T2处理：冲突成立概率升为0.010938但仍选false（Gold为true），动作依然wait（wait概率0.88639，Gold为reject_conflict）。
- 两套N1B都仍为来源Gold wait，并且原生模型选择wait；它们不是同一个编辑，也不是神经干预。

**解释边界**：这一严格共享旧状态的双编辑病例说明，在同一原始状态下，模型可对quorum证据形成正确的二元判断却仍不输出正确动作，而对真实新增冲突证据的二元判断仍错误。这是将“规则事实识别”与“动作独立读出”拆成两个可证伪终点的优质机制诊断病例，但 (n=1)，不得作为已证明的因果链；C、Q、A是独立渲染的问题行，不是已确认的串行神经中介。

## D. G3：冻结106次、运行器109次，导致预forward检查不可满足（P0）

逐项对照 **当前代码**：

- 冻结G3 `PROTOCOL_V1.json` 中 `hard_resource_bounds.forward_stage_budget = 106`（另有绝对cap128）。
- G0C构造器 `A461_g3_conflict_gate_cpu_v1.py`：`CAPS=10+10+6`即最多26对；对每对1 treatment +1 N1B；`N1_CAP=6`；`SHAM_CAP=6` 对六对最多各产生 SA/TS/RO 三臂（18个SHAM）；`REPLAYS=4`；`BUDGET=106`。
- 因此当前构造器总上限为 `26 old + 26 treatment + 26 N1B + 6 N1 + 18 SHAM + 4 replay = 106`。如果任意单元不足或SHAM_TS被跳过，则更少。
- 后续 `A461_g3_g1c_paired_forwards_fp32_v1.py` 却固定 `BUDGET=109`，将编辑臂按79计（其中 **21 SHAM=9 SA+6 TS+6 RO**），并在任何forward前要求 `len(plan)+REPLAYS == 109`。
- `admission_receipt_a461_g3.json` 同样写109，且描述109为原V1冻结预算；**该描述与现存V1的106不一致**，不能仅以109小于128视为满足冻结阶段预算。

**静态判决：`P0_STOP_G3_PLAN_BUDGET_MISMATCH`。** 只要G1C接收的是该冻结构造器所产G0C行，当前 `109` 的精确检查就不能成立，因而应在GPU推理前失败；这不是实际服务器已报错的证据。调整方案：优先沿用V1的106上限，执行脚本按经独立双路径复核的G0C真实计划行数运行，回据以实际forward数核销且不得超过106。若确实需要另加3个SHAM-SA，必须先重新冻结并核验新版协议、控制数、授权与独立执行回据，不得事后把旧V1写成109。

## E. 与上一轮未解除的来源合同问题合并审查

仍要解决：`SHAM_TS`新消息的更早received时间直接追加到末尾破坏非降序；`SHAM_RO`反转完整消息列表破坏时序；N1B缺新validator时fallback为名单外作者；六条SHAM优先配给wait格，Q=1 accept格可能完全缺SHAM。Gold不变、token等长、独立二路径重建均**不能代替来源合法性**。

据此，新的GPU阶段 **不应被标为已准入并且不能宣称执行成功**。有效的下一步是 `A461_G3_G0C_SOURCE_CONTRACT_AND_BUDGET_REPAIR`（G3前置审计/修复阶段，不是新的科学候选方向）。先核对所有来源逐臂合法性、计划行数及精确预算，再决定能否进行 `A461_G3_G1C_PAIRED_FORWARDS`。建议保存各阶段STOP/PASS及双路径回读回据，仍采用 `~/wjc` 下服务器路径；本报告仅已在GitHub归档，未在远端执行或核验GPT Library双备份。

## F. 当前可用的论文表述

支持：SecJev-0.8B在经过来源Gold确定的新增冲突票输入中出现真实模型冲突识别不足，6条pilot均预测false，其中多数原生softmax明显偏向错误选项；有同状态的run121双编辑探索性诊断，以及不同状态的T3既有冲突对照。

不支持：六例全是同种神经机制；已有已完成的G3未见组复制结果；已经证明C→A串行因果中介；已确认部署环境中的越权攻击；以V1直接执行109次模型forward；或以pilot误分类本身认定独立论文创新。

这轮不涉及新的文献创新判断：G−1中的 Tang et al. ICML2026 实体状态跟踪、SecJev源论文、One Word Opens the Gate 等仍构成必须对照的已有研究。正式白盒机制结论仍取决于有效G3复现后另行冻结的双向神经干预。
