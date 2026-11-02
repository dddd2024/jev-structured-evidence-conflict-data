# A461-G5-G2 论文证据包 V2｜独立整稿科学审计

日期：2026-10-27
审计对象：PAPER_CLAIM_PACKAGE_V2，研究成果冻结提交 a17c18900ca8ab21a3603dd3c26653a11326d1f0；完成声明及最终独立审计触发提交 307367a80a7798690d2af4c6316f073b50d06e3d。
**裁决：PAPER_AUDIT_REVISE_REQUIRED（P0×1 / P1×3）**。
工作范围：零新增模型前向／零 GPU；从 GitHub 原始 FP32 logits、预注册设计、真实执行回执、Release API、论文生成源码及原始学术论文独立交叉核查。不是对原有实验的否决，也不是论文级 PASS。

## 1. 独立确认的实验事实

- SecJev-0.8B：Stage-A～F 已归档。Stage-E 在第 11 层 all-row 的 same-forward C∩R 联合修复 8/32、SA-sham 和 dose 为 0；但 run-140 单供体占 7/8。Stage-F：未被识别的新增冲突片段 0/48；H-F2 预注册成功，H-F1 与 H-F3 均未达标。
- kev-4B：同样 124 个冻结场景上的严格识别 44/124，供体 14 组；SecJev 为 4/124、3组。模型的规模与训练均不同，不能把差别直接归因于模型大小。K-B 冻结层选择准则选择 L*=11，K-C 使用不同的 donor/host 场景做复制。
- 从 K-C 原始 Git blob 19d3a06c27953b1f2b4dcd2770394d28741a69fd 独立解析 417 行，按实际 run 为 128/128/128/33。完整 native four-question rows 417/417；main、SA-sham、dose 各 112 行，unrecognized 40 行。14 donor × 8 host = 112 个成对组合，每臂排除 8 个同来源组配对，得到 **104 个跨组有效组合**。
- 独立用 logits 的 argmax 计算 JOINT（conflicting_vote=true 且 certificate_action=reject_conflict）：主臂跨组特异联合修复 **53/104**，SA-sham **0/104**，dose **0/104**；主臂 dM > dose **95/104 = 91.35%**，主臂 dM > sham **104/104**；联合修复覆盖 14/14 donor run 组，最大组 7/53=13.2%，7/8 host 场景至少有一次修复。重算吻合冻结 K-C analysis（Git blob 2159ea39a4b9ac2c8e5123a5d472df1cac1ed093）。本独立核对没有把 104 个 crossed cells 当作 104 个统计独立样本。
- kev-4B K-C execution receipt Git blob be6c8ed6a5737ebd4f37cd9113cd50d0a6de34b9：COMPLETE，真实前向 417，持久 raw 行 417，1 次模型加载，0 denied。K-B execution receipt Git blob 928ab6705c412e7ce486b668a64b6c2e87512f73：346/346，批次 128/128/90，0 denied。九阶段 G2 前向总数 3,628（SecJev 2,487；kev-4B 1,141），与材料汇总一致。
- GitHub Release API 直接核实 a461-g2-captures-stage-c-v1 与 a461-g2-captures-def-k4b-v1 两个标签下 6 个 tar 资产确实存在、state=uploaded；每个 size 和 GitHub SHA256 digest 与 CAPTURES_SHA256SUMS 一致；总计归档描述 371 个张量。

**科研判断：** 以上证据真实改善 V1 的跨组供体集中问题。v8 主标题、摘要与正文多处已恰当地把主张收窄为“受控 whole-span 激活移植的条件性因果充分性”，不再宣称排他性定位编码失败、不宣称 C→A 自然中介或跨架构普适安全电路。**但目前文本仍出现以下会影响完整论文结论与一致性的错误。**

## 2. P0×1：把条件性供体类别对比错误解释为“recognition 而非 content 决定修复”

精确位置：
- PAPER_CLAIM_PACKAGE_V2/generate_v8.js 中 §4.10 标题为 “Semantic controls: recognition, not content or decision class, carries the repair”。
- PAPER_CLAIM_PACKAGE_V2/NOVELTY.md 的 Novelty delta 第 2 项写 “Recognition, not content or class, decides repair”。
- v8 Introduction 贡献列表也称 semantic negative controls separate recognition from content and decision class。

为何不能通过：
1. Stage-F 预注册 H-F1（TTT new 与 TTT SA）实际 0/72 vs 0/72，原实验说明明确认定该对比 **NOT MET / UNINFORMATIVE**；因而它不能识别是 recognition 还是 content 决定迁移。
2. TTT-new 来源场景本身识别了冲突，但其移植联合修复仍是 0/72；所以来源输出“已识别冲突”这个单一属性不足以保证修复。FTF 严格供体与 TTT 新状态之间同时存在冲突来源、上下文、输入关系等差异。
3. FFF-new 0/48 与 K-C unrecognized 0/40 对严格 donor 状态的比较，**没有只操控 recognition 一个变量**；结果支持“被测试来源类别的条件性差异”，不是关于内部 recognition 的单因素必要性/充分性证明。
4. Novelty delta 同时在第 1 项声称 content-specific sufficiency、第 2 项声称 not content，语义自相矛盾。完整 hidden span 的特异性因果作用不能自动归为特定见证关系、仅由模型识别标记决定，或者排除所有 content confound。

**处置：** 集中替换 §4.10 标题、Intro/Novelty 第 2 条及对应讨论为更窄的事实：“在测试的 donor 类别中，严格识别的追加冲突供体片段可以在部分 near-threshold hosts 引发特异性 C∩R 修复；未识别追加冲突与已识别的 pre-existing-conflict/duplicate 来源没有复现该效应。识别、来源内容、上下文和宿主交互尚不能独立分离。”保留 H-F1/H-F3 失败及 class-matched 对比的 exploratory 属性。**不要求为这个文字范围修正再做 GPU。**

## 3. P1×3

**P1-1：v8 仍有过时的单模型文字和未经证明的原因归因。**
- generate_v8.js §5 Bounds 仍有 “The causal statements are about one 0.8B checkpoint”，以及 “we make no ... cross-model claim”；§6 Limitations 仍以 “One 0.8B checkpoint” 开头。它们与本稿明确的两个 kev-family scorer 实验矛盾。
- §5 还将 donor 集中度在两模型中的差异直接归因于 SecJev specialist 的“rare recognitions”，没有隔离模型规模、训练目标、权重/模型架构、阈值及 donor 构造变化的影响。
- 处置：全文一致写为 “two kev-family checkpoints, one simulation family”；把“产生差异的原因已确定”降为“observed discrepancy, cause not isolated”。

**P1-2：论文贡献与直接先例的差异仍需强化，避免把标准 patching 当成新方法。**
- Abdelsalam et al., 2026, A Mechanistic Lens on Semantic Conflicts, 在四个公开模型上进行 token-aligned 语义冲突的 residual-stream patching（https://arxiv.org/abs/2607.05587）。
- Chu, Sun & Weng, Findings EMNLP 2026, From Detection to Refusal, 已在六模型上进行安全检测/拒绝的因果干预（https://aclanthology.org/2026.findings-emnlp.1629/）。
- Vaidyanathan et al., 2026, The Curse of Multiple Mediators, 解释 activation patching 的 NIE 与其他介体交互不可完全区分（https://arxiv.org/abs/2606.27510）。
- V2 已明确引用并承认前人贡献，这是 PASS 的部分进展；**还应以一个清晰的比较表**交代自身不同处：policy-relevant appended evidence、可执行独立 Gold、typed action、逐位置 dose 控制、same-forward 联合读出，以及同一个模拟器家族的范围限制。两个 kev 模型不是一个新安全电路方法，也不能直接证明跨架构一般性。

**P1-3：replication 的独立性必须准确披露。**
- K-B 层选择与 K-C 复现使用不重合的具体场景，但它们不是互不重叠的 donor 来源组：K-C 14组包含 K-B 已出现的六组。不能称“held-out source groups”，只能称“disjoint scenes”；都来自 twins_streamlet DEV 一个构造模拟器家族。
- 14 donors 共享 8 个近阈值 hosts；53/104 是在配对集合中的效果计数，不是 104 IID 的独立安全任务成功率，不是部署防御增益，也没有独立的通用模型系列验证。论文 limitations 已承认大多数限制，确保所有贡献、标题、摘要和对外报告一致。

## 4. 独立核验边界

核验了 K-C 冻结设计与跨组身份、417 条 native logits、四问题 joint、三臂一一配对、跨组样本排除、两个 K-B/K-C GPU receipts、公开 GitHub Release API 的资产摘要、全文生成源码与 Novelty/Limitations/README、公开原始论文。
**没有**在本次独立审计中实际下载私有 tar/解压 .pt、重跑九套分析脚本、重做所有历史 Gold 检验，亦未读取非 UTF8 的最终 PDF/DOCX 二进制页面。作者对这些项目提交了 REANALYSIS_CHECK 和可用依赖/脚本，外部审计不应把作者自检冒称本次独立重算。此处是核验范围说明，而非否定其已归档回执。

## 5. 集中修订与研究路线结论

**裁决：PAPER_AUDIT_REVISE_REQUIRED（P0×1 / P1×3）；无需重跑 GPU。** 现有证据足以支持“在两个 kev-family typed scorer 中，严格识别追加冲突的自然 whole-span 隐状态在特定层能条件性修复部分 near-threshold 场景的原生冲突判断与安全动作，而且超越指定对照，跨多个 source groups 复现”这项**限定范围的因果干预发现**。

先解决 §4.10/Novelty 的 recognition-versus-content 逻辑过度、清理 §5/§6 旧稿残留并更新紧邻已有工作的贡献比较；论文科学机制“encoding failure”的唯一定位仍然**没有**被证明，但 v8 把它界定为首选候选解释是恰当的。现有 SecJev H3 L11 AUC=0.844<0.9、Stage-F H-F1/H-F3 失败、Stage-D 设计勘误和同模型家族限制必须永久保留。

本轮审计不要求为每个修订点重启 L0/L2/L3。研究 Agent 根据集中清单自行修稿/测试。现已完成的 kev-4B 复制研究是实质新证据，因此此前“先停止跨模型，等单模型机制完全确定”的建议已过时；但也没有理由在完成上面必要的主张修订之前扩大 GPU 实验。

一手定位：
- 论文 V2 包：research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/PAPER_CLAIM_PACKAGE_V2/
- K-C 真实结果：GitHub commit 5ef7a16d517e01cebeca287a8160bd7ed2aca085
- K-B 与 K-C 冻结方案：GitHub commits 66fa2926f8350d3d3e899f1f20f29e5189b3ac4a、3a6173f92e8066d2be8ae170e75f6fa94f4caa1f
- 本轮触发：GitHub commit 307367a80a7798690d2af4c6316f073b50d06e3d
