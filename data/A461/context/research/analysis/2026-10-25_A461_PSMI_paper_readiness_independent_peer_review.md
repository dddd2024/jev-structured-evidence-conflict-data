# A461-PSMI 论文成立性独立审稿意见（基于可验证G0/G1/G2证据）

日期：2026-10-25。审查标的：用户转发并行Agent的“A461 全链完成、完整成果足以支撑论文”声明；`dddd2024/jev`中原始G1 103条logits、G0 source Gold/对照、G2汇总与逐对输出、V1/V2实验协议、正式G−1记录；直接核查SecJev等原始论文。**本审查未能打开执行方Windows本地`F:\\jev\\paper_a461_psmi\\A461_PSMI_audit_paper_draft.docx`（连接设备离线且该稿未在GitHub）**，因此评价的是**论文实证贡献是否成立，不是那份DOCX的逐节内容和格式是否合格**。

## 总裁决

**已形成实质性的、可复核的模型行为观察结果和可作为探索性方法/案例审计报告的论文材料；尚未形成符合白盒机制/安全漏洞方向高质量同行评审论文的充分证据。** G1/G2“已完成”与论文结论“已验证创新”不得等同。正式建议状态：`EXPLORATORY_BEHAVIORAL_AUDIT_READY_FOR_DRAFT`；白盒因果/部署漏洞/泛化创新`NOT_ESTABLISHED`。可以写一篇限定结论的研究稿，但不得再称“全套机制论证已完成”。

## A. 已成立的事实

- `G1_REAL_20261025/raw_native_logits_103_requests.jsonl` Git blob `5b4a6903171d0a5848162a335530492f6e1a6046`，实际103条FP32物理forward日志；角色34 old +31 treatment +14 N1B +17 N1 +3 N2 +4 replay；4个replay与原primary的完整native token SHA、全部question keys/logits严格一致；修订执行收据PASS（原FAIL回执仍保留）。不是“只有CPU准备/没有GPU模型实验”。
- G2行为结果：旧臂正确的Gold变化主轴20条，正确新动作7、旧动作不变且新Gold错误13；19/20的**目标新动作与旧动作logit差变化方向**为正，另1条T2 run100为负。该19/20只是一项输出分数方向，不是“新增策略事实19/20已被识别”的证明，也不是19个样本执行动作正确。
- Twins T2六条（six distinct run groups: 100/101/105/114/121/125）：新状态源Gold冲突true，模型`conflicting_vote=false` **6/6**，`evidence_level`对source Gold 2 **6/6错误**，`quorum`判断6/6正确，`certificate_action`拒绝0/6（wait四、accept二）。所有六条动作和把**模型自身输出的**C/Q值代入来源策略规则的结果一致。这是**新增冲突识别问题与动作错误同时存在的表型**，不足以得出“已识别冲突、仅最后决策阈值失效”；也不能证明C问题的模型输出是A问题的内部因果中介。
- SecJev原文§3.1–3.2明确每个question `(state,q,candidates)`作为**独立因果渲染行**，共用backbone/LoRA/pointer scorer；C/Q/A问题不是先答C再答Q后答A的串行神经决策链。T1 run121模型C=false,Q=true,A=wait而Gold应accept，是**跨问题答案不一致的一个案例**，不能推断“动作整合模块故障”已定位。
- LANL L1 threshold：9个新Gold burst=true，模型burst true仅3/9、triage investigate仅4/9；全部5个动作未升级者burst也错。N1B原生14例全体动作错误4/14，其中old-clean严格clean→wrong为**2/12**；Gold-changing的old-clean子集为**2/9**，两个分母均合法但须显式注明条件和总体。N2 3/3 Gold保持且模型本轮均保持，但只证明本3条delta=1的结果，不能“彻底证伪过去所有时间因素假设”。

## B. 主要方法和统计缺口（提交正式安全/ML论文前需要修正）

1. **论文中心机制陈述超出证据**（MAJOR）。报告把19/20行动logit变化称“方向忠实、已读懂风险”，将13/20归于“阈值欠反应”。T2实际6/6在`conflicting_vote`问题本身尚未正确判断冲突；必须分开写**规则事实读取/跨消息关系绑定错误**与**动作读出可能不一致**两种候选。没有任何Q/K、MLP、隐藏态/LoRA因果干预；现象不能成为已经证明的白盒机制。
2. **核心许可否决格的配平对照缺失**（MAJOR）。T2六条中仅4条旧wait→新reject在正式G1执行了N1B等token中性对照；两条最重要的**旧accept→新reject（run100/run125）均没有执行N1B或N1中性臂**，原G0对应N1新/中性state-token长度差4。不能用4个`wait→reject`的matched证明已排除quorum满足时追加冲突的词表/位置/长度混杂。此前CPU影子计划可在103次预算内重排，但那不是已经执行的G1，**绝不能事后改写物理计划**。
3. **N1配平标签与资源叙述错误**（MAJOR-METHOD）。冻结manifest旧字段把`neutral vs old`而非`neutral vs treatment`作为等长判据，因而错报N1 `0/31`；真实是**29/31**（LANL L1 9/9、L3A 6/6、Twins T1 6/6、T2 4/6、T3 4/4）。已执行G1前17条N1全为等长的LANL15+T1两条。故“LANL来源契约内不能构造任何等长中性对照”若意指treatment-vs-neutral的token数则**是错误的**。等token总长度又不等于序列内位置/特征完全受控。需要冻结正确判据和原始执行角色。
4. **统计检验的配对总体不同**（MAJOR）。将T2处理6个错误与N1B零违例写成“六个同向 discordant 所以精确McNemar p=.031”，并不对应6组严格有中性臂的匹配比较：**只有4组**有实测N1B，对应4个treatment错误、4个neutral正确；若仅对这4组进行单纯的双侧精确配对符号检验，p=**0.125**，而非0.03125。6个旧正确→新错误可以另作不同Gold下的配对正确率描述，但不能冒充6对`treatment vs N1B`对照；选取DEV stratum和旧A428复用来源组也限制了任何显著性推广。T2是6个不同run组，但其中run100/125在A428已接触过；LANL15条只有3个day group且这些组也全部见于A428。
5. **所承诺的“单调性违规”与观察的under-response不同**（MAJOR）。V2冻结协议明确`failed_to_change`**不是**反向单调性违例；大部分13/20是未响应，不是方向逆转。严格目标动作-vs旧动作logit的反方向变化仅1条T2 run100（约-1.497），该条恰没有等长中性控制。论文标题、摘要与创新主张不应把13/20直接标成已证实strict sign reversal。
6. **原G2独立计算代码存在第三Oracle的非独立子门**（MODERATE）。N2 `old_state=next(x.native_request.state for same pair_key)`因G0中N2一键只有一条`retimed`，实为把同一个修改后state当old，得到old Gold与new Gold恒等；另一次独立分析确实经撤销L1追加事件、逆向N2时间编辑两条路径重建旧状态，**3/3 Gold真正稳定**，故这是验证方法错误而非N2结果反例；原G2该段需要勘误/重跑且保存正式新回执。nonregression的`logit_new(Gold)-logit_old(Gold)`不是Gold-vs-最强竞争动作margin，须修正指标名和解释。
7. **外部有效性与“为什么不用规则引擎”问题**（MAJOR）。单一SecJev-0.8B、单精度、从DEV选出的31轴、30个不同原始scene/11个source group；既没有新的盲法未见source-group验证、其他尺寸/原生Kev/普通分类器对照，也没有证明攻击者控制这些认证投票/登录事件或真实部署allow/deny效果。Twins是收到的投票证据策略，LANL是事后logon triage，不是agent guardrail的越权成功率。显式规则的Gold由程序确定，**确定性规则引擎为可达100%的必要对照**；不能以模型执行显式规则错误自动证明在此问题必须使用模型。
8. **创新性现有文献竞争**（MAJOR）。SecJev原作者论文已经公开相同source policy和模型架构（https://arxiv.org/html/2610.03073v2）；*One Word Opens the Gate*在typed guardrail比较中发现格式与选项干扰及规则抽取可消除某些攻击（https://arxiv.org/abs/2610.12292）；*Do Language Models Track Entities Across State Changes?*（ICML2026，https://proceedings.mlr.press/v306/tang26ah.html）已深入研究状态变更的实体跟踪内部机理；*Monotonicity as an Architectural Bias for Robust Language Models*（https://arxiv.org/abs/2602.02686）已讨论单调性。当前`NOVELTY_DELTA_TESTABLE`只证明先例搜索后**实验值得尝试**，不等于已证明的论文新增机制。方法和安全语义增量必须正面与这些研究对比。
9. **手稿未经直接阅稿**（SCOPE）。DOCX路径只在并行Agent Windows机器`F:\\jev\\paper_a461_psmi\\A461_PSMI_audit_paper_draft.docx`的外部文本中出现，GitHub未存该文稿，远程设备`dd` Offline。本次不能替代逐节审稿或证实“postcheck0 errors”；后者即使正确也只是文档结构检查，不是论文科学验收。GitHub Issue #2仍`open`，不能以Agent文字宣称已关闭issue。

## C. 推荐的安全论文主张和阶段

目前可以负责任地写：**“在SecJev-0.8B的两个来源内显式策略任务上，我们使用冻结CPU双Oracle与真FP32反事实测试，观察到新增证据下的行为响应不足。Twins中六个独立run场景的新增冲突投票没有让模型冲突问题和证书动作问题得到正确Gold，而相应已观测到的quorum问题通常正确；该现象提示跨消息关系绑定/证据更新的行为鲁棒性问题。局部中性等长控制存在，但最关键两个quorum已满足时的否决格子仍缺失匹配中性臂。未做内部因果定位或跨来源确认。”**

**不允许**：称`19/20`证明模型已成功读入相关证据；称6/6 T2已定位“动作阈值电路”的因果故障；称中性配平31/31或核心两条有token配平；称当前已获得通用Jev模型漏洞、攻击者可达fail-open、系统性白盒因果电路或可发表的独立创新点。

**可投对象判定**：
- 课程项目、技术报告、诚实标注探索性的预印本：材料**足够撰写**，需依本审核实修改手稿措辞；
- 有竞争性的同行评审安全/ML或白盒机制论文：**尚不够**。至少应先完成G2评估勘误、新Gold不变匹配控制、未见来源组独立验证，以及同一原生问题行内双向隐藏态/Pointer QK/LoRA因果干预（或给出足够强且明确新颖的统计/方法贡献，不应假称白盒机制）。

## D. 下一步优先次序（本报告不批准/不启动GPU）

1. **现在即可做（CPU+已有数据）**：冻结修订后的G2完整多头统计`C/Q/A/evidence_level`、每组run的Gold与模型margin；修正N2第三Oracle和N1统计，核对论文摘要/主表对照计数，给出严谨的matched-T2四组分析与无法配平的两条清单；执行方DOCX上传到可访问位置后逐节比对这些不可误写的事实。
2. **独立G−1文献与新CPU编辑资格**：正式命名为`A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE`（目前**DRAFT_NOT_ADMITTED**）；验证来源内新投票与旧支持票的author/round/block关系，预注册时间、token位置/长度、同作者重复样本、逆序编辑等SHAM；先得到Q已满足的accept→reject两条核心格子严格配平控制的有效方案。
3. **再谈新GPU**：未使用过的source-run组中重现严格policy Gold/action差异、至少一种合理baseline比较；取得独立的新forward预算和授权后，在固定`conflicting_vote`单问题/candidate语义下做充分性/必要性双向activation patch，再对action独立问题复验并区分共享backbone与Pointer scorer影响。若无来源可写、Gold确定、严格模型阳性或可解释因果效应，及时降级为行为方法论文，而非硬凑防御。

## 研究证据来源

研究repo：`dddd2024/jev`；原执行归档commit `ca9eb88eda0339e412da74c67bae69c216af634b`；G1 raw Git blob `5b4a6903171d0a5848162a335530492f6e1a6046`，G0 Gold Git blob `24526c643434544b9a02587abc2d57e2c13ef627`，G2 `analysis.json` Git blob `e33f2306e5c4da8951993f438731a6a878ea7cba`；独立多头核算`research/analysis/2026-10-25_A461_REAL_G1_103_multihead_conflict_recognition_root_cause_screen.json`、同名MD及回读收据；冻结V2协议`research/experiments/2026-10-25_A461_PSMI_CPU_GATE_AMENDMENT_V2_ENDPOINTS_AND_CHRONOLOGY.json`。

本次审查使用已存在的真实G1/G2/G0证据+原始外部先例；没有新的模型运行、GPU、训练或TEST/CAL读取；不会代替并行Agent修改原始模型实验文件。**用户所述DOCX未能打开，服务器双端备份未由本审查核验。**
