# A461-G5-G2 | 独立完整论文级科研审计 V1

**日期**：2026-10-27  
**裁决**：`PAPER_AUDIT_REVISE_REQUIRED` — **P0 × 2 / P1 × 4 / P2 × 2**  
**结论边界**：Stage A–E 的真实实验阳性效应成立于冻结分析的条件与口径下；然而主稿 v6 的中心断言“追加冲突的失败已经被因果识别为 *encoding failure at the appended span*, 不是 readout/timing/interaction 失败”**尚未充分辨认**；“两个读出共同恢复”泛化亦不足。**不能授予 `PAPER_AUDIT_PASS`，但现有原始数据不因该裁决失效。** 没有执行新的 GPU 或修改历史 Gold。

## 0. 触发条件和精确审计对象

唯一触发：研究 AI 在 `PAPER_CLAIM_PACKAGE_V1/README.md` 明确发布完整创新成果的论文级声明，并标记 `UNVERIFIED_PAPER_READY_CLAIM`（提交 `e5de4b764b1776d288dfc87642ff19910998565d`）。用户明确要求本次“审计”。适用上位政策 `research_governance/2026-10-27_JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2.md`。

审计主工件：
- `PAPER_CLAIM_PACKAGE_V1/{README.md,CLAIMS_EVIDENCE_MAP.md,NOVELTY.md,LIMITATIONS_AND_ERRATA.md,REANALYSIS_CHECK.md,REPRODUCE.md,numbers_v6.json,extract_numbers_v6.py,assemble_v6.py,generate_v6.js,generate_v5_input.js,SHA256SUMS}`
- Stage-A–E GPU 原始 `raw_native_logits_stage_*.jsonl`、执行回执及预注册分析 JSON；Stage-D 独立动作行不可达勘误。
- A517 文献研究索引、原有 v5.2 denominator narrow PASS、公开直接相关论文官方页面。

**审计深度披露**：通过已连接 GitHub 私有仓库逐文件读取 UTF-8 原始数据和完整手稿生成源码 `generate_v6.js`，核对核心实验与文本对应。连接器会因非 UTF-8 拒绝二进制 `.pdf`/`.docx`，因此**没有检查渲染版的分页、表格视觉和 PDF 字节一致性**；也无法直接读取留在实验服务器的 Stage-C–E 全量二进制激活 capture tensors。它们的回执、冻结清单与 SHA256 文件可见，但**不能把来源作者“重算一致”视为本次独立字节重算**。这属于审计范围限制，不应隐瞒。

## 1. 确认可保留的科研结果（PASS 事实；不是整篇论文 PASS）

1. **五阶段真实执行**：直接读取五个原始 JSONL，行数分别 A **378**（批 128/128/122）、B **464**（4×116）、C **696**（124/124/112/112/112/112）、D **349**（71/70/112/96）、E **304**（88/72/72/72），合计 **2,191**。阶段运行回执、`numbers_v6.json`、配套 Git blob 指向一致。阶段 A 的原始结构与后续不完全相同，不能用后续字段 `M` 的存在作为其有效性门槛；本次只做其行数与批次交叉核验。
2. **Stage-A**：严格合格供体 **4/124**，位于 **3 个** `twins_streamlet:run` 组；Stage-D 剩余 **47** 个候选新增 0 供体，171 个冻结可构造场景已筛选。该数量是选择性构造的 DEV 母体结果，非全模型/部署错误率。
3. **Stage-B**：L11 restoration 只有 **9/16** 达预定义特异性判断，suppression 对 SA-sham 不特异（7/16 主要干预更强）；一向的阳性不允许写成双向闭合机制。
4. **Stage-C**：L11 主要恢复干预优于两组逐位置扰动幅度匹配的随机方向对照 **16/16**；但 H3 预注册 L11 AUC **0.8441 < 0.9**，预测不成立。L11→L13 的 patch 效应衰减是已观察结果。
5. **Stage-D**：L11 `conflicting_vote` 类别特异性翻转 **10/32**；Stage-D 补丁只触及 C 行，动作行不可能变化；已版本化勘误必须持续保留。
6. **Stage-E**：重新读取 **304** 条原始 FP32 logits，按冻结的 L11 action-only 三臂组合计算，主要干预 `reject_conflict` **11/32**，SA-sham **1/32**，dose-random **0/32**，因此 **10/32** 特异动作修复，覆盖 **3 供体组、6 宿主组**（8宿主场景中的7个）；L11 all-row 特异动作修复 **9/32**，L12 all-row **0/32**。这些结果是真实的、有意义的**受控内部干预效应**；它们不是无需内部干预即可部署的防御性能。

## 2. P0 — 阻止论文级通过的科学主张问题

### P0-1：中心“编码失败而非 readout/usage/interaction 失败”的排他性因果定位未证成

证据链支持一个**更窄**的命题：成功供体的自然激活片段可因果提高失败宿主的 C/A logits，在部分情况下使其跨越阈值，且优于现有对照。该干预是对 donor 与 host 多 token 高维状态的替换，**不足以唯一识别**原始失败是缺少冲突关系编码、下游解码/交互抑制、上下文融合失败、供体特异性状态偏置还是受上下文条件影响的多介体交互。

- 抑制臂中 main 与 host-SA-sham 效果几乎相同（−6.18 vs −6.45）；这是 **没有区分力的近似等效**，而不是直接证明 host 的 new-span 在自然计算中“被编码为 duplicate vote”。
- 直接的 H3 representation projection 预注册检验 **未达到** L11 AUC≥0.9 预期（实际 0.8441）。L12 的 0.901 为探索性跨层峰值，不得冒充 L11 确认性 PASS。
- 第 11–12 层可 patch、13层以后效果降低，不必然等于“此后不读取该 span”；存在干预位置、非线性重计算、路由和读出几何的替代解释。捕获投影在后续层仍不为零。
- 文献 `The Curse of Multiple Mediators`（arXiv:2606.27510）指出单个 activation-patching estimand 混合其他介体互动；本稿当前的主要效应不含足以排除该类解释的交互分解。

**处置**：或者将题目、摘要、讨论中的 *is an encoding failure / not in either readout / readout no longer consults span* 限定为“支持的候选解释”；或者补充在相同 Gold、内容、token 控制下能够**区别编码、使用、交互**的直接实验（自然场景解码、定向关系对照、联合/双向干预与必要性）。不允许通过重新解释 H3 不达标而追认 PASS。

### P0-2：共同恢复和“两个独立 reader 使用相同证据机制”的强主张过度，且被单供体支配

从 Stage-E 全部原始行，重新计算 `L11 all-row, main` 的**同一 native forward 内**四个 typed questions：
- 动作 `reject_conflict`：**11/32**；C 判断 `true`：**11/32**；**二者同时正确只有 8/32**。
- 对应 SA-sham 和 dose-random 的**双端同时修复均为 0/32**；因此 8/32 是有价值的特异性联合现象，**不是零结果**。
- 但 8 次联合修复中，**7/8 来自单个供体 `90dbf6d6536f`（`run-140`）**，另 1 次来自 `run-338`；`run-212` 两位供体 **0 次联合修复**。去掉 `run-140` 后仅 **1/24** 联合修复。
- 在更宽的 `action-only` 设置中，动作可改变而 C 仍 bitwise 不变；这说明 **action row 的自身可控性**，不能将其当作“从 C 检测传播到 A 安全否决”的因果中介链。
- 主稿 C5/C6 分别报告各自的 10/32 特异结果，不等于同一转发时两端都得到这些数字；讨论须单列同一 forward 的联合正确率和 donor/group 分解。

**处置**：给出 per-donor × per-host 的 C∩A 联合终点和所有控制组，区分（i）各行单独充分性、（ii）联合 typed-decision 一致性、（iii）真实 C→A 信息传递或共同上游介体。或者将主贡献收窄到特定模型中“分别可干预的 C 识别与 action 读出”，而不是已识别完整的共享编码—双读出安全机制。若保持跨来源普遍机制的论述，必须有独立于 run-140 的充分联合复现。

## 3. P1 — 论文成熟度 / 竞争文献 / 可复现性问题

### P1-1：论文级外部有效性不足、样本单位高度依赖

所有强阳性来自**同一个 SecJev-0.8B checkpoint、同一个 `twins_streamlet` DEV 模拟器家族**，4 个供体 / 3 个先前已接触来源组，近阈值宿主经过已观察结果有目的选择；32 个交叉 cell 不是 32 个 IID 样本。Stage-E 10/32 特异决策修复中，run-140 单供体贡献 6/10，去除此供体后 4/24（恰好达到预注册 2 donor groups × 2 host groups 的最低覆盖）。新数据的阶段预注册是积极实践，但不能替代未接触的来源家族/真正外部验证。若研究目标是顶会级的**一般性安全机制**，需要至少一个独立来源域/新模型或其他切实的强外推佐证；若没有则进一步收窄仅在当前 checkpoint/DEV 上的案例研究贡献，并相应调整发表定位。

### P1-2：直接相关已公开竞争研究的 novelty delta 比较尚不完整

`NOVELTY.md` / 手稿生成源码虽包含 SecJev、Lepori、Abdelsalam、Makelov、Zhang & Nanda，却未直接讨论：
- **Chu et al., From Detection to Refusal: Safer LLMs via Circuit-Guided Weight Scaling**, Findings EMNLP 2026：https://aclanthology.org/2026.findings-emnlp.1629/ （已发表的检测→安全决策因果分离、对六个模型的跨架构干预）；
- **Vaidyanathan et al., The Curse of Multiple Mediators: Hidden Interaction Effects in Activation Patching**, arXiv:2606.27510：https://arxiv.org/abs/2606.27510 （同一 activation patching 对“机制唯一定位”的解释约束）；
- 相关 `IPE: Isolating Path Effects`，BlackboxNLP 2025：https://aclanthology.org/2025.blackboxnlp-1.30/ ，可作为路径专门化对照而不必声称已实施。

这些研究**不自动否定** JEV 在 typed structured security scorer 这一具体问题上的新现象，却使“to our knowledge, no prior work”的排他性表述、机制辨识和顶级发表意义需要更新对照表。按已固定的标准，预印本也应比较实质内容；不可只按发表等级过滤。

### P1-3：最关键的源头语义/特异性替代解释未完全封闭

原样本中的 donor 自身就是正类 `reject_conflict`，直接把完整 donor-span hidden state 移植到 near-threshold host 可传递更一般的 decision-class prototype、置信度或上下文状态，并不必然传递**特定合法票据的作者—轮次—区块冲突绑定关系**。SA-sham、permuted、dose noise 排除了一部分替代解释，但还未证明针对相同 policy relation 的真正见证对应关系或非目标语义负对照。建议至少明确比较同幅度的**非本类冲突、相同分类但不满足宿主见证关系、反向 witness、匹配作者/轮次/区块**等必要对照；如不做则将“rule binding causal mechanism”退回为“positive-class-associated donor representation”层级。

### P1-4：全数据包的外部独立复现尚不完整

- 五个 analysis JSON 作者声称重新运行一致，本轮已经从 GitHub 原始 JSONL 独立核对主要 counts 和 Stage-E 联合终点；但 Stage-C–E capture tensors 在服务器，GitHub 只有 SHA256 清单，不等于外部复核者已拿到完整捕获数据。
- PDF/DOCX 为二进制，当前 UTF-8 GitHub 连接器拒绝读取，因此本次通过 `generate_v6.js` 查核主稿内容，**不能声称审过渲染版的 16 页全部视觉内容和 PDF SHA**。
- 应提供有权限的独立审稿者可实际获取/复算的 captures（不强制公开私有模型权重），并给出可执行、完整依赖锁定的最小 CPU 验证命令。GPU 重算仍需用户另行明确授权。

## 4. P2 — 可直接修复的文稿/工程问题

### P2-1：手稿再生成命令的文件名与打包输入不匹配

`assemble_v6.py` 读取 `generate_v5.js`，实际本次 `PAPER_CLAIM_PACKAGE_V1` 提交了 `generate_v5_input.js`，包内不存在 `generate_v5.js`。从 `REPRODUCE.md` 按给出的命令在包目录运行不能可靠再生。需要修脚本路径或明确复制步骤，并给出自检结果。

### P2-2：Stage-C CPU 复算示例路径不符合所声明的相对根

`REPRODUCE.md` 声明路径相对到 `A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/`；其 Stage-C 命令却写 `--run-dir G2_STAGE_C_GPU_RUNS/ATTEMPT_R1` 和 `--stage-a-per-scene G2_STAGE_A_ANALYSIS_R1/stage_a_per_scene.jsonl`，而文件实际位于 `G2_STAGE_C_GPU_R1/G2_STAGE_C_GPU_RUNS/ATTEMPT_R1` 与 `G2_STAGE_A_GPU_R1/G2_STAGE_A_ANALYSIS_R1/stage_a_per_scene.jsonl`。请修正可粘贴命令，避免把作者声称重现成功等同可交付包从清洁目录一键重现。

## 5. 集中修订目标（不做逐缺陷独立审计）

1. **优先科学主张收口**：降低 encoding-failure 与“双 reader 同一路径”措辞，明确哪些是直接干预事实、哪些是待验证机制解释；或者设计最少量**能区分主要替代机制**的确认性实验。不要泛化继续盲目扫描 100 个 GPU 实验。
2. 在主文增加 **8/32 的 C∩A 联合修复表**（SA/dose 皆 0）与 **run-140 7/8** 的真实贡献分解；action-only 自身修复 10/32 是独立结果，不能替代联合一致性。
3. 实事求是解释 H3=0.8441 的预注册失败，严禁 L12 事后峰值替代确认结论；L13 的措辞限制在“对该 patch site 的输出灵敏度降低”。
4. 完成与公开的安全决策电路和多介体文献的 novelty delta；按目前一个 checkpoint、一个模拟器、少数 donor 的有效性决定论文定位。如果要保留跨场景/因果安全机制的一般化主张，优先补充真正独立的测试，不要求为扩大实验编号增加轮数。
5. 修复制表、源代码/数据包中的复现路径及捕获访问方式，使外部复核者能独立复算关键终点。

**资源与审计规则**：本次报告即为这一份 `PAPER_CLAIM_PACKAGE_V1` 的**唯一一次完整论文级审计**。研究 AI 继续普通科研、修稿和工程自检；**不能对每项修复单独要求新的独立审计**。只有研究 AI 未来再次明确声称全部创新与整篇论文证据完整完成，才按治理 V2 触发下一次论文整体独立审计。没有此次审计自动批准任何 GPU/新来源推理。

## 6. 可核对的关键证据定位

- [声明包](https://github.com/dddd2024/jev/tree/e5de4b764b1776d288dfc87642ff19910998565d/research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/PAPER_CLAIM_PACKAGE_V1)
- [Stage C 真 GPU、AUC 和干预结果](https://github.com/dddd2024/jev/commit/8c5608c83f44534fe33a197e0cf95bedca9bf30f)
- [Stage D 真 GPU 与动作行不可达勘误](https://github.com/dddd2024/jev/commit/01f46ef8585b485f8d0c1ce4124cc0165464bba6)
- [Stage E 真 GPU 原始数据与分析](https://github.com/dddd2024/jev/commit/d7b55c4b2d65fed292ac8b59713bd74416c153af)
- [A517 竞争文献与当前声明索引](https://github.com/dddd2024/jev/commit/2c5b09a2d6585414cb3ab12608a33de877ca45c4)
- [现行新颖性标准](https://github.com/dddd2024/jev/blob/main/research_governance/JEV_RESEARCH_NOVELTY_AND_TOOL_REUSE_STANDARD_20261027_V1.md)

**最终判断**：目前已有**足以认真撰写机制性候选论文的真实结果**，但现有 v6 的**排他性失败定位及跨组共享机制主张尚超出证据**，且独立可复现性、直接先例比较尚未封口。**PAPER_AUDIT_REVISE_REQUIRED，不是 PAPER_AUDIT_PASS，也不是否定全部发现。**
