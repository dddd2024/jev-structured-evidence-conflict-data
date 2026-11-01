# A461-PSMI G1+G2：配对原生前向试点与独立分析结果（2026-10-25）

**实验**：`A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE_V1`（+V2 修订）
**阶段**：G1 `A461_PSMI_G1_PAIRED_PILOT`（**COMPLETE**，修正回据）+ G2 `COMPLETE_A461_PSMI_G2_INDEPENDENT_ANALYSIS`
**GPU 授权**：用户明确批准"批准 GPU（A461 G1，103 次 forward）"（AskUserQuestion，2026-10-25）；实际物理前向 **103/103**（≤批准额与 128 协议硬上限）；反传 0、网络 0、工具 0、TEST/CAL 0。

## 1. G1 执行事实

| 项 | 值 |
|---|---|
| 模型 | pinned SecJev-0.8B FP32，RTX 3090，TF32/flash-SDP 关闭，组件 SHA 与 A428 钉一致 |
| 构成 | 34 旧臂 + 31 处理臂 + 14 N1B 配平对照 + 3 N2 + 17 N1 + 4 精度重放 = **103**（等量置换：17 条不配平 N1 让位 14 条 N1B，批准总额不变） |
| 预前向门 | `PASS_A461_PSMI_G1_PRE_FORWARD_GATES`；与 A428 共享场景 **A428_023 跨运行 native token SHA 完全一致** |
| 精度重放 | 4/4 与各自主前向 **逐位一致**（logits 与 token SHA） |
| 勘误 | V1 回据 FAIL 仅因循环后 replay 记账 bug（replay 与 replay 相互比较）；103 次前向早已全部完成并持久化；修正回据 `execution_receipt_corrected.json`，失败尝试目录（5 个）服务器保留 |

## 2. G2 主结果（第三套独立 oracle；动作分支 argmax；旧正确条件化）

### 2.1 Gold 改变轴（GOLD_CHANGING_RESPONSIVENESS）

| 轴 | 旧正确对 | responsive | failed_to_change | baseline_wrong | dM 方向 |
|---|---:|---:|---:|---:|---|
| LANL L1（+1 次失败→investigate） | 9 | 4 | **5** | 0 | **9/9 dM>0**（+1.06～+3.09） |
| Twins T1（+1 有效票→accept） | 5 | 3 | **2** | 1 | 5/5 dM>0（+1.34～+5.92） |
| Twins T2（+冲突票→reject_conflict） | 6 | 0 | **6** | 0 | **5/6 dM>0 且 <2.2，1/6 dM=−1.50（反号）** |
| **合计** | **20** | **7** | **13** | 1 | 19/20 方向正确，1 反号 |

**核心表型**：方向响应完整（19/20 的动作 logit 差向新 Gold 移动），但 **13/20 未越过决策阈值**——欠反应集中在冲突轴（**6/6 全部 failed_to_change**，dM 仅 +0.70～+2.18，另 1 例 −1.50）。

### 2.2 Gold 不变风险追加轴（NONREGRESSION）

| 轴 | 旧正确对 | held | violation |
|---|---:|---:|---:|
| LANL L3A（再+1 次真实失败，Gold 保持 investigate） | 4 | **4** | 0 |
| Twins T3（C=1 再+合法票，Gold 保持 reject_conflict） | 3 | **3** | 0 |
| （L3A baseline_wrong 2/6：R=true 旧场景漏升级） | | | |

### 2.3 扰动对照（GOLD_INVARIANT_NUISANCE）

| 对照 | 旧正确对 | violation | 说明 |
|---|---:|---:|---|
| **N1B token 配平中性**（T1 轮次平移/T2 换作者） | 5+4 | **2（均 T1）** | 等长语义空编辑可翻转动作——格式敏感性实证 |
| N1 不配平中性（LANL Success 追加） | 9(L1)+4(L3A) | 0（L1 全保持） | 结构匹配但 token 不配平，仅作探索 |
| N2 时间重定时（仅改窗内秒值） | 3 | **0（3/3 保持）** | A428_021/024 时间线索在受控重定时不复现 |

### 2.4 统计边界

- 聚类结构：LANL 3 个日组、Twins 3+ 个 run 组；**不得按场景 IID 计置信区间**。
- T2 的 6 个 failed_to_change 与配平对照 0 违例构成 6 个同向 discordant 单位，若独立则精确 McNemar p=0.031；实际 ≥3 聚类，**只作探索性信号报告**。
- N1B 2/5 违例与处理臂对照：n 过小，不构成检验。
- 本试点为**探索性**：不证明部署漏洞、不证明真实攻击者写通道、不证明机制（Q/K/LoRA 白盒需另立协议+授权）。

## 3. 结论（严格分级）

1. **事实（已验证）**：103 次原生前向、双 oracle、配平对照、跨运行 token 同一性、逐位重放。
2. **现象（可复现于本冻结对集）**：方向响应完整（19/20）；决策级欠反应 13/20，冲突轴 6/6；配平中性可翻转 2/9；时间重定时不翻转 3/3。
3. **未证明**：机制本体、真实部署安全效果、跨模型泛化（单 checkpoint 单架构）。
4. **与先验结果的关系**：T2 欠反应与 A430 G1 试点（3/6 SHAM 冲突漏检）、A428 试点冲突漏拒同向；N2 与 A428_021/024 的表面线索相反（受控后不成立）——正是预注册对照的价值。

## 4. 对论文的含义

本试点与已归档证据链（P0 crossed 不可行性、A430 最小对方法学、本轮配平反事实审计）共同支持一篇**方法+审计型论文**：
- 主张：在 oracle 可执行、来源内、token 受控的条件下，安全型小模型的策略证据**方向读出**保真而**阈值读出**系统性欠反应（冲突轴最重），且该测量需要配平对照才能与格式效应区分；
- 贡献：预注册反事实审计协议（双 oracle + 契约内配平对照 + 物理前向清单 + 全链勘误保留）；
- 诚实边界：单模型、探索性、聚类小样本、LANL 契约内无法构造配平中性（如实登记）。

## 5. 产物

`G1_REAL_20261025/`（raw_native_logits_103_requests.jsonl、pre_forward_token_gate_receipt.json、replay_receipt.json、execution_receipt(.corrected).json、admission_receipt_copy.json、SHA256SUMS*）；`G2_REAL_20261025/`（analysis.json、per_pair_outcomes.jsonl、execution_receipt.json）。服务器 `~/wjc/a461-psmi-counterfactual-cpu-gate-20261025-v1/`（含全部失败尝试与 G2 前两版目录）。G2 勘误：v1 自比较缺陷（rs[0]=new 臂）→ v3 修正（`788ae31`）。
