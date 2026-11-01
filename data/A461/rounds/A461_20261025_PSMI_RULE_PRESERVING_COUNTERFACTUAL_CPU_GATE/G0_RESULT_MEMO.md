# A461-PSMI G0（规则保持反事实对 CPU 准入门）：执行结果（2026-10-25）

**实验**：`A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE_V1`（+ V2 修订）
**阶段**：G0 CPU ONLY —— **判决：`COMPLETE_A461_PSMI_G0_CPU_GATE`（双路径 PASS；31 对 + 配平对照冻结；GPU 0 次前向）**
**执行依据**：G−1 `5871f1f`（NOVELTY_DELTA_TESTABLE，CPU-only GO）→ V1 `20898b8` → V2 `311b349` → 脚本 `495dde0`/`823e9bd`/`1e172e2`/`a06d71e`/`11eede9`/`0f80028`/`6ffe680`。GitHub 提交时序满足"文献先于协议"（针对新 G0 协议；旧登记协议 a930540 的时序问题按 V2 修订案记录在案）。
**并行协调**：Issue #2 认领回执（comment 6393454987）；shadow-QA 与预算/功效审计的三项约束全部落实（见 §3）。

## 1. 执行事实

| 项 | 值 |
|---|---|
| 语料 | pinned `development.jsonl.gz`，SHA `2920e1c9…` 校验通过；仅 DEV（Twins 797 行/42 组、LANL 328 行/7 组，全部 `_meta.split=development`） |
| 交叉核对 | LANL oracle vs A427 归档 **328/328** 逐行一致；Twins oracle vs A428 归档 gold **12/12** 场景一致 |
| 模型 | CPU 检查点加载 **1 次**（仅 tokenizer/渲染器，`kev/model.py`+`api.py` SHA 与 A428 钉一致）；backbone forward **0**、GPU **0**、网络 **0**、TEST/CAL **0** |
| 渲染 | Kev 原生 `SystemOneRequest → to_record → encode(strict=True)`，max 8192，无截断 |
| 独立复核 | 独立编写的第二路径 verifier：归档交叉核对、逐对 oracle 复算、**编辑逐行重放**、**token 重渲染 65/65 MATCH**、**N1b 复核 14/14** |

## 2. 真实 DEV 普查与冻结配对

| 轴 | 合格起点 | 冻结对 | 说明 |
|---|---:|---:|---|
| LANL L1（B 阈值：4→5 次失败） | 30（day48/49/50 = 11/11/8） | 9（3/日组） | Gold：record_failed_attempt 或 continue_monitoring → investigate |
| LANL L3A（R=1 非回归） | 75（17/32/26） | 6（2/日组） | Gold 保持 investigate |
| Twins T1（Q 轴：wait→accept） | **93** | 6 | support=q-1、新验证者一票跨阈值 |
| Twins T2（C 轴：→reject_conflict） | **331** | 6 | 既有支持者对另一观测块投票 |
| Twins T3（C=1 稳定性） | **77** | 4 | 追加合法票，Gold 保持 reject_conflict |
| LANL N2（时间不变性） | — | 3 | 仅改窗内失败事件秒值，Gold 不变 |
| **合计** | | **31 对 / 65 臂** | 物理前向计划 **103 ≤ 128**（34 旧臂共享基线 + 65 臂 + 4 精度重放） |

## 3. 负对照与 QA 约束落实

- **N1（结构匹配中性追加）**：31/31 全部构建且 oracle 逐臂确认 Gold 不变；token 审计显示 **31/31 token 数均与旧臂不匹配**（如实标记 `N1_equal_token_count=false`）——按 shadow QA QA-1，不配平者**不进入**与 arXiv:2610.12292 的严格因果特异性对比。
- **N1B（token 配平中性，先于任何模型运行预注册）**：Twins T1/T3 用**同票轮次平移**（契约内：语料 3582/9120 条消息处于非 candidate_round）、T2 用**新验证者换作者**；CPU tokenizer 等长扫描后 **14/16 Twins 对获得等长配平对照**（2 个 T2 对无新验证者可换，`no_candidate`）；**LANL 记录 `INFEASIBLE_IN_CONTRACT`**（语料 5104/5104 事件均为窗内 LogOn，任何窗内已知目的地失败都改变 B，契约内无法构造等长中性）——作为诚实的可行性边界报告。独立 verifier 14/14 复核通过。
- **N2（Gold 不变时间重定时）**：LANL 3 行（每日组 1 行），delta 扫描 1..59 确定性选择，digit_width_change 如实记录。
- **N3（token 审计）**：65 臂逐行 token 数/SHA/首差异下标；无任何 "matched" 声称除非严格相等。

## 4. 执行勘误（保留失败产物，不覆盖）

| 尝试 | 结果 | 处置 |
|---|---|---|
| G0 attempt1 | token SHA 不一致（row 33）：渲染器对 dict 插入序敏感，追加消息键序 `round,received` vs 文件序 `received,round` | 根因修复（构造后 canon 规范化 + 渲染前 canon 往返），commit `823e9bd`；服务器目录 `G0_ATTEMPT1_KEYORDER_SHA_MISMATCH` 保留 |
| G0 attempt2 | token_audit row_id 与 pair_rows 不一致 | `1e172e2`；`G0_ATTEMPT2_ROWID_MISMATCH` 保留 |
| G0 attempt3 | 服务器在推送被拒窗口拉到旧脚本 | `G0_ATTEMPT3_STALE_SCRIPT` 保留 |
| N1B attempt1/2 | LANL 哈希查找 KeyError / 空 alt_rounds IndexError | `0f80028`/`6ffe680`；对应目录保留 |
| G0_VERIFY 首跑 | --n1b 未生效（目录已存在断言） | 移为 `G0_VERIFY_ATTEMPT4_PRE_N1B` 后重跑 |

## 5. 边界与下一步

- 本轮是**准入与冻结**：不产生任何模型行为结论、不证明单调性违例、不构成论文创新声明。
- G1（GPU 配对前向）为条件性下一步：**103 次物理前向 ≤ 128 上限**，预算清单见 `G0_FORWARD_MANIFEST_20261025/physical_forward_manifest.json`（含基线复用策略与逐行 native_request SHA）。**GPU 未获许可**；按 A430 G1 先例需用户明确批准。
- 统计边界（预算审计确认）：3 个 LANL 日组为聚类而非 IID；配对 McNemar 精确检验需 ≥6 个独立同向 discordant 单位才有 p<.05；G1 定位为探索性 pilot。

## 6. 产物

`G0_REAL_20261025/`（pair_rows.jsonl 65 臂、census.json、token_audit.jsonl、execution_receipt.json、SHA256SUMS）、`G0_VERIFY_REAL_20261025/`（independent_review.json：PASS，row_verification 34 对 + token_rerender 65/65 + n1b 14/14）、`G0_N1B_REAL_20261025/`（n1b_rows.jsonl 14 配平 + 2 no_candidate 记录、n1b_token_audit.jsonl、execution_receipt.json）、`G0_FORWARD_MANIFEST_20261025/`（physical_forward_manifest.json：103 ≤ 128）、执行日志 3 份。服务器原件 `~/wjc/a461-psmi-counterfactual-cpu-gate-20261025-v1/`（含全部失败尝试目录）。
