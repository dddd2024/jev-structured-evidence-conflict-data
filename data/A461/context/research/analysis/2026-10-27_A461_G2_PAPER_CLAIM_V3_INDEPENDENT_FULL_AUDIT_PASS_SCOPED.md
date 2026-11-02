# A461-G5-G2 V3 完整论文独立科研审计报告

**日期：**2026-10-27  
**正式审计对象：** `PAPER_CLAIM_PACKAGE_V3`，提交 `2fca4ef6757b9cf0de7cadf78da68f099fd4747f`，完成主张及独立审计触发提交 `45a522420d7855594b5e374e11c792a35a70ec81`，论文手稿 v9。  
**正式裁决：`PAPER_AUDIT_PASS`（限定于本文明示的狭义、受控因果干预结论）**。P0=0；发现 P1 编辑一致性×2、P2 排版×1，作为**不影响核心证据的提交前整改**，无需再次独立科研审计。  
**本次没有新增 GPU 前向，也没有重复运行已经冻结的模型实验。**

## A. 哪些论文级创新主张得到独立证据支持

1. **行为边界**：在同样 124 个构造的、带可执行规则 Gold 的 `twins_streamlet DEV` 场景，SecJev-0.8B 的新增冲突识别率约 11.3%，kev-4B 为 36.3%；相应严格识别供体 4/124（3组）与 44/124（14组）。**不把差异归因于参数规模**，因为训练目标、模型架构/数据也不同。
2. **自然激活片段具有条件性因果充分性**：在 SecJev 识别成功的追加冲突供体来源中，中间层全片段自然状态移植可使失败宿主的冲突 margin 上升，并在指定、靠近阈值的宿主上修复原生 C 行与动作行，优于所测试的 SA-sham、打乱和剂量匹配随机对照。SecJev 的同一模型前向联合修复 8/32，存在 run-140 7/8 的供体集中，作者诚实披露。
3. **kev-4B 的复制更稳定**：K-B 使用预定层筛选规则 `argmax median(main-doserand dM)`，在与复制集不重合的场景中选择 L11。K-C 的 14 个复制供体分别来自 14 个不同模拟器运行组，8 个靠阈值宿主。剔除同组配对后 104 个跨组组合，在同一 forward 中 C∩R 特异联合修复 53/104，对照 0/104，覆盖 14/14 组；最大单组 7/53=13.2%，留一组分析为 46–52 次。**104 不是 104 个独立任务**，因为供体和宿主重用。
4. **来源类别条件性差异，而不是已确认 recognition 单因子机制**：SecJev Stage-F FFF 未识别新增冲突 0/48、TTT-new 0/72、TTT-SA 0/72，认可供体 8/32；kev-4B 未识别来源 0/40。H-F2/K-C4 达到冻结标准；H-F1/H-F3 未达标。上述不同来源类别同时改变内容、上下文和来源—宿主关系，**不能**将结果归因于识别本身，不能证明内部具体关系见证机制。
5. **并未确定排他性 encoding failure、C→A 自然中介或同一安全电路**。SecJev 预注册 L11 H3 AUC 0.844 < 0.90，抑制实验与 Stage-D 勘误均被正确保留；全文将 encoding 作为候选而非已辨认因果机制。这使当前 `PASS` 只对**限定的表征移植效应及行为现象**有效，绝不延伸成一般大模型安全机制或真实部署防御。

**创新性比较的审计判断：** activation patching 本身早已存在，不是原创方法；现有相关论文（Abdelsalam et al. 2026 的代码语义冲突 patching、Chu et al. 2026 的 detection-to-refusal 安全电路、Lepori et al. 时序/利用分离，以及 Makelov、Zhang/Nanda、Vaidyanathan 的方法论限制）提供强近邻。v9 §2 Table R1 与 NOVELTY 的实质差异定位为：**合法追加安全证据的遗漏、逐臂可执行 Gold、typed independent-question outputs、same-forward conflict+action 双终点、匹配对照、跨源组复现**。审计未发现已公开近邻同时验证了这一完整、明确限定的经验结论，因此在这一狭义范围内属于具有实质新颖性的研究发现。**这不是对顶会录用、通用机制或投稿格式合规的保证**。

## B. 独立原始数据审查（不引用作者 summary 代替核算）

当前审计再次读取 GitHub 原始 `G2_K4B_KC_GPU_R1/.../raw_native_logits_k4b_kc.jsonl`（Git blob `19d3a06c27953b1f2b4dcd2770394d28741a69fd`）和冻结的 `k4b_kc_design.json`（blob `cd4cd9e5632cfa1b8aa476b94a332e3705af2f0f`）；将 donor/host scene SHA 映射至 frozen source groups，重新按 question logits 的 argmax 计算 `C=true AND certificate_action=reject_conflict`，配对 main、SA-sham 和 dose，并剔除 donor/host 同来源组：

| 观测项 | 审计独立结果 |
|---|---:|
| 原始完整行数 | 417 |
| main/sham/dose patch 行数 | 112/112/112 |
| 与 donor 同组而剔除的配对 | 8 |
| 有效跨组配对 | 104 |
| 主臂特异联合修复 | **53/104** |
| 贡献来源组 | **14/14** |
| 主臂 dM 高于 dose | **95/104** |
| 主臂 dM 高于 SA-sham | **104/104** |
| 主臂至少有一次修复的宿主 | **7/8** |
| 非目标 `evidence_level` 相对 sham 的 argmax 变化（探索性） | **24/104，全部在 53 次联合修复之内** |

最后一个结果非常重要：是否符合 `evidence_level` 的独立 Gold **没有核验**。本研究因此只能声称**指定的两个原生读出得到修复**，不能声称所有 typed 输出同时正确、整体系统安全率改善；V3 README 和 LIMITATIONS 已报告并约束这一点。

原有 V2 完整论文审计已对回执和 GitHub Releases 的六个张量资产的 API 大小和 digest 做过独立检查；本轮 V3 仅修正文稿，SHA、`numbers_v8.json` 及源数据保持不变。V3 附加 `REANALYSIS_CHECK.md` 提供 9 阶段复算和生成链条的作者回执，但**本审计没有下载 1.78 GB+ 的私有张量 tar 在本地重新解压，也没有独立可视检查 PDF/DOCX 二进制页面**。这不影响所述来源级 Logits 复算的范围，但不应把作者自检描述成审计方亲自执行的复算。

## C. V2 审计四项整改的本次裁决

| V2 发现 | V3 核查 |
|---|---|
| P0：recognition “而非 content” 单因素因果论证过强 | **已实质修正**：v9 §4.10、Intro、§5、§6、NOVELTY delta、CLAIMS C8 均改为 source-category contrast；承认 H-F1/H-F3 失败和多变量混杂 |
| P1：§5/§6 保留单 0.8B checkpoint 旧文 | **已修正**：现写 two kev-family checkpoints、同一家族模拟器 |
| P1：缺少相邻文献精确比较 | **已修正到可接受的限定范围**：v9 Table R1 和 NOVELTY 对比既有技术与新实证边界 |
| P1：K-B 与 K-C 被暗示是 source-group held-out | **已修正**：只说 disjoint scenes，明确组间重叠、统计依赖 |

**因此不再保留 V2 中的 P0 阻断项。** 这一修改不是证明“机制已被唯一解释”，而是诚实缩减科学结论，以让已完成的证据能支持主张。

## D. 非阻断提交前整改（作者自检，不必发起新的独立审计）

**P1-Editorial-1：配套 `NOVELTY.md` 两处尚未同步 v9 的旧说法。**
- “Tang et al., ICML 2026” 对照下仍写 `G2 places the failure at the encoding of the appended span`。应换成 `G2 establishes interventional sensitivity of the appended span; encoding deficiency remains a candidate, not an identified exclusive mechanism`。
- “From Detection to Refusal” 对照下仍写 `We separate recognition from decision class (Stage F)`。Stage-F 的 source-category controls 并未 isolation；换成 `We compare strictly recognized appended-conflict donors with class-matched, content/context-different sources; the contrast does not isolate recognition`。

以上不在 v9 主稿和 NOVELTY 新 delta 的最终主张中，因此认定为**说明文件的陈旧论断**，不推翻整篇论文主干的合法推断；但是提交论文公开材料前必须纠正，以免造成读者误解。

**P1-Editorial-2：避免把联合修复当作整个模型的安全纠正。** V3 已在配套 LIMITATIONS 披露 `evidence_level` 有 24/104 的非目标变化（Gold 未核），正文/摘要继续严格只说冲突 readout 与 `certificate_action` 两个终点，不能拓展为全部 typed 证书正确或可部署安全提升。该结果可作为论文局限/探索性诊断，而非需增加 GPU 的入门门槛。

**P2：** `NOVELTY.md` “Where it holds:” 一行的 Markdown 强调缺少闭合 `**`，修正文档格式。

## E. 最终科学结论和后续路线

**`PAPER_AUDIT_PASS`（仅限条件性自然激活表征移植、可执行规则 Gold、同一 forward 的冲突/动作读出修复、kev 家族/同一构造模拟器内跨源组证据）。**

不授予以下任何更强主张：已辨认唯一“新证据编码失败”内部机制、已识别 C→A 自然中介、认定 token witness binding 电路、已证明因果机制跨非 kev 架构普适、当前方法提升部署安全率或达到顶会录用标准。

下一阶段是**论文作者常规自检和投稿准备**：修正上面两处 NOVELTY 陈旧句子与一个 Markdown typo、检查论文格式和 venue 政策、维持样本非独立和负结果披露。不必为非阻断文字修订启动第三方 L0/L2/L3，也不需要自动开启新一轮 GPU 实验。论文核心证据已经满足本次限定主张下的独立科研审计。

## F. 依据

- V3 声明：`45a522420d7855594b5e374e11c792a35a70ec81`，v9 生成源 `PAPER_CLAIM_PACKAGE_V3/generate_v9.js`，配套 `NOVELTY.md`、`CLAIMS_EVIDENCE_MAP.md`、`LIMITATIONS_AND_ERRATA.md`。
- K-C 原始 GPU：`5ef7a16d517e01cebeca287a8160bd7ed2aca085`，预注册设计 `3a6173f92e8066d2be8ae170e75f6fa94f4caa1f`。
- V2 独立审计：`research/analysis/2026-10-27_A461_G2_PAPER_CLAIM_V2_INDEPENDENT_FULL_AUDIT_REVISE_REQUIRED.md`，本轮逐点比对确认重要更改。
- 直接先例：`https://arxiv.org/abs/2607.05587` (Abdelsalam et al. 2026), `https://aclanthology.org/2026.findings-emnlp.1629/` (Chu et al. 2026), `https://arxiv.org/abs/2606.27510` (Vaidyanathan et al. 2026)。
