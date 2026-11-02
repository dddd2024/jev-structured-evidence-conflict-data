# A462原生可信来源×规则Gold交集审计；A461双来源单调性命题约束

**研究日期**：2026-10-24（纽约当地）；**本轮没有执行新实验**。直接读取最新仓库主线A462候选/协议与此前真实运行的R0、R1、A427、A430、A451归档；对上游SecJev v2和三篇直接竞争论文阅读相关方法与结果。所有结论以机读同名JSON为证据索引，不改历史实验终态。

## 一、A462的原始2×2机制缺少同一个原生来源中同时成立的两个属性

预登记A462的变量是：相同Veto事实在**可信已认证的字段**与**攻击者可写低信任文本字段**中的位置×该事实出现/缺失，在相同来源/规则/候选上比较模型安全动作。该实验必须先有：
- 固定原生政策(P)并可独立重新推导每个2×2格子的动作Gold；
- 原始模型输入契约中**确有**区别于认证证据的低信任内容（仅字段看起来像文本不足以证明攻击者编辑权限）；
- 除事实和可信标记之外保持语义任务不变；至少两个独立来源族；
- 验证部署权限/攻击者写入路径后才允许把源内模型错误升级为真正攻击。

旧R0真实DEV语料`research/rounds/R0_20261020_NATIVE_SECURITY_TASK_QUALIFICATION/R0_REAL_20261020/R0_OFFICIAL_NATIVE_DEVELOPMENT_SOURCE_AUDIT_V1.json`，Git blob `1842eeadbf0b1447b426f55f4b211e3533f11982`，覆盖**8个原生来源、9911场景**。其state顶层字段与后续Gold重算相交：

| 原生来源 | DEV场景/组 | 已独立重算来源内可执行规则Gold | 显式 `untrusted_tool_response` 字段 | A462原生2×2共同条件 |
|---|---:|---|---|---|
| Twins/Streamlet | 797 / 42 | 是，规则certificate action | 无 | **未验证** |
| LANL auth | 328 / 7 | 是，规则triage | 无 | **未验证** |
| AgentDojo | 222 / 7 | **无独立部署许可/策略动作Gold**，仅工具文本分类 | 有 | **未验证** |
| InjecAgent | 124 / 2 | **无独立部署许可/策略动作Gold**，仅请求操作分类 | 有 | **未验证** |
| 其余四种分类来源 | 8440 / 各自source groups | 无对应已验证规则动作Gold | 无 | **未验证** |

按**上述两种经验证的原生能力**计算：`policy_gold_verified_sources={Twins,LANL}`；`explicit_untrusted_response_sources={AgentDojo,InjecAgent}`，**交集为空（0个家族）**。注意：“交集0”是**先前实际原始DEV审计所呈现的能力交集**，不能升级为“任何嵌套字段都不可能是低信任”“系统无法新建合法合同”或“全体研究语料不存在潜在权限字段”。它证明**A462现设计所需自然来源，当前没有被原始证据准入**。

A427真实LANL-v2显示**328/328**原生DEV可核对、7来源组、0来源内规则不一致，且`real_authorized_action_gold=false`。A430原始Twins DEV-v2 797/797行、42组、行动Gold类290/230/277已核验规则映射，但没有自然重复候选票、攻击者可写到达通道亦未验证。上述两源不是“安全授权Gold”的两个真实部署。A425旧元数据把AgentDojo `boundary_action`明确描述成`use_data/ignore_redirect`二选一**工具返回处理分类**，InjecAgent只是请求操作类型，不是已经执行的permit/deny动作。

更强的完整性限制：R1旧归档`research/rounds/R1_20261020_SOURCE_OWNER_ADAPTER_GATE/R1_G1_ORIGINAL_FOUR_SPLIT_TO_MODEL_BOUNDARY_V2.json`，Git blob `773fa2d5bd02025b5e630ad17b097e7eb41b2b0f`，报告`deployed_external_attacker_to_model_message_write=NOT_PROVEN`、`upstream_trace_to_corpus_mapper=UNVERIFIED_IN_PUBLISHED_SCANNED_PYTHON`；上游Twin投票数据类型的`verify`检查来源成员身份和**布尔签名有效值**，不构成独立密码学验签及现实认证来源的证明。因此A462描述的“已认证可信投票 versus 攻击者评论”不能被现有`received_messages`仿真修改所证明。

**决策**：不否定所有未来可信/低信任交叉实验的科研价值，但**A462-TCMI原生DEV门标记`HOLD_NO_NATIVE_TRUST_POLICY_INTERSECTION`**，不能因存在两个各有一部分能力的不同来源就将它们组合成一个同任务2×2。新增评论字段或把工具返回分类改成Twins政策决策，将形成新数据契约/数据分布，须重新做G−1与原生任务语义准入，不得称“原生自然反事实”或现实攻击。

## 二、A461仍有一个更窄而清晰的来源内策略单调性命题

在仍然不碰GPU情况下，旧原生独立规则Gold支持的是**语义受约束的单调谓词**，不是LANL和Twins动作菜单相同。

**Twins：** 令`C=存在同一轮次、决策时限内、身份有效的候选投票者发出的其他块冲突票`；`Q=有>=quorum个不同候选投票者`，Gold动作：

| C | Q | Gold动作 |
|---|---|---|
| 0 | 0 | wait |
| 0 | 1 | accept |
| 1 | 0 | reject_conflict |
| 1 | 1 | reject_conflict |

在`policy / validator_set / candidate_block / round / quorum / cutoff`保持不变、追加消息经过相同可观察资格规则的条件下：
1. 加入来自未投过其他块的新合规候选作者票可使Q从0→1，但不得使C从0→1；`wait→accept`可合法；
2. 在已有候选投票的同一作者名下加入有效的异块投票使C从0→1；Gold须变成`reject_conflict`（原本可能wait或accept）；
3. C为true时单纯增加其他合法候选投票不能撤销reject。这是**规则Oracle数学性质**，尚不是模型输出保持单调性的观测。

**LANL：** 设`R=(有效时间窗内至少5次历史失败)||(至少3个已知目标计算机)`；`F=(当前LogOn结果为Failure)`。Gold:

| R | F | Gold triage |
|---|---|---|
| 0 | 0 | continue_monitoring |
| 0 | 1 | record_failed_attempt |
| 1 | 0 | investigate |
| 1 | 1 | investigate |

在`history_window_seconds`、当前事件、较早summary边界与身份定义保持固定，且仅追加**可信、时间窗内的真实历史失败事件**时，R不能由true变false，已处于investigate不应回到非investigate。**不能把`continue_monitoring`、`record_failed_attempt`、`investigate`强行做成授权允许/拒绝的单一全序**；它们只是分类，`investigate`可定义为单调风险升级的Boolean投影。LANL旧v2对于`Fail→Failure`有明确标签映射，缺少该映射不能重用旧v1的negative错误。

两套真值表是**静态推理**，非已执行的自然成对样本、模型预测或可利用漏洞；源组统计也无法替代合法反事实所需的逐场景身份、窗口及持久状态验证。

## 三、避免再重复“模型已识别冲突，但不服从该识别”的不成立机制断言

旧`A451_M0_EXISTING_NATIVE_VETO_ACTION_RECOUNT/RESULT_MEMO.md`重核18条已消费DEV真实FP32旧输出、6组、1个Twins来源，得到**1条**Gold有冲突且模型`conflicting_vote`头预测正确、`certificate_action`却错误accept的源内候选，原记录`A428_011_SHAM_ACTIVE_MATCHED_TO_CANDIDATE_ID_WIDTH`，accept−reject margin `+0.524726391`。这一候选**没有被否认**，但不能称为“冲突识别中间状态被动作头忽略”的因果链，因为SecJev v2 §3.1明确每个问题独立causal row：`conflicting_vote`分支输出不直接传入`certificate_action`分支。若未来证明机制，只能在原生动作问题本身的Query/Key/LoRA表征内用**双向、同状态、同候选的控制干预**去识别，而不是凭两个独立问题的预测不一致推断信息流。

## 四、最新直接竞争研究：不要把来源认证、策略可见性和动作后果混成一条链

- **SecJev v2**，`https://arxiv.org/html/2610.03073v2`，本轮直接读§3.1/3.2/4.1及附录：typed独立问答行、训练和源标签任务已公布，常规source field敏感性不是新增架构。
- **Policy-Invisible Violations in LLM-Based Agents / PhantomPolicy**，`https://arxiv.org/abs/2604.12177`，原文引言与方法：政策相关真实世界状态缺失造成执行错误，和已验证的底层字段源/标签充分性不是同一个Gold对象。
- **CONTINUITY**，`https://arxiv.org/abs/2609.05269`，原文引言及形式合同：来源-字段-执行效果的签名/许可沿组件链传播已有形式化方法；“仅输入多一个trust标签即可得到真实授权机制”不是可信增量。
- **Authenticated Workflows**，`https://arxiv.org/abs/2602.10465`，原文方法主张：密码学来源认证、执行前许可检查与模型的概率分类互补，绝不能误称boolean模拟验签等于真实部署认证。

这些工作并**未证明原生SecJev指针头对可信策略证据的全部单调性**，所以A461的M-route仍可能有价值，但可发表增量必须是**严格独立Gold错误、有效合法配对、跨来源复现以及指针头Q/K或共享LoRA因果必要/充分**，非普通逻辑题不一致。按现行SOP，本轮论文主要段落直接核验不代替独立复审签发，仍然`HOLD_PRIOR_ART_INCOMPLETE`。

## 五、正式状态及资源

| 候选 | 基于本轮旧数据的建议状态 | 下一步 |
|---|---|---|
| **A461-PSMI** | **P1，CPU G−1未完成** | 首先确认原始合法规则对、同步Gold和来源组不交叠、严格候选/负对照，再决定是否准入GPU |
| **A462-TCMI** | **P2，HOLD_NO_NATIVE_TRUST_POLICY_INTERSECTION** | 没有可信+低信任原生字段共同存在且独立规则Gold的证明前不开展2×2 |
| **A453-OSST** | **P2，TRAIN O/L分层HOLD** | 不重训；必须先证明同任务同组高低可观测支持与标签真实性 |
| A460 | P3，常规锚定/顺序偏差已有近似先例 | 方法对照或排除 |

A461当前登记的正式实验名是`A461_20261025_POLICY_SEMANTIC_MONOTONICITY_CPU_G_MINUS_1`，A462是`A462_TRUST_CONDITIONED_MONOTONICITY_CPU_G_MINUS_1`，**两者均`DESIGNED_NOT_EXECUTED`，没有新GPU许可**。本轮自身只是对旧结果的CPU逻辑/证据交集分析，需通过最新实验前独立文献G−1才能在服务器上开新语料G0。

**新资源实耗**：仓库GitHub读+算+写，学校服务器访问0、原始TRAIN/DEV/CAL/TEST行读取0、模型前向0、GPU0、重训练0；没有双端服务器和GPT Library备份验证。新增的JSON与Markdown另保留GitHub读回SHA及收据。
