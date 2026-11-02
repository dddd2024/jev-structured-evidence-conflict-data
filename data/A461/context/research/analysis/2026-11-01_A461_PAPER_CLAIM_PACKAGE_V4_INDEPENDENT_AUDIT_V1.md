# A461 PAPER_CLAIM_PACKAGE_V4 论文级独立审计 V1

- 审计日期：2026-11-01（Asia/Shanghai）
- 审计对象：`research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/PAPER_CLAIM_PACKAGE_V4/`（manuscript v10 / M1–M22）；对照仓库 `main` 提交 `2ffb9b366d0e2768c6c684fe2dedba7ba87ea5cd`。
- **论文裁决：`PAPER_AUDIT_REVISE_REQUIRED`。** V3 对限定 G2 移植效应的 `PAPER_AUDIT_PASS` 不撤销、不扩展至 V4 深层机制。创新性 `NOVELTY_NOT_YET_PASS`，完整自然因果机制 `NOT_IDENTIFIED`。
- 审计类型：论文级一次性集中缺口清单；不为单次修订循环触发新独立审计。没有运行 GPU、没有修改冻结数据、Gold 或正式实验结果，也没有发布机制 captures。
- **核验边界：** 直接读取 GitHub 版本化协议、结果、复算脚本和原始 JSONL；从 M18/M20/M22 原始 logits 独立重数。M19/M21 的读出指标核对分析 JSON 和论文数值提取脚本，未在本次重跑前向或独立读取未发布的 4.1GB capture、head.pt；v10 正文依据 `v10_edits.py` 的逐节完整生成文本和证据地图审阅，未独立渲染检查 DOCX/PDF。**不能把作者同脚本的 22/22 ALL_EQUAL 当成完整独立实验复现。**

## 一、独立 CPU 原生动作复核（直接解析 GitHub raw JSONL）

`M18_GPU_R1/raw_native_logits_m18.jsonl`、`M22_GPU_R1/raw_native_logits_m22.jsonl` 各有 620 条：124 scene × 5 arm，17 source groups。对每条 `certificate_action` 使用三个原生 logits 的 argmax，并与 `gold_action` 逐条比较：

| 模型 | new: reject/accept/wait | old 误拒 | SA 误拒 | ROUND 误拒 | OUTSIDER 误拒 | 非 new 误拒总计 |
|---|---|---:|---:|---:|---:|---:|
| kev-4B（M18） | 40 / 83 / 1 | 0 | 0 | 7 | 6 | 13/496 |
| SecJev-0.8B（M22） | 14 / 69 / 41 | 11 | 11 | 10 | 7 | 39/496 |

所有 124 条 new 的 Gold 均为 `reject_conflict`，所有 496 条非 new 的 Gold 均为 `accept` / `wait`。该**完美 arm×Gold 绑定**直接可见于原始行，而非推测。

直接解析 M20 `raw_native_logits_m20.jsonl`：488 行、488 不重复 forward_index；原生 donor-new 14/14 的 M>0。以 M≤0 独立重数：
- `full_host` 21/104，`full_ctrl` 7/104；
- `bulk_host` 27/104，`bulk_ctrl` 8/104；
- `bulk_round_self` 9/14，因而有 **5/14** donor 仍保留 M>0；
- `bulk_hostmean` 2/14。
以上与正式 `M20_ANALYSIS_R1/m20_analysis.json` 的主要率和 M18/M22 报告计数相符。另从 `numbers_mech_v1.json` 重加各阶段 forwards = **86,758（kev-4B 86,138 + SecJev 620）**，与包内总数相符。

此核验支持 **原生现象和局部移植干预的数值真实性**，但不独立证明隐藏张量的写入位置、probe 学到的语义变量或自然机制的唯一性。

## 二、实质性问题（按一次集中修订清单）

### P0-1｜M18/M22 的线性可解码性存在 arm/Gold 混杂（核心机制识别）

证据：`PREREG_M18_R1.md` 规定 probe 标签为 Gold reject，MISSED=预测失败的 new，BENIGN=未拒绝的其他四个 arm；对两模型原始 JSONL 独立检查，所有正类均 new，所有负类均非 new。leave-one-source-group-out 避免同组泄漏，但**不能解除 arm、Gold、消息形态、文本角色与正确认证语义的完全共线**。表面 embedding AUC 0.816/0.805 小于 L11 AUC 0.993/0.964，说明深层比表面特征更强，却不唯一证明“冲突有效性语义已编码”。高 AUC 亦不能排除 learned arm shortcut、不同位置/形态和 Gold 规则共同变化。

要求：要么增加同 arm、同 source-group 下 Gold 不同且格式匹配的反事实/负对照，独立检验真实可信 validator×round×block×vote×validity 关系；要么将 M-E 明确降为“本构造数据上，new-missed 与 non-new-benign 的状态可线性区分（above embedding surface）”，撤回已唯一识别冲突语义的语言。不得用“已 pre-register”或“AUROC 很高”代替可辨识性。

### P0-2｜M19/M21 的 null 不足以证明完整 readout 不使用冲突

`M21_RESULT_R1.md` 报告：decide-token 层 19/31 上按受控方向的 β=0.2||h|| push 修复 0/84；同剂量随机方向近乎惰性；L31 γ32 gain 修复 1/84，但新增误拒 17/483；梯度余弦约 −0.062。pre-reg verdict `NOT_READABLE` 仅适用于**这些位置、方向、幅度和指定指标**。原生 head 还读取 option-token states；这些没有被同路径干预。随机方向同时惰性，也使指定方向的零效应缺乏特异性。不能由此推断整个原生决策电路“不读取任何冲突信息”，更不能推断完整的自然 QK/OV/MLP 中介。

`v10_edits.py` 的 abstract/contributions/§4.15 使用“present but not used”“the miss is not a failure to form it”“steering ... moves no decision”等超范围表述，其中最后一句还忽略 γ32 造成 18 个目标外或目标内动作改变。要求将 M-F 改为“测试的 decide-token conflict-aligned steering 未产生选择性的修复”；将“present but unused”明确标成**有限数据的候选解释**，不称已证明自然 readout 失败或已辨认电路。若坚持强机制结论，先补 option-token + decide-token 联合的自然路径因果测试和识别对照。

### P1-1｜L11 round-sensitive 作用成立，但 writer/认证关系与自然必要性不得泛化

M1 53→1/104，M2–M5 局部 patch 控制、M20 round-self 9/14 为**有价值的局部双向证据**。但 M3 严格 H* 仅 head 10，其他 heads 8/9/14 为近阈值/分割不稳；M2 两个 LOGO 将 formation layer 推到 8；M4 context 与 OTHER_ITEMS 同时起作用；M20 host→donor 的识别丢失仅 21/104、27/104（对照 7/104、8/104），5 个 donor 在 own ROUND-BULK 干预下仍有 recognition。不能声称唯一原生认证电路、所有场景必要性、或已区分 validator/block/vote 等字段的联合作用。改为“kev-4B 的特定 14 donor×8 host 上，L11 context/round-sensitive attention 写入具有局部条件性充分性，及对 9/14 recognizers 的部分干预必要性”。

### P1-2｜独立性和跨模型泛化不足

M22 是 M18 probe/monitor 的第二个 kev-family checkpoint、同 124 scenes/17 groups 的**同家族再测**；不是 M1–M5/M17/M19–M21 自然因果路径复制。K-B/K-C scene 分离但 donor source-group 交叠；104 crossing cells 共享 14 donors/8 hosts。禁止把 `source-group LOGO` 当独立环境/架构复制。若声称泛化，须独立 scene family、未见来源组与第二模型机制干预；否则固定为“同家族、同构造模拟器的有限 replication”。

### P1-3｜安全端点不能只合并为“未 reject”或把 probe 当部署防御

根据独立 raw recount：kev-4B new 错误 accept 83、wait 1；SecJev 错误 accept 69、wait 41。合法四 arm 上分别有 13/496、39/496 原生误拒，还存在大量 accept↔wait 错误。不能用 reject-error 一个数字替代三动作风险和组间不确定性。M17 自然值移植 `full` 对 SA/ROUND 产生 36/104、43/104 误拒；M21 γ32 额外误拒 17/483。规则 oracle 在本模拟器上可精确给出 Gold；supervised monitor 需要规则标签，`GENERIC_MATCHES` 两模型均成立。安全贡献仅 S2 条件性描述/诊断，无 S3/S4、无真实部署、无相对规则基线的部署收益。

### P1-4｜novelty 尚无可确认、不可替代的机制增量

直接相关公开先例包括：
- Lepori et al., *Language Models Struggle to Use Representations Learned In-Context*, ACL 2026（represented-but-not-deployed） https://aclanthology.org/2026.acl-long.676/
- Chu et al., *From Detection to Refusal: Safer LLMs via Circuit-Guided Weight Scaling*, Findings EMNLP 2026（安全检测→拒绝多阶段因果电路，跨 6 模型） https://aclanthology.org/2026.findings-emnlp.1629/
- Ma et al., *Mechanistic Diagnostics of Spatial Lexical Bias in Multimodal Large Language Model Spatial Reasoning*, EMNLP 2026（正确关系可读但决策错、patch/neuron 定位） https://aclanthology.org/2026.emnlp-main.2575/
- Vaidyanathan et al., *The Curse of Multiple Mediators*, arXiv:2606.27510（patch 中介交互与归因限度） https://arxiv.org/abs/2606.27510

作者 `NOVELTY.md` 也承认 probe、patch、steering 和 decodable-not-used 已有先例；额外价值主要在 source-internal rule oracle、round-sensitive 同场景局部干预、两侧风险对照。当前更像**具体场景的技术性实例化**，并不能直接给出显著原创的完整内部安全机制。正式 `NOVELTY_NOT_YET_PASS`，如要争取强贡献，需在未见场景中验证自然可信/伪权威字段组合的可辨识中介及安全改善，不以更多轮号替代科学分辨力。

### P1-5｜可复核性与修改历史的表述

`RECOMPUTE_MECH_R1/RECOMPUTE_MECH.json` 报告 22/22 EQUAL，属于作者相同冻结分析脚本在既有输入上的**确定性再计算**；不能作为独立于分析规则、数据标签、capture 来源的审计。M3/M5/M18/M19/M21/M22 需要服务器端未发布的 captures；M19/M21 还需要 pinned head.pt。此次未访问原服务器 capture bytes，不宣称逐 tensor 完整 SHA、head 导出或 PDF 排版均独立 PASS。M17 v1 真实返回 INCONSISTENT，v1.1 修复后可用，须保留“post-run analysis correction”显著标记；M22 None-safe 修复在预注册前，不能混同。

### P1-6｜“每项修复都审过 false veto”范围越界

M17 实际覆盖 four arms (`full`、`meanD`、`cs0`、`abc05`)，并非 M1–M16 所有已测试 repair 变体及剂量。V4 `README.md` 的 M-D “Every repair is checked for false veto” 和 `v10_edits.py` contributions “false veto of every repair” 需要改成“four representative repair families checked in M17”，其余按 `NOT_TESTED` 处理。

### P2-1｜M20 保留 donor 数量误述

M20 正文称 9/14 donor 识别丢失，却列出“four donors that keep M>0”；独立 raw recount 为 14−9=**5**，故四个列出者至多是示例而非全集。修改措辞，不改原始数值。

### P2-2｜文稿措辞与书面证据状态

`v10_edits.py` 的“steering ... moves no decision”须更正为“20% push 无翻转，32× gain L31 造成 1 次修复+17 次合法误拒”。任何列为“完整机制已找到”“独立跨架构复制”“monitor 优于通用 probe”的叙述均删除。 `PAPER_CLAIM_PACKAGE_V4/README.md` 在正式再审前保持 `UNVERIFIED_PAPER_READY_CLAIM`，不得由本审计直接升级为 PASS。

## 三、仍可保留的经验证事实

1. G2 V3 的限定范围 patch sufficiency 的历史 PAPER_AUDIT_PASS 保留。
2. M1–M5 与 M20 的 kev-4B 局部 L11 round-sensitive attention 结果、条件性充分性和部分必要性作为**限定因果结果**保留；M20 原始数量直接复核一致。
3. M18/M22 在同一模拟器的 new-missed 与 non-new-benign 分类下深层表示线性可分，监督 probe 优于 embedding baseline；但不单凭此证明完整认证关系被编码。
4. M19/M21 的特定 readout steering 失败是可信负结果；不转为“所有读出路径无效”。
5. M17、M21 的 false veto 副作用和 M22 三动作代价是实质性 S2 安全证据；没有实现防御。
6. 原始日志计数与 22 阶段复算回执相容，但没有完成服务器 captures 的本审计独立核验。

## 四、一次性返修验收清单（不自动要求 GPU，也不循环发起独立审计）

1. 将 M-E/M-F 以及 abstract/contributions/discussion 改成最窄可支持陈述；若坚持“完整自然机制”需新正交设计及可证伪介入证据。
2. 对 M1–M5、M20 严格标注 `local conditional sufficiency / partial necessity`，并列出 M2/M3 异质性、M20 的 5 位 survivor。
3. 将三动作错误接受/错误 wait/合法误拒按 arm、模型、source group 作为论文安全表主结果，并说明固定规则基线与非部署场景。
4. 收窄 M17 风险覆盖范围；修正 M21 任何“没有动作翻转”表述及 M20 donor 数量用语。
5. 将 related work 直接差异与最小实际 novelty delta 汇总成严格竞争矩阵，不能把 probe/patch/steering 作为新方法。
6. 复核 manuscript v10 DOCX/PDF 的最终文字、表格和数值映射，并由有原始 server capture 授权的独立复核者校验所需 Tensor/Head/SHA；未核验填 UNKNOWN，不得标 PASS。任何发布 captures 需要另获用户允许。
7. 如果作者希望支持更强论文级新机制，先独立确认同 arm、同 group、Gold 有变化的真实认证关系反事实的可构造性，再决定是否存在高信息价值实验；没有也可以仅作为局部机制与 S2 诊断结果保留。

**总裁决：`PAPER_AUDIT_REVISE_REQUIRED`（P0×2、P1×6、P2×2）。这不是数据全部无效，也不是“22/22 复算失败”；而是整稿当前所声称的机制识别和创新性超过了已消除混杂的证据范围。**

## 五、核验用路径

- V4: `research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/PAPER_CLAIM_PACKAGE_V4/`
- Raw: `research/rounds/A461_MON_M18_SPAN_MONITOR_GPU/M18_GPU_R1/raw_native_logits_m18.jsonl`; `research/rounds/A461_MON_M22_SECJEV_REPLICATION_GPU/M22_GPU_R1/raw_native_logits_m22.jsonl`; `research/rounds/A461_MECH_M20_NATURAL_NECESSITY_GPU/M20_GPU_R1/raw_native_logits_m20.jsonl`
- Source reports: `M18_RESULT_R1.md`, `M20_RESULT_R1.md`, `M21_RESULT_R1.md`, `M22_RESULT_R1.md` in their stage directories.
- 2026-11-01 literature/risks: `research/literature/A630_20261101`, `A631_20261101`, `A632_20261101`.
- Governance: `research_governance/2026-10-27_JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2.md`.
