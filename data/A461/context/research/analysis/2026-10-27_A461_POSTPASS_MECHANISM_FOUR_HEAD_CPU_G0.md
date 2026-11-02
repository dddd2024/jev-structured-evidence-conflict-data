# A461 后续机制研究：四原生读出 CPU 独立复核 G0（已执行）

**日期：** 2026-10-27。**状态：`CPU_G0_COMPLETE / NO_NEW_GPU`**。科研任务沿用 A521 的 `TYPED_GOLD_AND_RELATION_MATCH_CPU_PREFLIGHT`；本报告仅关闭其「已有 K-C 四读出 + 冻结 host Gold」部分，**关系 witness 匹配并未完成/并未准入 GPU**。A461 V3 当前 `PAPER_AUDIT_PASS` 不因此修改；不是再次论文审计。

## 1. 输入与来源（只读冻结数据）

- kev-4B K-C 原生四题 FP32 GPU raw：`G2_K4B_KC_GPU_R1/G2_K4B_KC_GPU_RUNS/ATTEMPT_R1/raw_native_logits_k4b_kc.jsonl`，Git blob `19d3a06c27953b1f2b4dcd2770394d28741a69fd`，417 行，原物理 GPU 实验已经完成。
- 冻结设计：`G2_K4B_KC_FREEZE_R1/k4b_kc_design.json`，Git blob `cd4cd9e5632cfa1b8aa476b94a332e3705af2f0f`。
- 独立原始 oracle：Stage-A 冻结候选 roster，Git blob `1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8`，172 candidates，字段 `oracle_new`、`oracle_old`、`oracle_sa` 和合法追加事件 `declared_edit_new`。**这不是把模型预测或 Stage-A 分析标签冒充 Gold**。Git 仓库克隆后可用 `git cat-file blob 1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8` 回读。

每对以 `(donor_scene_sha256,host_scene_sha256)` 关联 main/SA-sham/dose；用上述冻结设计检查 donor 与 host 的来源组；从 112 个配对中排除 8 个同组，剩余 104。所有 8 个目标 host 的 `oracle_new.conflicting_vote=true` 与 `oracle_new.certificate_action=reject_conflict` 全部验证（104/104）。其中 6 个 host 的 Gold quorum=true，2 个 host 的 Gold quorum=false。

## 2. 独立复算（不是作者总结的转述）

原生 `conflicting_vote` 和 `certificate_action` 按 question logits 的 argmax 解析。`evidence_level` 是 ordered score；提供两种**探索性**测量：
- 类别诊断：最高 logit 是否落在等级 2（**不能等同于官方有序评分的 Gold 正确性**）。
- 连续诊断：令 `E_T=Σ_{k∈{0,1,2}} k·softmax(logits_k/T)`；报告 `ΔE_T=E_T(main)−E_T(sham/dose)`，仅衡量原生 logits 对等级 2 的移动，**不能冒称模型的正式 evidence_level 输出校准分数**。T=1 为默认，另作 0.5/2.41/5 敏感性分析。

| 复核指标 | 独立 CPU 结果 |
|---|---:|
| K-C raw | 417/417 完整四题 |
| 跨组有效 main/sham/dose 配对 | 104 |
| main 的 C=true 且 A=reject_conflict | **53/104** |
| sham / dose 的 C∩A | **0/104 / 0/104** |
| main `evidence_level` 的 argmax=2 | **24/104**（都发生在 53 次 C∩A 内） |
| main 相比 sham 的 E argmax 变化 | **24/104**（23 次 0→2，1 次 1→2） |
| `ΔE_{T=1}` main > sham | **103/104** |
| `ΔE_{T=1}` main > dose | **99/104** |
| `ΔE_{T=1}` main−sham 中位数 | **+0.340683** |
| `ΔE_{T=1}` main−dose 中位数 | **+0.196268** |
| 53 次 C∩A 中 E 连续诊断提升 | **53/53** |
| 51 次未实现 C∩A 中 E 连续诊断提升 | **50/51** |
| quorum main vs sham 的 argmax 变化 | **0/104** |
| quorum 与冻结 host Gold 不符（main 与 sham 均） | **26/104**（来自 2/8 个 host） |
| 53 次 C∩A 修复中 quorum 仍 Gold 错误 | **6/53** |

**温度稳健性（描述性；不是统计独立的 104 样本）：**

| T | E(main)>E(sham) | E(main)>E(dose) | median ΔE main−sham | median ΔE main−dose |
|---:|---:|---:|---:|---:|
| 0.5 | 103/104 | 99/104 | +0.444234 | +0.268664 |
| 1 | 103/104 | 99/104 | +0.340683 | +0.196268 |
| 2.41 | 103/104 | 99/104 | +0.160281 | +0.087472 |
| 5 | 103/104 | 99/104 | +0.079462 | +0.042660 |

来源独立性的界限：14 个 donor、8 个 host 被重复配对，因此不可把 104 个单元看成 104 个独立 Gold 测试。T 仅为分析温度，不是已经验证的模型生产 temperature 参数。

## 3. 新发现的科学意义（**诊断，不是已确立机制**）

**第一，行为层面的联合修复并不等价于四个 typed 读出全部正确。** 因为原生 C∩A 修复中的 6 次，quorum 原始输出仍与冻结 Gold 不符；quorum 在本轮 main/sham 之间 0 次 argmax 变化。这限制任何「全部安全证书被修复」的扩张主张。注意：quorum Gold false 的两个 host 仅共享 26 个配对，**不可当成 26 次独立错误案例**。

**第二，evidence_level 的连续变化远比其 argmax 翻转普遍。** 尽管只有 24/104 次 E 最高类别变为 2，但 103/104 次移植均使由原始 logits 推导的 E 序数期望高于 sham；即使在 51 次 C∩A 未联合修复的组合中仍有 50 次为正。**这提示不同头的下游 margin/阈值可能不同，但不能由此证明同一内部路径或读取机制。**

**第三，当前“编码失败 vs 使用失败”仍不能区分。** 全片段自然激活移植可能同时改变多个潜在特征，并与宿主其他中介交互；既不能认定 E/C/A 共享同一关系特征，也不能因为 Q 不变认定 Q 的电路完全隔离。**须使用对应的 row-specific/path-specific 因果干预及 witness-matched 语义反事实。**

## 4. 下一步具体任务与准入门

唯一主线名：**`A521_20261027_TYPED_GOLD_AND_RELATION_MATCH_CPU_PREFLIGHT`（剩余部分，CPU；尚未执行）**。不立即申请/运行 GPU。

1. **核实 ordered-score 官方读出语义**：从 pinned kev 源码、实际 native score 接口和校准约定确认 `evidence_level` 正式输出；T=1、T=2.41 的探索性差异不能直接当作正式的分数纠正；定量分数应与 `oracle_new` 的正式 Gold（冲突→等级 2）比较。
2. **读取真实场景的完整见证关系**（作者、轮次、区块、已有支持票与新冲突票）；不要用不同 source groups 中字符串 `v0`、`b2` 恰好相同来冒充同一个实体。构造 role-normalized 的 witness ID 和 token/长度匹配验证；明确哪些反事实改变冲突 Gold，哪些只改变非因果表面信息。
3. **建立可判别实验的 2×2 严格对照**：在固定 host/Gold、供体语义角色以及 model recognition status 尽可能不共变的前提下，区分“正确绑定的关系证据”和“同标签但错见证/仅正类状态”。若无法完成独立匹配，直接 `NOT_ADMITTED`，不得把已有 Stage-F 的混杂类别当成已隔离因子。
4. **只有通过 CPU 门后才冻结路径级最小实验**：模型内部可观测层/位置上分离内容编码、读出路由、宿主交互；同一个 host 的不同 typed row 分别报告 `ΔC, ΔA, ΔE(official score), ΔQ`，其终点、保留负对照、独立 source groups 和可证伪阈值先于 GPU 预注册。
5. 新 GPU 必须使用已登记的研究授权窗口与冻结预算、CPU 自测、持久 ledger、模型和代码 identity pins；所有服务器文件必须在 `~/wjc`。该任务不是对已通过审计的 v9 再做一次审计，也不自动撤销其限定 PASS。

## 5. 已核对的直接文献

- Lepori et al., ACL 2026, `Language Models Struggle to Use Representations Learned In-Context`，展示 encode 与 use 的可分离（https://aclanthology.org/2026.acl-long.676/），因此只说“失败不识别”不足以证明编码失败。
- Vaidyanathan et al., NeurIPS 2026, `The Curse of Multiple Mediators`（https://arxiv.org/abs/2606.27510），whole-span activation patch 的效应可能含与其他中介的高阶交互。
- Brunello et al., BlackboxNLP 2025, `IPE: Isolating Path Effects`（https://aclanthology.org/2025.blackboxnlp-1.30/），提供路径特异性辨认的直接近邻；不能把 path patching 本身冒称创新。
- Mueller et al., ICML 2025, `MIB`（https://proceedings.mlr.press/v267/mueller25a.html），建议基于受控因果变量与电路比较的可证伪标准。
- Pandere et al., BlackboxNLP 2026, `Rewired or Gated? How Instruction Tuning Shapes Knowledge-Conflict Circuits`（https://aclanthology.org/2026.blackboxnlp-1.28/），研究已有特征是否被重新门控，与本项目 “encode vs use” 机制分辨存在实际科研竞争。

**结论：** CPU G0 已完成并发现一个有价值的“E 连续响应 vs C/A 离散联合修复 vs Q 不动”的诊断差异。它强化了为什么下一阶段不能继续只做普通 whole-span patching；**尚未**建立关系绑定电路、C→A 介导或唯一编码失效机制。本任务保留 V3 已通过论文的结论，作为深挖机制的独立后续工作线。
