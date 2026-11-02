# JEV A461｜论文 PASS 后机制辨认唯一研究主线（2026-10-27 V1）

**状态：ACTIVE_RESEARCH_PRIORITY / ROUTE_FROZEN / NOT_MECHANISM_PROVEN。**  
**适用范围：** A461-G5-G2 追加合法冲突证据（append equivocation vote）遗漏现象的**后续机制深化**。  
**设立依据：** 用户明确纠偏：当前目标是**深入解释已经发现的同一现象的因果机制**，不是通过增加四读出诊断、模型数量、任务种类或模拟器来取代机制解释。  
**与既有论文关系：** `PAPER_CLAIM_PACKAGE_V3`（v9）已经对**限定的自然激活移植修复效应**取得内部完整论文审计 `PAPER_AUDIT_PASS`，这是稳定基线；不把 PASS 误写为已经辨认 encoding failure、完整 C→A 中介、电路或跨架构普适性，也不为本研究强制重启整稿审计。  
**顶层行动原则：** **M1 → M2 → M3，严格顺序准入；宁可 STOP/不启动 GPU，也不通过外围任务迭代代替解释。**

## 0. 唯一核心科学问题

当真实有效且合法追加的冲突证据使规则 Gold 从允许操作转为 `reject_conflict` 时，模型为什么经常仍保留非冲突读出/允许操作？为什么严格识别成功的供体在特定中间层的自然 hidden-state span 经受控移植，可以纠正失败宿主的冲突判断和动作？**是哪一步内部计算失效、哪个内容或路径具备可排除替代解释的因果作用？**

现有明确事实（不新增意义推断）：
- SecJev-0.8B 和 kev-4B 同一个冻结构造场景家族都有新增冲突遗漏；K-C kev-4B 原始 FP32 logits 417/417，跨组有效配对 104，同一 forward 的主干预 C∩A 联合修复 53/104，SA-sham/dose 0/104，14/14 donor source groups 贡献；104 crossed cells 并非独立任务。
- SecJev 的相关 Stage F 主干预 8/32 联合修复，其中 7/8 来自 run-140。SecJev L11 的 H3 AUC=0.844，未过预注册 0.9 门槛。
- **已证明的是干预对指定读出的条件性充分性；尚未确定究竟未编码、未传递、未读取或发生了多介体交互。**

## 1. M1｜关系表征辨认：内部是否形成了正确的冲突关系信息？（当前唯一 P0）

**目标：** 严格辨认作者—轮次—区块的合法冲突关系在成功/遗漏样本中是否形成**可用且具有因果作用的**内部特征，而不是把 probe 可读、C 类别或整段 donor 状态视为关系语义已被识别。

主要竞争解释：
- **H-ENC**：有关见证关系未形成足以支撑指定读出的表征。
- **H-READ**：关系表征存在，但下游读取/运用失败。
- **H-CLS/H-CTX**：修复来自一般拒绝倾向、供体上下文或与其他中介的交互；没有证明具体 witness binding。

M1 的**可证伪对照**（先 CPU Gold，再有条件 GPU）：
1. 固定真实 host、原生 Gold、目标读出、供体/宿主身份及严格原始记录；控制同类别的正确 witness、同类别但关系错配 witness、被模型错过的真实 conflict、duplicate SA、token/长度配对及随机剂量、非相关片段。不要跨 run 将 `v0`、`b2` 等局部字符串直接视为同一实体。
2. 将 gold 的可计算关系（author/round/block、有效票、时间）与 token span 对齐，并**在不改变拟固定语义变量的条件下**构造反事实；如果关键单因素对照无法构造，记录不可识别和 STOP，而不是事后改名。
3. 现有跨组 whole-span patch 作为正控；**直接解码/线性 probe 只作辅助**，只有预注册的语义角色条件干预才能为“关系表征”提供更强因果证据。
4. 正向恢复与反向破坏需分别报告；恢复成立、抑制不特异时，只能给“单向局部充分性”。

M1 准入要求：合法 witness 的独立 Gold 已复算；核心对照每格可构造且匹配；来自真正独立 run group 的单位数明确；原生模型行为可复验；机制假说和能区分它的预测在看到新 GPU 数据前冻结。

**当前下一任务（唯一）：`A461-MECH-G1.0`，CPU-only：原始 state/四项 Gold + role-normalized witness 匹配可行性检查。** 现有协议 `research/experiments/A461_MECH_G1_CAUSAL_ROUTE_VS_ENCODING_CPU_GATE_V1.md` 是下位实现草案。本门未完成、GPU 未准入。服务器语料从已冻结 runner 指定的 `~/wjc` 路径读取，禁止虚构已有的服务器证据。

**M1 通过定义：** 至少一个机制预测在预注册的真实独立对照中成立，能够明确排除“同类拒绝原型/任意 donor 变化”中的相关替代解释；如无法排除应停在“有表示或干预相关性，但未辨认关系机制”。

## 2. M2｜信息传递、读取与计算路径辨认（依赖 M1；P0）

**目标：** 将“M1 中已被精确定义的关系特征”与 native `conflicting_vote`、`certificate_action` 的计算路径关联，具体区分：
- 特征在 append-span 的哪段/哪个层被构造；
- 正确特征是否到达候选 key / query 或相关注意力/MLP 中介；
- readout 是否有能力使用特征，但在失败 host 的自然前向中因路由/上下文而未使用；
- donor × host 与多介体交互是否解释 whole-span 恢复。

**拟用实验：** 有控制的 row-specific / layer-specific / path-specific patch，2×2 保持/替换关键中介，以及源—宿主反向操控；完整列出被修改与保持原样的组件；报告各臂真实 native logits 与 margin、独立 Gold，不从一个 full-span patch 推断唯一电路。

**M2 通过定义：** 至少一项路径级预注册实验给出“该路径特异因果作用”的正向与负向控制，并能区分至少一个竞争机制（encoding / use / interaction）。如无法区分，保留未定位结论，不夸大。

## 3. M3｜机制级因果验证与稳定复现（依赖 M2；P0）

**目标：** 在前两个阶段已明确的机制下提出**新的、在冻结复现集预测得出、且可被证伪**的因果预言，进行恢复与抑制双方向、消融、独立 source groups / hosts 复现，以及错误副作用检查。

**端点：** 主要机制指标需先预注册，至少覆盖冲突识别 C、合法动作 A；`evidence_level`（官方 ordered score）和 `quorum` 仅用于排查目标外影响/整体 Gold，不得用探索性 argmax 冒充官方分数。若声明“全证书正确”，四题 Gold 均须满足，不能只用 C∩A。

**M3 通过定义：** 正反向干预与严格关系对照在先行隔离的独立场景成立，提供机制特异因果效应及其条件/失败边界；必须报告所有失败/零效应、供体集中特征、实验选样和统计独立单位。

## 4. 优先级与非目标（避免研究偏航）

| 科研事项 | 优先级 | 定位 |
|---|---|---|
| M1 当前现象关系表征辨认 | **唯一即时 P0** | 科学机制主线 |
| M2 对具体信息通路/读取的隔离 | **依赖 M1 的 P0** | 机制路径 |
| M3 机制级正反向与独立验证 | **依赖 M2 的 P0** | 因果闭环 |
| 旧 logits 的四输出头、ordered-score、quorum 分析 | **辅助诊断** | 仅定位副作用、识别 host Gold 的混杂；不得代替 M1–M3 |
| 第三模型、跨模型家族复制 | **HOLD** | 仅在检验明确机制预测时解锁 |
| 跨授权状态/访问控制/证书撤销等任务 | **HOLD** | 仅在机制明确后检验泛化，不作为眼下新主线 |
| 真实系统安全部署与 deterministic rule baseline | **HOLD** | 更后期的外部有效性/实际安全价值验证 |
| 任意新实验编号/重复审计/重新跑旧 GPU | **NO-GO（无新增因果信息时）** | 不能计为机制进度 |

**禁止偷换：** “能修复”不等于“编码失败”；“probe 可解码”不等于模型自然使用；“两个同家族模型”不等于架构普适；“四头发生响应”不等于已找到共享因果电路；“C/A 正确”不等于全体 typed gold 正确。

## 5. 行动顺序与治理

1. **现在**：执行 `A461-MECH-G1.0` 的 CPU 准入条件；严格读取真实 corpus，复核完整 witness / Gold / token / 来源组身份。CPU gate 完成要保留实际结果与失败原因；没有结果就继续标记 NOT_EXECUTED。
2. **M1 可准入**：把形成的关系匹配对照和 falsifiers 写成冻结的最小 GPU 方案（名为 `A461-MECH-M1-GPU-R1`，只在此时才成立正式实验）；确定预算、每批硬限、不可更改的样本选择和捕获计划，并按照既有的有效 GPU 授权/配额治理执行。
3. **M1 结果决定 M2**：只有特定关系表征得到可辨认的证据、或明确排除其一替代解释，才设计路径操控；不得事后绕过门槛以获得更好阳性。
4. **M3 独立验证后**：决定把真正新机制发现加入当前 v9 的下一修订，还是构成独立但实质不同的论文。**不预先按两篇分割**。

**执行约束：** 前置学术文献核查、冻结 Gold、确定性 CPU 自测、双向/负对照、source-group 严格统计、逐次预算与 durable ledger、模型/数据 digest、原始日志、GitHub 留存；在服务器上所有新文件落在 `~/wjc`。既有审批与授权修订仍适用，不自行创造重复审计流程。

## 6. 已存在的证据/研究文件（有明确上下级）

- **当前已有受控效应和纸面审计**：`research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/PAPER_CLAIM_PACKAGE_V3/`，`research/analysis/2026-10-27_A461_G2_PAPER_CLAIM_V3_INDEPENDENT_FULL_AUDIT_PASS_SCOPED.md`。
- **现有机制先验与初始 CPU 实证**：`research/analysis/2026-10-27_A461_POSTPASS_MECHANISM_FOUR_HEAD_CPU_G0.md` 和 `research/analysis/scripts/A461_kc_fourhead_cpu_v1.js`。它们只是约束机制猜想的旁证，不是替代主线。
- **M1.0 下位 CPU 准入方案**：`research/experiments/A461_MECH_G1_CAUSAL_ROUTE_VS_ENCODING_CPU_GATE_V1.md`。本文件给它明确的优先级与目的，不等同已执行。
- 先例：Lepori et al. ACL 2026（encode/use 分离），Vaidyanathan et al. 2026（multiple mediators），Brunello et al. 2025（path-specific effects），及 `PAPER_CLAIM_PACKAGE_V3/NOVELTY.md` 中已有的近邻工作。必须先查最新竞争文献再冻结新 GPU。

**标准：** 研究进展的单位是“排除了哪个替代机制、对何种关系进行了可证伪因果识别”，而不是实验次数、模型数量、输出头数量或论文编号。
