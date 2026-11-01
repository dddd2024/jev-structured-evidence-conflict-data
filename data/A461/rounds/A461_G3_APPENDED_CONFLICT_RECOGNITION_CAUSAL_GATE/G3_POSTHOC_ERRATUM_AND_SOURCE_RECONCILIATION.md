# A461_G3_POSTHOC_SOURCE_AND_METRIC_ERRATUM：正式勘误与来源对账（2026-10-25）

**性质**：响应独立论文级评审（`dd55688`，MAJOR REVISION）与两份独立证据审计（`3c559a7`、`a66493d`）的正式勘误轮。CPU-only：无模型前向、无 GPU、无新语料读取。本文件修正 G3 手稿 v2 与 G3_RESULT_MEMO 中的全部 P0/P1 事实错误；原 G3 产物保留不动。

## P0-1 勘误：N1B"每对配平且有效"为假

手稿 v2 摘要、§3.4、表 2、§5 声称 N1B 作者置换中性"每对 token 配平"且支持排除形式/作者混杂。逐臂审计（`G3_POSTHOC/n1b_validity_roster.json`）：

| 子集 | 有效且配平 | 分母 |
|---|---:|---:|
| T2 wait→reject | 10 | 10 |
| T2 accept→reject | **3** | **10** |
| 全部 T2 | **13** | **20** |
| 全部 T2+T3 | **19** | **26** |

7 条 accept 格 N1B 使用 `z_neutral_outside_set`（该场景无可用新验证者）——在 validator_set 之外且与处理臂 token 数不等；其 Gold 不变仅因消息不被识别为验证者。手稿相应句子**全部撤回**。有效 13 对 T2 三元组上：处理与中性 C 预测 **13/13 相同**（处理 true 时中性也 true 或都 false 语义未分离；其中 run-338 的**中性对照本身假警报 C=true**，D_C=+7.219）；严格语义特异性 D_C 仅 **7/13** 为正。这些降级为探索性子组观察。

## P0-2 勘误：SHAM_TS/SHAM_RO 违反时间戳契约

两者 6/6 存在 `received` 非递减违例（TS 尾部追加更早时间戳；RO 整表反转），违反构造器对输入语料强制的同一准则。重定性为**蓄意分布外格式压力测试**；其"6/6 与处理预测一致"不构成时间/顺序混杂被排除的证据。SHAM_SA 9/9 全部来自 wait 格（accept 格零覆盖）；N1 六条与对应 N1B 的 state-token SHA 完全相同（非独立变体）。§4.2/§5 "token 长度、作者身份、到达时间、顺序因素被排除"的表述**撤回**，改为：低格式风险（N1B/N1/SA 一致性高）+ 已知契约违例（TS/RO）+ 关键格配平不足（accept 7/10 无有效中性）。

## P0-3 勘误：基线标签错误

摘要与 §4.3 的"低于保持原判基线（16/20）"错误：16/20 实为**新预测等于旧 Gold**（欠反應度量），不是基线。修正：真正的"保持旧决策"策略在新 Gold 下得 **0/20**（20 个 T2 新 Gold 全部变为 reject_conflict）；常数 reject 在蓄意制造冲突的新臂上得 20/20（构造性退化，无用基线）；多数类 10/20 是旧 Gold 分布而非新状态分类器。比较性表述全部移除，改为仅报欠反應度量与退化基线并说明其含义。

## P1-4 勘误：Fisher 检验的可比性与独立性

合并 1/20 vs 6/6（名义 p=3.04e-5）混用两种估计对象（转移 vs 状态）且 2 个 T3 组与 T2 重叠（24 个独立组而非 26）。修正表述：一致端点对比（新 C=true：T2 4/20 vs T3 6/6，p=9.12e-4）；去重叠 T3（1/20 vs 4/4，单侧 p=4.71e-4）仅为描述性类别对比；给出 Clopper-Pearson 区间：清洁旧臂识别 1/17 = **[0.15%, 28.7%]**，T3 6/6 = **[54.1%, 100%]**。"充分功效的确认"改为**独立组确认样本**（无先验功效计算）。

## P1-5 勘误：evidence_level 整数解析错误

G2C `norm()` 把 "0"/"1" 映射为布尔、"2" 留为字符串——全部正确的 level-2 预测被判错。整数解析修正后新臂 E=2 正确：**T2 wait 0/10、T2 accept 1/10、T3 4/6**（原 G2 记 0/26）。相关叙述与表格全部更新；旧工件保留。

## P1-6 来源与预算对账：106 冻结 vs 109 实际执行——已用确定性重跑解决

协议 V1 冻结 `forward_stage_budget=106`；实际执行 109（SHAM_SA 9 而非 6）。独立审计认为 checked-in 构造器无法产出 9 个 SA、"exact executed source is not derivable"。**本勘误以确定性重跑证据纠正该静态判断**：在 HEAD（`dd55688a`）以相同 pinned 语料重跑 checked-in 构造器（`~/wjc/a461-g3-posthoc-erratum-20261025-v1/G0C_RERUN`），`pair_rows.jsonl`、`census.json`、`token_audit.jsonl` 与存档 G0C **逐字节一致**（含 9 SA、planned=109）。机制：SHAM 循环中 TS 失败的 `continue` 不消耗 `sham_used` 配额，故 SA 数（9）可超过每族预算（6）——配额约束的是**完成的三元组**。106→109 的偏差 = 3 条 TS 失败对的 SA-only 追加，仍在 128 绝对上限内。勘误行动：预算记账从"每族计数"改为"完成三元组计数"，偏差如实记录，不追改任何历史工件。

## P1-7 表述收紧

"relational-binding failure"（关系绑定失效）是机制假说而非已确证机制——全文改为 **"behavior consistent with a relational evidence-integration failure"**；独立保留 C 头识别失败、假警报、跨头整合（T3 2 例 accept despite C=true）三类行为。Tang et al. 的机制证据使本行为发现不构成机制新颖性。

## 修正后的核心事实（评审确认有效 + 本轮修正）

1. **真实行为现象（保留）**：合法追加冲突证据下，干净旧臂→新冲突的 C 头识别仅 **1/17**（清洁旧臂合格对）或 1/20（全部 T2 对），run-338 唯一；高格 3/10 旧臂假警报；T3 既有冲突 6/6 识别（其中 2 例动作仍 accept）。
2. **对照缺陷（如实陈述）**：accept 格 7/10 无有效配平中性；TS/RO 为 OOD 压力测试；SA 仅覆盖 wait 格；N1 冗余。
3. **特异性的弱证据**：D_C 正 7/13；唯一真识别的中性对照本身假警报——语义特异性未确立。
4. **机制未确立**：无隐藏态/指针定位、无双向干预、无跨模型复现。

## 产物

`G3_POSTHOC/n1b_validity_roster.json`、`G3_POSTHOC/corrected_metrics.json`、`G3_POSTHOC/provenance_rerun.json`、本文件、手稿 v3（同 commit）。服务器确定性重跑目录 `~/wjc/a461-g3-posthoc-erratum-20261025-v1/G0C_RERUN`（逐字节比对证据）。
