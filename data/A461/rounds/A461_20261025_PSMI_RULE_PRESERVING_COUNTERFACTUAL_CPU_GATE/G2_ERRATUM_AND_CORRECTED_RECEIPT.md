# A461-PSMI G2 勘误与修正回据（2026-10-25）

**性质**：对 `G2_REAL_20261025/analysis.json`（commit ca9eb88）的正式勘误与修正统计。本文件不修改任何已冻结的协议、G0/G1 原始产物或已归档回据；修正仅涉及 G2 汇总统计的三处错误与两处表述收紧。独立依据：`research/analysis/2026-10-25_A461_REAL_G1_103_multihead_conflict_recognition_root_cause_screen.{md,json}`（并行会话独立逐头审计）与 `research/analysis/2026-10-25_A461_V1_V2_paper_readiness_independent_peer_review.md`。

## 勘误 1：N2 第三 oracle 非独立（结果本身经独立路径确认成立）

原 G2 的 N2 段以同 pair_key 的 pair_rows 行状态为"旧状态"——N2 键只有一条 retimed 行，故实为把编辑后状态与自身比较，old/new Gold 恒等，该子门**不构成独立验证**。并行会话经两条独立路径（撤销 L1 追加事件、逆向 N2 时间编辑）重建旧状态后确认 **3/3 Gold 真正不变且模型预测均保持** `record_failed_attempt`。结论：N2 的 Gold 不变性由独立重建路径成立；我方原 G2 该段方法错误、结果碰巧正确，以本勘误替代。

## 勘误 2：N1 等长判据用错（neutral-vs-old 应为 neutral-vs-treatment）

原 G0 manifest 的 `N1_equal_token_count` 以 **neutral vs old** 为判据，错报 0/31。正确判据是 **neutral vs treatment**（两者均为追加事件）。按正确判据重算（本目录 `G2_CORRECTED/n1_flags_corrected.json`）：**29/31 匹配**（LANL L1 9/9、L3A 6/6、T1 6/6、T2 4/6、T3 4/4）；仅 2 条 T2 accept→reject 格不匹配（run-100: 1086 vs 1090；run-125: 411 vs 415，均 +4 tokens）。已执行的 17 条 N1（LANL 15 + T1 2）全部匹配。因此：
- G1 报告与论文草稿中"N1 31/31 不匹配"、"LANL 契约内无法构造等长中性"的表述**错误**，予以撤回；
- N1B 的动机表述（"N1 全不配平"）不成立；N1B 仍是有效的**单字段**配平对照（14/14 vs treatment 匹配），与 N1（结构同形追加）互为补充；
- 真正的配平缺口收窄为：**T2 accept→reject 两条核心格无任何已执行中性臂**。

## 勘误 3：McNemar 配对总体错误（p=0.125，非 0.031）

T2 6 个 failed_to_change 中仅 4 个有已执行 N1B 对照（run101/105/114/121：4 处理错误 vs 4 中性正确）。严格配对双侧精确检验 p = 2×(1/2)^4 = **0.125**。run100/125 无中性臂，不得计入对照。"6/6 failed_to_change" 仅是 Gold 改变轴的结果陈述（旧臂全对、新臂全部未转 reject），不是 6 对 matched contrast。

## 表述收紧

1. **failed_to_change ≠ 单调性违例**：13/20 是未响应；严格符号反转仅 T2 run100（dM=−1.50），且该格无配平对照。论文标题与摘要不得把 13/20 写成 sign reversal。
2. **T2 表型重定性**：独立逐头审计证明 T2 的 6/6 中模型 `conflicting_vote` 头全部输出 false（Gold true）、`evidence_level` 0/6 正确、`quorum` 6/6 正确、动作与模型自身 C/Q 值的规则函数 6/6 一致——**新增冲突识别失败（跨消息 author×round×block 绑定）**，而非"已识别冲突但动作阈值失效"。同 run 的 T3 自然对照（run105/114/125）显示模型能识别**既有**冲突、漏读**新增**冲突。原论文草稿"方向忠实但阈值欠反应"的机制表述按此修正。
3. **N1B 严格风险终点**：无条件动作错误 4/14；old-clean 严格 clean→wrong 为 **2/12**（T1 run105/114：轮次平移票被误读为 quorum 成立）。分母必须显式注明。
4. **LANL 外部效度**：仅 3 个日组且均被 A428 接触过，LANL 侧无未见组可验；扩样只能在 Twins 侧进行。

## 修正聚合（与原 G2 不冲突的部分保持）

| 量 | 原 G2 | 修正后 |
|---|---|---|
| N1 匹配率（vs treatment） | 0/31（判据错误） | **29/31** |
| N1B 严格 clean→wrong | 2/9（分母含旧错误对） | **2/12**（无条件 4/14） |
| T2 matched contrast | "6 对 p=0.031" | **4 对 p=0.125** |
| T2 机制表述 | 动作阈值欠反应 | **新增冲突识别失败**（动作=自身 C/Q 的规则函数 6/6） |
| N2 验证方法 | 第三 oracle 非独立 | 独立重建路径确认 3/3 成立 |
| 严格符号反转 | 隐含 13/20 | **1/20**（run100，无对照） |

## 产物

`G2_CORRECTED/n1_flags_corrected.json`（neutral-vs-treatment 重算）、`G2_CORRECTED/corrected_aggregates.json`（本表机读版）、本文件。原 G2 产物保留不动。
