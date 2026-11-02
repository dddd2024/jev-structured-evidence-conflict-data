# A461｜GPU科研实验准入核算与Gold术语澄清

**本轮日期（America/New_York）：2026-10-24；本轮类型：只读科研准入审查及既有结果解释。** 不等于新CPU G0、不等于GPU授权、不等于模型推理；本报告依据统一SOP、强制G−1新规范、A461候选协议与历史真实Gold/模型结果。基准 main：`0b985db4f4ba99a7b06bdcd5497428419860f59e`。本轮另存同名机器可读JSON。

## Gold是什么？

Gold = **ground truth / gold standard**，也就是模型预测所对照的**独立参考答案**。其可信性取决于生成机制，不能把Gold这个名称视为“客观绝无错误”。

- **来源/人工标注Gold**：原数据集给出的类标签；可能与可见证据脱节或有错。
- **独立规则Oracle Gold**：在固定政策(P)下，从合法原始state独立运行确定性的Oracle函数`g_P(state)`生成的源内策略答案；应该和语料给定标签独立比对并处理时序、缺失和歧义。
- **真实部署授权Gold**：包含用户实际权限、工具参数、动作来源与实际后果的“允许/拒绝”授权答案。当前SecJev Twins/LANL缺少这样的完整部署权限证据，**不能用来源内策略Gold代替**。

Twins示例：合资格的同一作者存在异块冲突票，Gold动作`reject_conflict`，模型却回答`accept`，这是来源内动作错误；不证明真实交易已被错误批准。LANL示例：当前不足阈值的4个有效先前失败事件与两个以下有效失败目标，在合法增加同时间窗第5个事件（保持目标集合）后，Gold依策略从非investigate转为`investigate`。这是**尚待构造和双Oracle验证的反事实**，不是已经运行过的实验对。

原始LANL V2有328/328来源内Gold与语料标签一致；Twins DEV包含797场景和42组、LANL DEV328场景7组。旧A427 v1处理原始`Fail`和规则词面`Failure`不匹配导致143/328 invalid，v2显式修复语义映射。这证明即使写成“规则真值”，也必须先核对词表、时间窗与原始证据，而不能直接把模型/语料标签作为真值。

## GPU为什么尚未获准入？

请以已经提交的规范`server_runner/EXPERIMENT_OPERATIONS_STANDARD_V1.md`和`research_governance/PRE_EXPERIMENT_DIRECT_PRIOR_ART_GATE_V1_20261024.md`为准，而不是历史口头预算。

| 顺序 | 需通过的门 | 已有证据 | 现阶段缺失与裁决 |
|---|---|---|---|
| 1 G−1 | 本轮直读至少最强3项（可得时）直接竞争研究：原模型、同任务同机制、安全终点；逐条已知/新增/替代解释/否定实验；正式`NOVELTY_DELTA_TESTABLE` | A461/A462存原始论文摘要与部分章节的综述 | **`HOLD_PRIOR_ART_INCOMPLETE`**；不存在规范路径下A461独立前置Go文档。不得事后将既有协议追认成事先G−1通过 |
| 2 G0规则Gold | >=2独立来源家族，各自真正可执行源内规则、不可将不同策略标签混为同一端点；新反事实两臂独立Gold及源码版本 | Twins与LANL原生来源内Oracle初步够2家族；原始记录Gold已复核 | 新状态Gold+编辑合法性**0对** |
| 3 G0场景与对照 | 原始TRAIN/DEV合法输入；场景中政策、时序、身份、候选/动作菜单、意图与非目标字段固定；source-group统计；中性SHAM及无关格式控制 | 从历史LANL派生记录筛出31个失败阈值起点/3日组、22个目标数量起点/2日组 | 是53个必要条件起点**而非53个完整实验对**；独立Gold、token等价、真实时序均未过 |
| 4 G0技术和预归档 | 冻结backbone/LoRA/QK head/tokenizer/calibration/precision和原生输入、token ID、代码/环境SHA256、预算和停止条件；先GitHub存档回读 | 旧模型固件有版本冻结工件 | A461实验自己的成对输入和代码尚未冻结/回读 |
| 5 显式GPU执行许可 | 共享3090可用；确切物理前向上限、显存/时长、输出和所有cache只在`~/wjc`；用户提醒并有本次批准回执 | A461条件性草案写128原生前向、64 Hook前向上限 | `approved_gpu_hours=0`，**没有许可**，不得自动加载模型 |

经过上述步骤，最多可以为**受预算约束的原生GPU行为pilot**申请许可；行为pilot确证严格源内Gold错误、有匹配干净对照、来源组阳性和独立复算后，**另行批准**白盒Query/Key、LoRA/hidden state的双向Hook因果实验。仅有Logit margin单调方向错误、单点源内分类失误、或假Gold，不准替代确认性阳性。

**命名陷阱**：冻结A461协议中的`future_gpu_if_admitted.stage_g0_max_native_forwards=128`属于“未来若GPU获准”的内部草案字段，**不是统一SOP中的CPU-G0阶段获得128次GPU许可**；`stage_g1_max_hook_forwards=64`也是条件预算。建议后继**新版本**用`G1_NATIVE_PILOT_MAX_FORWARDS`与`G2_MECHANISM_HOOK_MAX_FORWARDS`避歧义。原协议不能静默覆盖。

**文献前置硬门的实际存档问题**：仓库`research/literature_preflight/`目前9个目录中不包括A461。同一方向虽然已有`research/literature/A461_20261025/A461_experiment_protocol.json`，但不能依靠以后补一个带过去时间戳的文件宣称那份旧协议G−1 PASS。应将旧协议保持历史候选，并在本轮新的G−1合法通过后，先提交前置决策文件，再正式冻结**新版本实验**的协议/脚本。

## 截至本轮的真实状态和当前下一步

**当前命名仍是`A461_20261025_POLICY_SEMANTIC_MONOTONICITY_CPU_G_MINUS_1`（候选设计，`DESIGNED_NOT_EXECUTED`），GPU 0。** 下一步先结束G−1直接论文竞争审查和签发，若`NOVELTY_DELTA_TESTABLE`则进入CPU-G0，使用上述已归档起点逐一从真实原始DEV构造合规单事件配对、冻结独立Gold、SHAM、来源组预算与hash，独立复核并归档。A462因缺少同一原生家族的可信/低信任字段和规则Gold交集而暂缓，A453的TRAIN高低可观测分层仍HOLD。没有必要把重复统计权重或新增方向ID当科研推进。

**资源/归档边界：** 本轮只有既存GitHub证据与研究SOP读取、机读状态审计和当前GitHub写入；无服务器SSH、无新增原始语料行读、无新GPU/模型前向/训练，尚无服务器/GPT Library双端SHA验证。
