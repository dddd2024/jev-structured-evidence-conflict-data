# G−1 先行文献排重与新颖性决策：A461-PSMI（策略语义单调性）

**审查时间**：2026-10-25T03:58:12Z（UTC）
**审查仓库 SHA**：`0b985db4f4ba99a7b06bdcd5497428419860f59e`（origin/main，本文件提交前最后一次核验）
**实验登记名**：`A461_20261025_POLICY_SEMANTIC_MONOTONICITY_CPU_G_MINUS_1`
**决策**：`NOVELTY_DELTA_TESTABLE` —— 仅放行 CPU 准入门；**不含任何 GPU 许可**。

本文件是按 `research_governance/PRE_EXPERIMENT_DIRECT_PRIOR_ART_GATE_V1_20261024.md` 第 5 条要求、在冻结任何 A461-PSMI 协议之前提交的先行文献决策。A461/A462 两轮的文献台账对本实验处于 `HOLD_PRIOR_ART_INCOMPLETE`；本报告完成其要求的靶向检索与最强 3 篇以上正文直接核验，并给出增量决策。它**不**改写 A461/A462 轮的任何历史结论。

## 1. 一句可证伪假设

> 在 SecJev-0.8B 原生 typed 策略决策上（Twins `certificate_action` 的 C/Q 真值表；LANL `triage` 的 R/F 真值表，Gold 均可由源内可执行规则独立重算），存在**规则保持的证据追加反事实对**——在同一冻结 scene 内追加通过同一可观察资格规则（Twins：`kind=vote ∧ round=candidate_round ∧ received≤decision_time ∧ author∈validator_set`；LANL：同窗、`seconds_before_current` 不与现有事件撞秒、目的地为场景内已知计算机）的新事件，且策略文本、身份集合与选项菜单不变——使得模型严格策略动作向**策略非单调方向**移动（如追加有效 quorum 票反而提高 reject 相关 margin；追加冲突证据反而提高 accept margin；追加可信窗内失败反而降级 triage），且该现象**超过等长中性事件负对照**。

## 2. 最强直接竞争文献（≥3 篇，本轮实际阅读范围）

| # | 论文 | 本轮阅读深度 | 已解决 | 未覆盖 | 我们的可测增量 |
|---|---|---|---|---|---|
| 1 | [SecJev v2](https://arxiv.org/html/2610.03073v2)（v2, 2026-10-14） | §3.1–3.2、§4.1 由 A461/A462 轮直接读原文并与本仓库 pinned 组件哈希比对 | 定义了本研究对象：typed 独立 causal 问题行、共享 Q/K 指针评分头、Twins/LANL 原生源；本文冻结的任务 schema 即出自它 | 未陈述、未测量、未保证评分器对策略证据追加的任何单调性；无规则保持反事实对 | 首次用 oracle 重算双臂 Gold 检验其策略语义是否单调 |
| 2 | [One Word Opens the Gate](https://arxiv.org/abs/2610.12292)（v1, 2026-10-08） | 本轮直接读 arXiv 摘要页；A461 轮经公开研究摘要做过章节级阅读（HTML 原文不可达已如实记录） | typed 决策模型作为护栏的 fail-open/fail-closed 不对称；**攻击者注入** 6 行无关日志使 fail-open 0%→63%；选项改名攻击 93–100% | 诚实系统自身追加**策略相关**证据；可执行 oracle 判定 Gold 是否合法改变；原生结构化 scene；单调方向分析；白盒读出 | "无关文本能翻转决策"≠"策略相关证据追加违反单调性"；后者是我们的命题 |
| 3 | [Monotonicity as an Architectural Bias](https://arxiv.org/html/2602.02686v1)（v1, 2026-02） | **本轮直接读方法与结果**（T5-small、单调 FFN、HotFlip 19% vs 63%、ROUGE-L −3.2%） | 提出语义单调 FFN 约束并测对抗鲁棒性 | 无证据追加导致的决策翻转基准；无安全/授权任务；无 typed/指针头；无反事实对与 oracle Gold；从未测量未修改生产评分器是否违反单调性 | 提供其概念前提缺失的**测量侧**：真实安全型评分器上的 oracle 验证单调性违例检验 |
| 4 | [Metamorphic Testing 安全评估](https://doi.org/10.1007/s11390-026-5705-z)（JCST 2026） | 出版方摘要/方法概述（A461 轮） | 七类变异关系，确立 MT 方法论 | 无可执行安全策略 oracle；无单调证据追加关系；无双独立 Gold 实现 | 每族实例化**一条**精确单调变异关系 + 确定性双 oracle |
| 5 | [Giving an LLM More Correct Evidence Made Its Decisions Worse](https://www.greaterwrong.com/posts/wgiEb3PooeA2EN4Ge/giving-an-llm-more-correct-evidence-made-its-decisions-worse)（未发表，2026-09） | **本轮直接通读** | Qwen3.6-27B 逆反博弈：加 4 条正确示范使动作准确率 79%→55%，报告仍 99% | 单一通用对话模型、游戏任务、无安全策略、无可执行 oracle、未发表、作者明示无机制结论 | 将证据追加一致性问题推广到安全策略语义 + 双源族 + 预注册负对照 |

相邻但非直接竞争（已在历史轮读过相应部分，逐条列出防止漏判）：[2609.39768](https://arxiv.org/abs/2609.39768)（NN 单调性验证复杂性）、[2604.12177 PhantomPolicy](https://arxiv.org/abs/2604.12177)、[2609.05269 CONTINUITY](https://arxiv.org/abs/2609.05269)、[2602.10465 Authenticated Workflows](https://arxiv.org/abs/2602.10465)、2610.19619（数值锚定，A460-PEPS 先例）、[2608.03506](https://arxiv.org/abs/2608.03506)、UAI 2026 counting-to-n、ICLR 2026 Mixing Mechanisms、ACL 2026 Cell-Based Binding。

## 3. 逐条 Novelty Delta 与重复反证

- **对 2610.12292**：它证明的是*攻击者可控的无关文本*翻转 typed 护栏决策。若我们的违例对与**等长中性事件**对照的违例率不可区分，则现象坍缩为其发现在另一模型的复现 → 行为层主张 `REJECT_REDUNDANT`。
- **对 2602.02686**：其单调性是*架构修改手段*，从未评估真实评分器的证据追加行为。我们不重复其架构工作；若有人把本轮表述成"提出单调架构"，即超出本轮范围。
- **对 SecJev v2**：其已发布任务面与架构是本实验的输入。若 SecJev 后续版本已报告证据追加单调性违例，本轮即为重复。
- **对 JCST MT**：若其七类关系已含"证据追加单调关系 + oracle Gold + 结构化安全决策"，方法层增量失效。
- **对 LessWrong 帖**：其在通用模型上的独立证实**不构成**我们命题的满足（无 oracle、无安全终点、单模型、未发表）。

## 4. 竞争解释（≥2，将进入协议负对照）

1. **通用序列化/长度/位置敏感性**（2610.12292 与 2610.19619 锚定先例）：追加事件改变问题 token 位置与长度。→ 负对照：与追加证据 token 数相同的**中性事件**（Gold 不变），其违例率必须严格更低；另加非安全序列化翻转对照。
2. **阈值附近计数容量限制**（counting-to-n）：违例集中于边界=容量伪影。→ 按距阈值距离分层，并与同层自然 scene 准确率比较；纯容量故事预测对称错误，而非越过层基线的方向性非单调。
3. **非确定性/精度伪影**：G1 前必须重放冻结 baseline 并与归档 logits 比对（A430 G1 先例：最大绝对误差 0.0）。
4. **分词边界伪影**（A430 G0C 已记录的数字前缀共享现象）：资格规则在解码后 scene 上检查，记录首差异 token 下标。

## 5. 来源与 Gold 状态

- **Twins**：C/Q 真值表 oracle 已在 A430 双路径验证（G0A 独立 verifier + 主实现）。
- **LANL**：A427 v2 的 328/328 行独立重导出、0 分歧、7 个日组；反事实编辑后的 Gold 必须在 CPU 门内由**两套独立实现**重算一致后才冻结。
- **来源边界**：仅 DEV（Twins 797 行 DEV v2 池；LANL pinned `development.jsonl.gz`，SHA `2920e1c9…`）；CAL/TEST 协议禁止。终点标注为**模型策略一致性**，不作真实部署授权声明。

## 6. 已有重复样本来源（防止把旧数据当新证据）

A428 24 个 DEV scene（12 Twins + 12 LANL）与 A430 G1 6 worlds × 3 arms 的 FP32 原生输出仅作**重放参照**；PSMI 对来自 DEV scene，未来 GPU 阶段双臂全部新跑，不消费任何 CAL/TEST 行。

## 7. 决策与权限

`NOVELTY_DELTA_TESTABLE`：进入 CPU 准入门设计（反事实对构造规则、双 oracle、负对照、停止条件 `STOP_NO_RULE_PRESERVING_PAIR` / `STOP_FEWER_THAN_TWO_INDEPENDENT_FAMILIES` 等）。**GPU 未获任何许可**；任何模型前向需按 A430 G1 先例单独申请用户明确批准并记录预算。

**本决策的证伪条件**：(a) 无规则保持对存活 → STOP；(b) 中性对照与策略相关编辑违例率不可区分 → 格式效应坍缩；(c) 仅单族出现且不能在第二族独立组内复现 → 单族伪影。
