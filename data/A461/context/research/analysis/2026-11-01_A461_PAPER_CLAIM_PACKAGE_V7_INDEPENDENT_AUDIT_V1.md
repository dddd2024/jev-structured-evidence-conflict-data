# A461 PAPER_CLAIM_PACKAGE_V7（v13）｜论文级独立复核与投稿适配审计 V1

**日期：** 2026-11-01（美国东部时间；源仓库同日）
**冻结标的：** dddd2024/jev main 中 PAPER_CLAIM_PACKAGE_V7；论文内容提交 101aa8409e5adba25a3ebfd0d45a227ab3eea7cb，V7 触发 46e3b35cd3d65d00f6650d55d6ad15b8418975c4，SHA256SUMS 维护 a182e1906ffe747ebd9092a0b33a4e62a0e4507d。
**执行：** 按用户最新要求，对已正式触发的 V7 论文包进行一次集中审计；并对不产生新重大创新时的投稿适配性作独立评估。不得误称为第三方同行评审或独立 GPU 复现实验。

## 裁决

**PAPER_AUDIT_REVISE_REQUIRED（P0×1 / P1×4 / P2×2）**；限缩的 M23 原生行为计数及 V3 G2 既有 scoped PASS 不撤销；**NOVELTY_NOT_YET_PASS**；**自然关系检查机制 NOT_IDENTIFIED**。V7 文本明显解决了 V6 的两个过强机制表达 P0，但没有产生新的机制实证贡献，因此不授予“一区竞争力已达成”或“完整机制已找到”。

**独立核验边界：** 本次直接从 GitHub 读取 V7 README、AUDIT_RESPONSE、CLAIMS_EVIDENCE_MAP、NOVELTY、LIMITATIONS、REPRODUCE、generate_v13.js/v13_edits.py；对 M23 kev-4B 与 SecJev 两个 raw_native_logits JSONL 逐行解析 native certificate_action 三 logits argmax，按 target_scene 配对并统计 17 个来源组。未调用 GPU，未访问/逐张量验证 4.1GB captures、M23 服务器端 captures、head.pt；未独立渲染/逐页检查 DOCX/PDF；未验证全量 SHA256SUMS 或重新执行作者的 22/22 复算；未核验 AUROC/CI 的张量级训练路径。不可将这些未核验事项标注 PASS。

## 直接原始数据重算（与 V7 相符）

| 独立项目 | kev-4B | SecJev-0.8B |
|---|---:|---:|
| raw 行数 / scene 对 / 来源组 | 248 / 124 / 17 | 248 / 124 / 17 |
| new native reject / accept / wait（Gold 124 reject） | 40 / 83 / 1 | 14 / 69 / 41 |
| TWIN native reject / accept / wait | 45 / 72 / 7 | 15 / 56 / 53 |
| TWIN Gold accept / wait | 102 / 22 | 102 / 22 |
| TWIN Gold=accept 但预测 reject | 33 | 14 |
| TWIN Gold=wait 但预测 reject | 12 | 1 |
| TWIN Gold=accept 但预测 wait | 0 | 33 |
| TWIN Gold=wait 但预测 accept | 3 | 1 |
| TWIN 错误拒绝来源组 | 14/17 | 9/17 |
| new reject -> TWIN reject | 37/40 | 14/14 |
| new non-reject -> TWIN reject | 8/84 | 1/110 |
| twin conflict margin > new | 88/124 | 101/124 |
| span、决策位置、总状态长度相同 | 124/124 | 124/124 |
| full token SHA 不同 | 124/124 | 124/124 |

因此，在**这 124 组同一构造模拟器、单一种 PARTNER_ROUND 编辑家族**内，“有效性变化没有可靠映射到模型拒绝行为”这一行为发现有直接的原生输出证据。此处的 SHA 是元数据对比，不能据此宣称整段输入逐 token 只有一个变化已经在本审计独立验证。有效统计单位不是 124 个彼此独立的现实部署事件。

## P0（论文创新性与目标定位）

**P0-1：V7 的 novelty delta 仍以特定规则任务、同跨度反事实、三动作误拒和旧 G2 局部移植组成；相关机制/方法类已有直接先例。** 与 Yan et al. ICML 2026 机制 shortcut circuit、Buzato et al. EMNLP 2026 证据与 patching、Feng et al. Findings ACL 2026 shortcut 诊断以及 TrustJev 相比，本项目确实有可复核的狭义增量，但不具备已经证明的新方法、新电路、跨架构机制或防御。不能由研究任务规模或 30 页手稿推导为高水平一区期刊竞争力。整改有两条合法路径：（A）若不做新实验，将贡献严格写作任务特异的安全行为和局部因果分析，选择注重技术正确性的发表渠道；（B）若要主张机制突破，需另有可辨认的自然路径实验。路径 A 不强制新增 GPU，也不等于不能发表。

## P1（重要论文问题）

**P1-1：NOVELTY.md 仍混入过强的历史主张。** 该文件的“V6 smallest delta”段仍说模型由 form 而非 validity 决策、状态是 shortcut judgment；旧 M18/M21/M22 段说 conflict decodable but not used，甚至称 state carries a relation-validity verdict。V7 README 与 v13 正文已主动撤回上述机制断言，历史段应加 ARCHIVAL / SUPERSEDED 标识及明确 V7 覆盖规则，或替换为最新、可证伪的边界。否则论文主张与证据地图/创新性申明相互矛盾。
**P1-2：当前稿子 Related Work 的叙述仍有遗留风险。** generate_v13.js 在旧近邻比较中写“dissociation between represented and appended relational evidence”以及“the query side is not where the failure lives”；相关工作的创新描述说“byte-identical same-span counterfactuals”，而独立核验的是**追加 span 本身相同、前文 partner-round 改动、full-token SHA 不同**。建议统一表述为“same appended span, matched position and length, changed partner-round context”；把 query-side 因果排他结论缩为测试设定下的 decomposition/local effect，避免用因果机制语言包装行为结果。
**P1-3：外部有效性和统计单位。** 仅一模拟器家族、17 source groups、两同 kev 家族 checkpoint；124 pairs 有来源组相关性，且不同来源组大小高度不均，不能泛化为真实生产错误率或跨架构发现。加入 group-level 分布与 cluster-level 不确定性（若可从已有数据离线计算），明确哪些结论仅为描述性以及 false-veto 与 missed-conflict 两端同时出现。
**P1-4：独立复现仍有上限。** M1–M22 的 22/22 为作者脚本同路径复算，部分 M23 capture / head.pt 不可由本审计获得，最终 DOCX/PDF 未逐页独立核验。投稿需要诚实的 Availability/Limitations 与可运行的最小重算路径；对外承诺复现能力前须确认必要资产的授权与实际可取回性。未核验即 UNKNOWN，而不是伪造 PASS。

## P2（一般修订）

**P2-1：统计展示。** TWIN 三动作矩阵不要只汇报 45/124、15/124，完整展示 kev 的 wait->accept 3、SecJev 的 accept->wait 33 和 wait->accept 1；将 14/17、9/17 来源组与原分母一起展示，避免“14/14=100%”的无条件外推。
**P2-2：投稿格式。** 当前 v13 为 30 页手稿，不可直接假定满足 ARR 4 页/8 页、AISec Workshop 的限页，或某一 SCI 期刊格式；确定 venue 后再压缩并检查盲审、重复投稿、AI 披露及私有 repo 的复现政策。

## 竞争先例独立核对（本审计审阅官方摘要/政策，非逐页全文再审）

- Yan et al., ICML 2026：https://proceedings.mlr.press/v306/yan26f.html —— RLVR 的 shortcut circuit、path patching 与双向 steering。
- Buzato et al., EMNLP 2026：https://aclanthology.org/2026.emnlp-main.1562/ —— 支持证据的 gold/counterfactual passage 与 activation patching、四模型法律 QA。
- Feng et al., Findings ACL 2026：https://aclanthology.org/2026.findings-acl.1226/ —— 多 benchmark 的 bias shortcut 与反事实对比训练。
- TrustJev：https://arxiv.org/abs/2610.34826 —— 同类模型的结构化 policy/evidence supervision；这是预印本，不能称已经同行评审录用。

## 不出现重大新科学贡献时的合法投稿分层（不是录用保证）

1. **首选检验适配：TMLR**（https://jmlr.org/tmlr/acceptance-criteria.html）：官方强调 soundness + 对一定读者有学习价值，不要求新方法足够 novel。但需要拿出明确值得学习的因果控制与失败类型结论，不能仅将已有 shortcut 换场景。
2. **期刊备选：IEEE Access**（https://ieeeaccess.ieee.org/reviewers/reviewer-guidelines/）、**PeerJ Computer Science**（以官方当期 author guidance 为准）、**PLOS ONE**（https://journals.plos.org/plosone/s/criteria-for-publication）：侧重证据充分、原始研究和适配性，前者仍要求区别于先前论文、技术正确，不能误当为容易录用；后者尤其重视可复现及原始研究。核实学校当期 SCIE/JCR/分区认可后再选择。
3. **会议路线：ARR short paper → ACL/EMNLP Findings（视具体 venue 接纳）**（https://aclrollingreview.org/cfp），或**下一年度 AISec Workshop**（2026 截稿已在 7 月 24 日结束；https://aisec.cc/）。短论文/负结果允许，但仍须有具体新知识；Workshop 正式录用、是否 archival、能否再投期刊须遵守官方重复发表条款。
4. **更偏应用安全期刊：Journal of Information Security and Applications**（https://shop.elsevier.com/journals/journal-of-information-security-and-applications/2214-2126），本方向相关，但若无外部授权场景/应用价值证据，适配风险高。

**强调：TMLR/Findings/Workshop 并不能自动折算“中科院一区 SCI”。分区须以学校认可年度、期刊 ISSN、Web of Science Core Collection/JCR 类别核对。**

## 终态边界

**V7 的两项核心机制过度外推已有实质性文字修正；新审计并未否定 M23 行为或旧 G2 受控移植效果。** 当前可以基于现有结果形成不声称自然机制、普适性或可部署防御的限定研究稿，并准备技术正确性导向的渠道。若以“已找到新的安全机制、满足高质量一区投稿水平”作为主张，仍不通过。此裁决是一次论文级集中缺口清单，不要求每改一个 P1/P2 再审一次，更不自动批准 GPU。
