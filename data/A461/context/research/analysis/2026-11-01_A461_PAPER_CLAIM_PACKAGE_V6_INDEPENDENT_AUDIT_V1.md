# A461 PAPER_CLAIM_PACKAGE_V6｜论文级独立审计 V1

- **日期：** 2026-11-01（Asia/Shanghai）
- **裁决：`PAPER_AUDIT_REVISE_REQUIRED`**；**P0×2 / P1×5 / P2×2**。既有 V3 对 G2 有限移植效应的 scoped PASS 保留，不扩张到 V6。
- **审计冻结对象：** `PAPER_CLAIM_PACKAGE_V6` 的论文主张与 v12 手稿；内容提交 `fd58722b19f6d571c446b876d1f759c344a07571`，哈希清单提交 `2b537bae22451733f9ea4fc59e4cef0031fb414e`；用户审计触发提交 `0170b6994f9cbf3e841d508eb7a46b15d52b0641`；截至 `88573d7a95efb7cfbd0ae29e4022e562f008bc3b` 的 SHA256SUMS 状态修订。
- **审计方式：** 直接读取 GitHub 版控中的 M23 原始 JSONL、协议、manifest/design、分析 JSON、执行回执、G23 CPU Gold 双 oracle 结果、V6 证据映射和 `generate_v12.js` 文稿生成源码，独立按原生三动作 logits argmax 重数。对 M1–M22 审阅历史独立审计及本轮证据包，**未**重跑 GPU、未重新加载/核验 4.1GB captures、M23 服务器端 captures、pinned `head.pt`，未独立渲染 DOCX/PDF，未运行 SHA256SUMS 对整个包的字节级审查；这些项目为 **NOT_INDEPENDENTLY_VERIFIED**，不是 PASS。

## 一、原始 GPU 原生行为的独立重数（不依赖作者分析脚本）

读取：
- `research/rounds/A461_MON_M23_TWIN_PROBE_GPU/M23K_GPU_R1/raw_native_logits_m23k.jsonl`
- `research/rounds/A461_MON_M23_TWIN_PROBE_GPU/M23S_GPU_R1/raw_native_logits_m23s.jsonl`

逐行将 `certificate_action` 三个 logits 取 argmax，与 `gold_action` 对照；按 `target_scene` 配对 `new/TWIN`。

| 项目 | kev-4B | SecJev-0.8B |
|---|---:|---:|
| 行数 / 配对 / 来源组 | 248 / 124 / 17 | 248 / 124 / 17 |
| new 原生 reject / accept / wait | 40 / 83 / 1 | 14 / 69 / 41 |
| TWIN 原生 reject / accept / wait | 45 / 72 / 7 | 15 / 56 / 53 |
| new Gold | reject 124 | reject 124 |
| TWIN Gold | accept 102 / wait 22 | accept 102 / wait 22 |
| new 拒绝时 TWIN 仍拒绝 | 37/40 | 14/14 |
| new 未拒绝时 TWIN 却拒绝 | 8/84 | 1/110 |
| TWIN 错误拒绝覆盖来源组 | 14/17 | 9/17 |
| new 未拒绝场景的 median(TWIN M − new M) | +0.29661 | +0.57510 |
| 全 124 对中 TWIN M > new M | 88 | 101 |
| span 相同位置 / decision position 相同 / sequence length 相同 / full-token SHA 不同 | 124/124 各项 | 124/124 各项 |

上述数字独立于 M23 analysis JSON 复算，与作者汇总的核心新结果一致。注意：相同 span、位置、长度与不同 full-token SHA 的检查是元数据级核验，**未**独立证明上下文 token 必然只改一个，也未逐 tensor 校验 embedding/capture；“只改一个此前 partner round token、两 oracle 一致”依据冻结设计与 G23 结果/runner gate。

**已验证的有限事实：** 在构造的同一批 124 场景、同一 partner-round 反事实中，两个 scorer 的真实冲突拒绝对消除冲突关系表现出明显不稳健，且对合法 TWIN 有可观错误拒绝。保留为模型行为结果；M23 所有分析 verdict `ARM_SHORTCUT` 的回执存在，但 probe AUROC、bootstrap CI 未经过本审计独立的 tensor 级重算。

## 二、问题清单

### P0-1｜“neither scorer checks the relation”超出已识别的因果机制范围

v12 `generate_v12.js` Discussion 使用 “The scorers do not check the relation that makes the appended vote a conflict”；§4.18 使用 “Neither scorer's conflict judgment depends on the element that defines an equivocation”；README 标题、摘要也以 “form, not validity” 作为强机制解释。

M23 是单一干预家族的**行为对照**：移动前序 partner vote 的 round，保持追加票与位置相同。它说明模型**没有可靠地把 Gold 的变化反映在拒绝判断上**，并不能识别模型的内部计算“完全没有检查或使用 partner 关系”；`new/TWIN` 决策差异也并非全零（kev-4B 在 40 个 new-reject 中 3 个 twin 改判；SecJev 在全部样本中亦有边际变化）。M1 的 own-round patching 也不是 partner-round 自然路径的机制解析。

**整改：** 全文将无条件 `does not check / never depends / ignores the partner` 改为“在该 partner-round matched counterfactual 上，大多数原生拒绝以及 readout 未随 Gold 翻转，显示与形式线索一致的非有效性稳健性失败”；把“形式驱动”明确标成受控任务上的**行为解释**，而非唯一内部因果机制。无需为了文字收窄而补跑 GPU。

### P0-2｜把 `ARM_SHORTCUT` 阈值 verdict 等同于“无有效性表征”遗漏了反证方向

M23 预注册的 `ARM_SHORTCUT` 判据为 AUROC_pair ≤0.65 **或** TWIN_flag@FV5 ≥0.50。这可反映很差的有效性选择性，**不是**“模型完全没有编码或区分关系”的证明：即使一个检测器能区分两组，只要阈值较宽就可能判 shortcut。

尤其是 SecJev `PROBE:SPAN_ATTN11`：作者结果 AUROC_pair **0.698** [0.642,0.772]；在 MISSED 成对场景 `score(new)>score(TWIN)` **0.945**，TWIN 在 FV5 仍被 flag **0.655**。这同时支持“某些上下文区别对表征有影响”和“当前 detector 在固定阈值下不具 validity specificity”。v12 §4.18 的 “no probe separates conflict from twin” 与“all probes read form”绝对表述需纠正。

**整改：** 精确报告两个维度（成对方向/可分性 **和** false-veto/FV5）；用 “none meets preregistered VALIDITY_TRACKED gate” 取代 “no probe separates”，并显著保留 SecJev L11 的部分上下文敏感性。不得从 ARM_SHORTCUT 推断内部没有关系信息；撤回“represented-but-unused 已证明”的处理是正确的，但同样不能倒推出“validity never represented”。

### P1-1｜G2 移植的因果**效果**与移植状态的“shortcut 判断语义”仍未分离

G2 在 kev-4B 的 104 个跨组 cells 中 53 个 joint repair、M1 53→1 own-round 对照、M2–M5 L11 attention 的条件性充分性、M20 9/14 donor 部分必要性均为**有限干预结果**。但移植 donor 与 host 的上下文、内容、关系不同；M23 没有对同 donor 的 valid/TWIN 中间状态做匹配的 swap-in/out 自然路径实验，不能断言植入的状态“就是 shortcut judgment”或已识别完整 partner relation 的传递环节。

**整改：** 标题与贡献改为“layer-11 readout-positive span states causally affect the readout/decision under these patches”；`recognition` 仅为 readout-positive 的重新定义是合适的。保留原始 G2 scoped PASS，不升级为自然 circuit、认证规则中介或修复防御。

### P1-2｜创新性门槛尚未过：shortcut 与 evidence-patching 已有相近先例

相关先例至少包括 2026 年：Yan et al., *Spurious Rewards Paradox* (ICML, mechanistic path patching and shortcut circuit), https://proceedings.mlr.press/v306/yan26f.html；Buzato et al., *On the Role of Supporting Evidence in LLM Reasoning* (EMNLP, gold-vs-counterfactual supporting passages and activation patching), https://aclanthology.org/2026.emnlp-main.1562/；Feng et al., *C2PO: Diagnosing and Disentangling Bias Shortcuts in LLMs* (Findings ACL), https://aclanthology.org/2026.findings-acl.1226/；TrustJev (arXiv 2610.34826, structured policy/evidence supervision), https://arxiv.org/abs/2610.34826 。

当前最小增量是**特定 typed vote 规则 + matched same-span context counterfactual + 原生三动作误拒 + 旧 G2 局部状态干预**，不是新方法、跨架构归纳、已识别的自然 shortcut circuit 或防御。作者 NOVELTY.md 已记 `NOVELTY_NOT_YET_PASS`，本审计不将其改为 PASS。

**整改：** 竞争矩阵增加这类直接 precedent，按 `prior question / counterfactual / causal isolation / security endpoint / what A461 adds` 明确差异；若希望更强贡献，再考虑互补的关系扰动与真正外部持出分布，而不是为凑轮次继续 GPU。

### P1-3｜统计单位和跨模型外推必须始终限制

124 scene 只属于 17 个 source groups，且都来自同一 simulator；两模型同 kev 家族、使用相同场景。行为效应是**配对的描述性结果**，非 124 独立真实世界样本。被拒的合法 TWIN 出现在 kev-4B **14/17** groups、SecJev **9/17** groups；这个跨组计数应与 45/124、15/124 同时报告。SecJev 14/14 的条件分母小且依赖原 new-rejected 选择，不能写成一般可靠的“100%”规律。

**整改：** 明确 group-level cluster uncertainty 和 held-out 范围；不可声称跨架构复现或部署错误率。

### P1-4｜原生三动作安全分析需同步纳入 TWIN 的完整分布

V6 §4.17 Table S1 覆盖 M18/M22 的 old/new/SA/ROUND/OUTSIDER，而 M23 的 TWIN 新臂仅以“false veto 45/124、15/124”总结。独立核验还显示 TWIN 的完整行为是 kev-4B reject/accept/wait **45/72/7**，SecJev **15/56/53**，而 Gold 是 accept **102** / wait **22**，因此除了误拒，还有 accept/wait 混淆，需明示，不能仅报道 false veto。

**整改：** 补充 TWIN 的 Gold×pred confusion matrix、group breakdown，遵循现行安全评价标准。强调规则引擎在该构造任务可精确求解；结果仅 S2 性质、无防御、无部署。

### P1-5｜独立复现和资产链尚未闭环

V6 的 M1–M22 `RECOMPUTE_MECH_R1` 为作者原脚本 22/22 exact equality，不是独立验证；历史 M17 v1→v1.1 在运行后修正仍需保留；机制 captures 发布私有 Release，M23 captures 仍在服务器；M19/M21 的 `head.pt` 未发布。GitHub 上的 SHA256SUMS、日志与回执可供核对，但本审计未访问所有 release bytes、server captures、head tensor，也未把 PDF/DOCX 完整渲染校对当成已验。

**整改：** 写明 reproducibility ceiling；若要外部独立复现，建立 M23 captures 可取回的完整 hash 路径，依授权提供 `head.pt` 的可再导出脚本或不可发布理由，并安排真正独立算法与布局核对。不得将日志 `ALL_EQUAL` 等同科学结论 PASS。

### P2-1｜只做过一种 partner 对照，仍有可行但未执行的正交对照

G23 CPU 门已证明 PARTNER_BLOCK **124/124** 场景可构造，PARTNER_AUTHOR **23/124**；M23 只做 PARTNER_ROUND **124/124**。后者在 **4/124** 场景还使 accept→wait 的 quorum/Gold 细分改变（G23 显示 120/124 的 Gold 等于旧 Gold）。不构成实验无效，但阻止把单一 one-token edit 泛化为“任何 context validity edit”。

**整改：** 将三种 family 的 executed/not-run 明确并列，解释 4 个 quorum 变化样本；如坚持唯一内部关系解释，再做预注册独立对照，否则不强制 GPU。

### P2-2｜文稿修订与审计状态应避免历史快照混淆

V6 `AUDIT_RESPONSE.md` 的历史行 “No new audit has been triggered” 在最新 `0170b699` 用户触发后已不是当前事实；`README` 的 status 于触发后已修订，需将其他历史快照标明归属时间。M-E 历史段还保留 v4 “represented but not used” 概述，虽 V6 段落已撤回，读者易误读。

**整改：** 添加明确截至 2026-11-01 的 V6 audit verdict 指针；保留修改前证据链，不覆盖预注册实验与原始数据。

## 三、保留的可靠结论及裁决边界

1. **原始 M23 行数、native 行为与主要 error counts：独立重数一致。** 原始 248×2 行，124×2 对，各 17 groups；GPU 回执各 248 physical forwards、0 denied、两批 128/120，且在设计预注册提交 `5bd58f6` 后由结果提交 `543b259` 归档。这支持执行和结果记录的可信性，但不等于独立 GPU 重跑。
2. **M23 falsifies validity-specific reading of the old M18/M22 monitors at the reported thresholds**；撤回“已表征但未使用”是方法论上应有的纠错。**SecJev L11 的部分 context sensitivity 不应删去。**
3. **G2 scoped causal transplant result continues to stand**：不是完整自然因果机制或可部署防御。M1–M5/M20 仅为有限位置、模型、来源组、控制条件下的局部充分性与部分必要性。
4. **S2 security finding survives**：构造场景中出现真实冲突漏判与合法 TWIN 误拒，须用全部三动作和规则 Gold 正确表达，不能外推到真实系统。
5. **Novelty remains `NOVELTY_NOT_YET_PASS`**；没有新的论文级无条件 PASS。

## 四、一次性返修验收（不自动触发循环审计或新的 GPU）

- P0 文稿：全文搜改 `does not check / ignores / never depends / no probe separates` 等过强表达；对 `ARM_SHORTCUT` 与 partial sensitivity 的双重含义进行明确说明；将标题/摘要/贡献限定为行为和局部移植效果。
- 数字与误差：加入 TWIN 三动作 Gold×pred、14/17 与 9/17 source groups、4 个 quorum 变化，区分 40/14 new-recognized 条件分母和全 124 分母。
- 创新性：更新直接相邻 prior work 矩阵，保留 `NOVELTY_NOT_YET_PASS`，不宣称唯一 shortcut mechanism。
- 复现：将未独立核验的 captures、head、PDF 布局写 UNKNOWN；独立重算和模型前向重跑明确区分。
- 若作者放弃强“内部完全不使用关系”结论，**以上主要是证据与文字边界修订，不强制重新运行 GPU**；若坚持强因果机制，则先预注册 orthogonal PARTNER_BLOCK / PARTNER_AUTHOR 和 matched-state mediation，必须经原有 CPU/GPU 准入，而非直接启动。

**最终审计裁决：`PAPER_AUDIT_REVISE_REQUIRED`，P0×2 / P1×5 / P2×2。** 与 V4 的审计不同，V6 的核心新增 M23 native 数字经直接独立重数获支持；主要阻断点集中在“行为反事实现象”到“内部完全无有效性检查/确定表征语义”的推理跳跃及创新性门槛，不是实验作废。原始实验、旧版文件、预注册、历史 PASS 全部保留。
