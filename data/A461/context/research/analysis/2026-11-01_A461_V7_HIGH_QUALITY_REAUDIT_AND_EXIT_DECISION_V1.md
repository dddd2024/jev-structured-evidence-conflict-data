# A461 V7｜高水平论文重审及“退出机制深挖”决策审计 V1

**日期：** 2026-11-01。**审计对象：** GitHub `dddd2024/jev` 的 `PAPER_CLAIM_PACKAGE_V7`（v13；论文内容提交 `101aa8409e5adba25a3ebfd0d45a227ab3eea7cb`），现行治理标准与最新已归档 M1–M23。**证据截至：**本次核查前主分支 `4acf7de14a1dcb63e7058e81e987f68a57c66fd9`；此次独立审计是研究去留专项再审，不改写已冻结 V7/V6/V3 裁决。

## 一、总裁决（不与 V7 独立审计混淆）

- **技术可信性：SCOPED_EVIDENCE_SUPPORTED**。M23 原生三动作行为和 G2 kev-4B 跨组局部移植效果得到本次直接再次重数，与既存审计相符。
- **自然因果机制：NOT_IDENTIFIED**。不能由整段或 L11 patch 的局部充分性/部分必要性、round 敏感性，唯一确定模型对 author × round × block × vote 的自然关系核查、完整 Q/K/OV/MLP 中介或 C→A 路径。
- **新颖性：HAS_LIMITED_DELTA_BUT_NOVELTY_NOT_YET_PASS**。“零创新”不成立；但 task-specific security error + matched same-span partner-round twins + typed action + local patch 的新增知识仍未显示具有高水平一区竞争力所需的强独特性/重要性；不能以另一个领域应用既有方法替代直接先例的技术比较。
- **V7 论文：保留上一轮 `PAPER_AUDIT_REVISE_REQUIRED`（P0×1/P1×4/P2×2）及已列问题**。这次未看到修订后的新稿，不重复“发明”第二套 P0 数量；V7 的标题/摘要已限定行为边界，但 NOVELTY.md 的历史段仍可读到 `decodable but not used`、`shortcut judgment`、`form rather than validity` 等超范围断言。
- **当前决策：CONDITIONAL_CONTINUE / HOLD_UNBOUNDED_GPU**。不宣布“马上放弃”，也不默认开启 M24；只有在最后一个高信息价值、经独立 Gold 和真正可区分预测的实验包被证明可行、有明确 novelty 增量且获有效 GPU 批准时，才继续机制深挖。否则转为“有限贡献实证论文”的稿件收束。

## 二、本轮重新从原始 JSONL 独立计算（非复述旧审计）

1. G2 K-C raw `research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/G2_K4B_KC_GPU_R1/G2_K4B_KC_GPU_RUNS/ATTEMPT_R1/raw_native_logits_k4b_kc.jsonl`; blob `19d3a06c27953b1f2b4dcd2770394d28741a69fd`；417 条。按 `cross_group === true` 和 `certificate_action` 的三 logits argmax 以及 `M>0` 重计：`patch_kc_main_all` C/R/JOINT=65/62/**53**（n=104）；`patch_kc_sasham_all`=0/0/**0**（n=104）；`patch_kc_doserand_all`=12/5/**0**（n=104）；`patch_kc_unrecognized_all`=0/0/**0**（n=40）。104 crossed cells 共享 8 个 hosts，不是 104 个独立任务。
2. M23K raw `research/rounds/A461_MON_M23_TWIN_PROBE_GPU/M23K_GPU_R1/raw_native_logits_m23k.jsonl`，blob `7ffebade1d6339340a466bd5032f93f0a992ecc3`；248 条，124 个 scene pairs、17 个 source groups；new reject 40、合法 TWIN reject 45、new-reject→TWIN-reject 37，错误拒绝覆盖 14/17 个组。
3. M23S raw `research/rounds/A461_MON_M23_TWIN_PROBE_GPU/M23S_GPU_R1/raw_native_logits_m23s.jsonl`，blob `6e2d9a8e1beeac1507433ce3a68a0a4f23a3ddce`；248 条、124 pairs、17 groups；new reject 14、TWIN reject 15、new-reject→TWIN-reject 14，覆盖 9/17 个组。
4. 两模型配对元数据的 span、决策位置与总状态长度均 124/124 相同；full-token SHA 不同，不能称全文输入 byte-identical；被固定的是追加证据 span 与其位置。17 个组的 scene 数范围 1–16，仍存在明显组大小与独立单位问题。
5. 本次未重跑 GPU、未独立逐 tensor 验证 4.1GB captures/服务器 M23 captures/head.pt；未逐页渲染 v13 DOCX/PDF；M23 probe AUROC/CI 来自现有结果，非此次原始 tensor 重算；最新相关工作以官方论文摘要和作者报告核对，未重新阅读所有完整 methods/results。全部须标 NOT_INDEPENDENTLY_VERIFIED。

## 三、为什么还不足以得出“一区已就绪”

- 现象类别（shortcut / patching / evidence-use failure）具有强直接先例：Yan et al., ICML 2026, https://proceedings.mlr.press/v306/yan26f.html；Buzato et al., EMNLP 2026, https://aclanthology.org/2026.emnlp-main.1562/；Feng et al., Findings ACL 2026, https://aclanthology.org/2026.findings-acl.1226/；TrustJev arXiv:2610.34826。当前任务特定增量可靠但不等于独有机制或普适定律。
- 原生安全 Gold 属于构造的 Streamlet 风格规则任务；没有自动获得真实部署 S4 或跨架构泛化资格。
- SecJev L11 的部分 relation/context sensitivity（M23 AUROC_pair=0.698）妨碍“内部根本没有核查”这类绝对结论；G2 donor state 没有在 Gold 翻转的同场景 twin 之间进行受控 natural mediation swap。
- 既有 V7 V1 审计未完成的 NOVELTY 与 related-work 文字一致性、来源组统计和独立资产验证仍需按原清单一次性处理。

## 四、退出标准：研究路线退出 ≠ 论文可投稿 ≠ 论文应废弃

此为**推荐的 A461 研究决策规则**，不自动修改既有治理政策，亦不新增独立审计触发点；与既有 `JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md` §5 一致。

### A. 新机制研究“继续准入”必须同时满足

1. **贡献存活：** 针对最相近论文，写出至少一个尚未被它们解答、若验证将改变科学理解的可证伪增量。仅换模型/重新命名 head/增加数据行数不算。
2. **可辨认：** 给出至少两种相互竞争的自然机制（例如 H-ENC vs H-READ vs H-CTX/INTERACTION），在 Gold 合法、token/位置/幅度与上下文对照充分时对同一原生安全端点提出**不同的预注册预测**。阳性和阴性两种结果都应改变机制结论。
3. **现实可执行：** CPU 构造性核验 Gold 双 oracle、严格配平/可解释的不可配平、来源组独立性、功效/不确定性和样本泄漏；合理的 host/donor holdout；明确成本、硬预算、停止条件；真实模型前向须具备用户有效许可。
4. **安全端点闭环：** 原生 `certificate_action` reject/accept/wait 与独立 Gold，既检查漏拒，也检查合法 false veto 和其他 typed 输出副作用；不能以 readout margin 单项上升替代安全收益。
5. **剩余信息价值：** 下一次实验不论成功或失败，都能保留或排除一种实质候选机制，或明确改变“能否达到高水平论文”的判断。只是多一个 M 编号、增一组类似 patch 不满足。

**任一项缺失时，不启动新的机制 GPU，状态为 HOLD_RESEARCH_DESIGN 或 PIVOT_TO_PAPER；不能把无授权或纯预算阻塞误当成科学证伪。**

### B. 建议的“最后一个有界攻关包”（不是保证成功、不是自动 GPU 授权）

- **实验目标 1：关系有效性的正交检验。** 在 M23 PARTNER_ROUND 之外，先利用 G23 的 CPU 已知可构造性检查 PARTNER_BLOCK（标注 124/124 候选）及条件适用的 PARTNER_AUTHOR（23/124 候选），重新核验 Gold、身份、位置、token 等长与词面混杂。比较 Gold 改变与形式/位置保持的原生 C/A/TWIN 三动作，而非再运行一个无关 probe。
- **实验目标 2：自然中介的排他性检验。** 对经过 Gold 匹配的 valid/TWIN 或其他语义反事实状态，设计正向安装/反向移除/回补，对 attention/MLP、option-token 与 decide-token 的关键自然路径做可辨认的组合干预；同等剂量 sham、负面合法场景、完整三动作输出。测试应使至少两个竞争解释得出不同结论。
- **限制：** 这两个目标是**一个研究决策包内最多两个彼此正交的确认性问题**，不是承诺各自动用 GPU，也不能未经可行性检查宣称预注册已完成。若 CPU 就显示不可识别或直接先例已经覆盖，跳过 GPU 直接退出。新模型或新模拟器只能服务事前有价值的假设，不自动增补成“下一轮”。

### C. 停止深挖机制并转向已有成果投稿（PIVOT_TO_PAPER）的触发

- 当前现象与局部效应继续成立；可以给读者一个超过“已知 shortcut 换个场景”的**诚实且明确的狭义新知识/可复核安全教训**；
- 经直接先例比对及 CPU 可行性检查，剩余机制假设不能构成有信息价值、可区分且资源许可的测试；**或**有界正交检验已得到可信负结果，全部强机制候选应降为 NOT_IDENTIFIED；**或**即使假设成立也不能显著改变论文贡献/适配性；
- 后续科学探索的边际信息价值不足以抵消成本；先在原始证据上补统计、复现和文稿一致性，而不是为了凑正结果继续开发 M24、M25。

**重要：负结果若样本不足/干预无力/控制不合格，应标 UNKNOWN 而非“证伪”，但若又没有可行改进路径，则同样可以在资源与机会成本意义上退出，不能冒充机制已被推翻。** 此处没有“必须做满两次失败 GPU 才退出”的机械规则。

### D. 停止当前论文方向、仅归档（ARCHIVE / REJECT_CLAIM）

- 独立 Gold、数据 provenance 或原生主结果被实质性推翻且无法修复；或
- 直接已公开先例已经包括**全部**最小新增贡献，严格收窄之后仍不能告诉任何目标读者新知识；或
- 关键安全端点与声称的研究问题不相干、外部意义无法合理表述，甚至局部受控因果结果也不可靠。

**以上才是放弃这篇论文的条件。它们不等于当前已满足。**

### E. 转向投稿的提交门（PAPER_SUBMISSION_READY）

- 主张仅包括已验证的 M23 行为、G2 条件性移植与客观边界；所有直接先例矩阵更新，突出真实的独特安全教训；
- 计算完整三动作 Gold×pred、source-group 统计/不确定性、描述性 vs 确认性结论；清理 NOVELTY.md 等过强旧措辞；
- 重要资产能按合法许可提供可验证的独立重算路径，做最终手稿与图表检查；无法分享的 assets 清楚声明复现上限；
- 确定匹配期刊审稿政策和学术收录/学校分区要求。TMLR 的科学正确性与读者兴趣是例子，不代表已经录用，更不等于中科院一区。

## 五、当前具体判断

**不批准无条件继续 M 系列机制搜寻。建议先做一次仅需文献/旧数据/CPU 的 Go–No-Go：** 在一个研究决策包中明确“正交关系反事实 + 自然中介”的最小可识别问题及先验分歧。若合格，再视独立授权对有界 GPU 实验做决定；若不合格，立即关闭当前深层机制路线，保留原行为/局部干预成果，按既有 V7 清单完成限定范围论文。

**不能把“现在尚未找到机制”直接判为“已经证明机制不可找到”；也不能把“创新性没有 PASS”直接当成“零创新”或“投稿必定失败”。**

## 六、治理说明

本报告是根据用户明确要求的再次审计及退出标准建议，**不是对 `JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md` 或唯一审计触发政策的修改**。不设日常独立复审轮次、不生成 GPU 许可、不自动重新运行模型；既有 V7 V1 审计优先保持其冻结审计事实。