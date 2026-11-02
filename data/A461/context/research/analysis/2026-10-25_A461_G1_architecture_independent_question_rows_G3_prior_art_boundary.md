# A461 G1架构性勘误与G3先例预审：跨问题预测一致性≠内部因果串行决策

**日期**：2026-10-25。性质：原始SecJev论文定义核对+实际G1 103条logits复核后的科学解释边界；**不是正式G3 G−1放行、不是新增模型实验**。

## 1. 必须纠正的“多头”因果叙述

SecJev原始模型论文《SecJev: Bringing Security Expertise to System One Decision Models》（Chen等，arXiv:2610.03073v2，https://arxiv.org/html/2610.03073v2 ）§3.1–3.2明确：每个问题`q`和候选描述`C`都单独与同一个state进行因果输入行渲染，并用**共享**backbone/LoRA及pointer scorer计算每个候选的得分，`z_k=((W_Q h_d+b_Q)^T(W_K h_k+b_K))/sqrt(d_p)`。不同问题行不直接共享问题token；没有被证明存在先计算`conflicting_vote`答案、再把该答案送给`quorum`、最后送入`certificate_action`的显式级联电路。

因此，G1实测T2全部6个请求的跨问题模式`pred_C=false`、`pred_Q=Gold_Q`、`pred_A=f(pred_C,pred_Q)`，**不能成为“C输出因果导致A错误”或“动作阈值层没有问题”的直接证明**。只能陈述：同一结构化state在两个独立问题行上，冲突识别与策略动作均未反映合法新增冲突，且可观察输出在逻辑上相容。

同样，T1 run121的`pred_C=false,pred_Q=true,pred_A=wait`对照来源Gold`accept`，是**跨问题答案的逻辑不自洽**，不是已定位的“动作整合头”故障；不同问题自带不同`q,C`，不能用它们的预测结果做可见的隐藏状态因果流程图。

## 2. 前人工作的直接竞争

- **Tang等，ICML 2026**，*Do Language Models Track Entities Across State Changes?*，https://proceedings.mlr.press/v306/tang26ah.html ：已有研究针对状态改变中的实体跟踪研究内部机制，发现模型可能并不按token增量维护世界状态，而是对查询相关信息做并行聚合。因而**“LLM不善于增量合并状态”不是尚无先例的新主张**。它并未自动说明SecJev的原生投票证据冲突识别根因相同。
- **Zhang & Nanda，ICLR 2024**，*Towards Best Practices of Activation Patching in Language Models: Metrics and Methods*，https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html ：patching结果对评估指标和corruption方案敏感，不能把某层修复动作当成已证明电路定位。
- **Makelov等，ICLR 2024**，*Is This the Subspace You Are Looking for? An Interpretability Illusion for Subspace Activation Patching*，https://proceedings.iclr.cc/paper_files/paper/2024/hash/70b8505ac79e3e131756f793cd80eb8d-Abstract-Conference.html ：即使低维patch有端到端正向效果，也可能激活与原路径因果断开的旁路，须设计必要性/充分性、反向撤销和未改动事实保持等交叉验证。

本次只核对上述4篇原始论文/官方会议摘要的直接方法边界，**不构成按照SOP完整冻结的G−1 novelty decision**。正式A461下一白盒协议必须复核A464 2080篇汇总中有关状态更新、事件多关系绑定、原生typed head问题条件和安全证据读取的近邻先例，并记录为什么本研究提供不同的安全含义、因果证据与独立来源复现。

## 3. 下一轮机制筛选的正确计算对象

候选拟名`A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE`，**DRAFT_NOT_ADMITTED_NOT_EXECUTED**；不是现有G1的补跑。主假设是：在相同任务的**冲突判断问题行**中，合法追加`author/round/block`异块关系后，模型如何在共享主干与原生Pointer Score之间整合这一跨消息关系。固定问题说明、候选选项、原始source policy，先CPU研究同一state可以形成的冲突证据位置/顺序和身份可写性及其Gold；区分真正冲突与语义等价的SHAM、token个数、字段次序。优先使用**T3中模型正确识别旧冲突**的合法样本作为候选正向donor，**T2新增冲突模型预测false**作为负向target，但这些旧状态并不相同，必须严查语义污染和donor资格。

**若以后另行获准GPU干预**：首先在**同一原生问题行**内比较old/new及donor/target的`C=true`signed logit margin；再考察shared backbone的hidden state、候选末尾hidden与decision marker隐藏态、独立的`W_Q/W_K`投影。反事实双向patch的必要性、充分性与source policy Gold必须逐项冻结；不要直接把`conflicting_vote`问句得到的hidden tensor移给`certificate_action`问句就宣称发生内部介导（问题token和候选语义并不相同）。

**停止条件**：缺少来源有效的相同状态/可比较donor条件、Gold歧义、无法同时保留合法事实与对照、严格行为阳性在独立source run组不可复现，均不得进入白盒因果强主张。新预算单独申请，不自动复用已花完的103次。

## 4. 研究现状

GitHub `ca9eb88`已真实上传完整G1 103条FP32原生logits及修正收据，原始G2 action-only统计31组。我方独立多头分析位于 `research/analysis/2026-10-25_A461_REAL_G1_103_multihead_conflict_recognition_root_cause_screen.{md,json}`，发现T2冲突识别问题6/6错误、动作6/6错误、源内法定人数6/6正确；LANL-L1 burst仅3/9、triage仅4/9；T1 run121出现单条跨问题不一致；N1B14条中旧正确到中性错误2/12。**这些已是模型行为的真实实验结果，不是已证实的白盒因果机制或部署漏洞**。

本勘误已通过GitHub Issue #2通知执行方；本轮新GPU0、训练0、服务器访问0、原始TEST/CAL读取0。
