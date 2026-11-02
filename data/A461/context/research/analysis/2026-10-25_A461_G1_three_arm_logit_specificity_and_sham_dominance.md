# A461/G1 新定量分析：三个真实输入臂之间的语义特异性，而非仅 old→treatment 的方向移动

**日期**：2026-10-25。分析级别：已经执行的SecJev-0.8B FP32模型原生logits的二次计算；**无新模型推理、无训练、无GPU、无TEST/CAL语料读取**。本轮数据原文件是G1真实103行、G0来源内独立Gold 65行、N1B 14行、native state token审计65行；所有Git blob与31个 `pair_key` 的完整计算值见同名JSON。独立复算共15项断言全部PASS。

## 1. 为什么原来的「19/20方向正确」不是足够强的机制证据

先前G2报告：20个旧动作正确、Gold应发生变化的样本，19个目标新动作相对于旧动作的logit差确实向新Gold方向移动。但是**这个指标没有排除追加任意合法新记录本身带来的分数漂移**。若`old→neutral`对照也使新Gold分数变大，不能仅凭`old→treatment`变大说模型已理解处理语义。

本次因此直接使用冻结G1真实三臂：

- **old**：旧source state，旧Gold动作；
- **treatment**：向同一state追加一条合法、确实改变source Gold的规则相关事件；
- **neutral**：向同一state追加不改变source Gold的合法事件，来自真实前向的LANL N1或Twins N1B，而不是只在CPU上生成但没有执行的对照。

对于Gold-changing轴定义signed margin：

`M_A(x)=logit_x(Gold_new)-logit_x(Gold_old)`。

真实策略事实**相对于中性增量**的动作特异性为

`D_A=M_A(treatment)-M_A(neutral)`。

这也可写作`[M_A(treatment)-M_A(old)]-[M_A(neutral)-M_A(old)]`，即在**同一原始状态的输入行内**相消old的差分。正数代表真实规则证据比Gold不变的追加事件更推动正确新动作。此分数在同一原生问题、相同候选菜单与排序下才可解释，不将不同source家族的logit差值合并成一个通用效应尺度。

对于Twins T2新增冲突还定义原生`conflicting_vote`问题下的

`M_C(x)=logit_x(true)-logit_x(false)`, `D_C=M_C(treatment)-M_C(N1B)`；

`evidence_level`头同理比较新Gold 2与旧Gold 1的logit差，输出`D_E`。

所有这些都是**模型输出观察指标**，不是神经路径激活干预，不宣称因果归因。

## 2. 三条Gold-changing轴的对照结果

| 冻结实验轴 | 实际完成、来源Gold不变且state token等长的对照 | `D_A>0` | `D_A`平均值（logit） | 来源独立组数 |
|---|---:|---:|---:|---:|
| LANL-L1 第5次失败的调查阈值 | 9/9 N1 | **9/9** | **+3.343** | **3 day** |
| Twins-T1 达quorum后wait→accept | 6/6 N1B | **6/6** | **+1.857** | **6 run** |
| **Twins-T2 同作者异块投票冲突导致reject** | **4/6 N1B** | **1/4** | **+0.059** | **4个有对照run；另2个无对照** |

LANL-L1中九个 `D_A`均为正，范围`[+2.188,+4.518]`；Twins-T1六个都正，范围`[+0.933,+3.470]`。这表明同样采用合法追加记录控制时，模型**在这些冻结输入上**有可辨识的、相对中性臂的规则方向分数信号。其本身仍不意味着argmax一定正确：LANL-L1仍有5/9未升级，T1仍有2/5旧正确对未接受。

T2在四个等长中性三臂中只有一个run取得正`D_A`，其余3个非正（严格负数）。范围`[-0.451,+0.997]`，mean`+0.059`；其**唯一正样本run121**对总均值影响很大。T2另外两个Gold为`accept→reject_conflict`的`run100/run125`既没有执行N1B，也没有执行原N1，不可算进四组 `D_A`，其原N1静态state token长度与处理臂相差4。不得伪称T2 6/6拥有匹配控制。

**跨任务不能推断统一效应量大小：** LANL和Twins的策略动作、输入规模和候选内容不同；上述正负方向信息在各轴内有效，但均值之间不是同一个可交换总体。LANL仅3个来源day，不能将9条当9个来源独立replication。

## 3. T2更强的发现：SHAM中性消息本身使「冲突」和「拒绝」分数朝错误方向上升

将四个合法且state-token等长的T2 N1B输入逐来源run列出，其中N1B保持候选块、轮次、时间和kind，只把追加投票作者换成未在当前轮次投票的**新合法validator**；N1B来源Gold始终`C=false, certificate_action=wait`，而真正的T2 treatment Gold变为`C=true, reject_conflict`。四条N1B模型动作也都正确wait。

| T2 source run | old→处理：`M_C`变化 | old→N1B：`M_C`变化 | 真处理相对N1B：`D_C` | 真处理相对N1B：`D_A` |
|---|---:|---:|---:|---:|
| run101 | +0.464 | +1.539 | **−1.075** | **−0.451** |
| run105 | −0.193 | +0.342 | **−0.535** | **−0.146** |
| run114 | +0.351 | +0.662 | **−0.311** | **−0.163** |
| run121 | +2.539 | +0.441 | +2.097 | +0.997 |

定量后果：

1. 四个真正中性、旧Gold不变的N1B，使`M_C`在**4/4**组相对old变大；目标正确动作`reject_conflict`相对于旧`wait`的分数也在**4/4**组朝拒绝移动，虽然这些Gold仍需`wait`。
2. 正向真实冲突证据相对N1B的特异效果`D_C`为**1/4正、3/4负**，均值**+0.044**；`D_A`同样**1/4正、3/4负**，均值**+0.059**；`evidence_level`的正确级别2相对旧级别1的差分也**1/4正、3/4负**，均值**−0.098**。
3. 所有四个T2真实treatment仍预测`C=false`且动作`wait`，来源Gold则需要`C=true, reject_conflict`。即使某一行`D_C`正，正确冲突判断的`M_C`也没有跨过0。该正向信号仍不足以形成正确动作。
4. 这是比旧`19/20`更有区别力的反事实：**部分向拒绝移动的分数可以由不包含真实冲突的合法中性消息诱发；仅看old→new不能认定模型已经成功解析同作者、同轮、异块关系。**

目前不存在可接受的推论：“模型完全没有语义特征”或“T2在一般总体中语义敏感性精确为零”。四组DEV筛选样本很小，`1/4`为正的双侧精确符号检验即使假设公平独立也仅`p=0.625`，不支持统计性证明。中性与真实消息虽然总token等长，但author token身份、旧消息结构关系和可达位置有差别；这是**尚未排除的潜在原因，而不是已测定的机制**。

## 4. 新的研究方向排序与可执行CPU前置任务

**主方向保留但假设收紧**：`A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE`依然仅为**DRAFT_NOT_ADMITTED**。具体研究对象从笼统「方向正确但最终阈值欠反应」转为：

> SecJev对来源内合法的跨消息author×round×block冲突事件，能否产生独立于等长度Gold不变投票追加的语义特异性评分？若不能，是输入事件绑定/共享backbone隐藏状态没有形成所需关系，还是问题条件/Pointer QK候选读出未充分区分已成立与新形成的冲突？

**CPU工作，无GPU许可即可先推进，但需要并行执行所有权协调：**
- 为已运行四个T2 matched三臂登记`D_C,D_A,D_E`作为探索性诊断终点，保留全部old、处理、N1B的native request与SHA，不基于当前显著样本事后筛选。
- 对未覆盖的`run100/run125`两组quorum已满足的old accept→new reject，测试**仅允许来源中确实观察到的other round**的中性候选方案和正确Gold，连同完整原生token等长、格式位置和多问题菜单不变的双Oracle审计。此前有8个旧A428状态上的浅层Gold可行性，不代表已在这2条新G0样本得到合格候选。
- 先对照先例（SecJev源码/原文、entity state tracking、Gold不变增量下的状态更新/patching）；如需模型因果实验，再另立受控干预协议、停止条件、预算与用户GPU授权。Patch固定`conflicting_vote`问题行与候选选项，另一条`certificate_action`问题行单独测，不将两条独立问题输出错写成串行C→A机制。
- 新未见source run组需要能够排除曾见DEV、来源组相关和作者/字符串宽度等混杂。对于影响T2核心结果的两个旧accept情形，未完成等长对照前不得作机制特异性强主张。

## 5. 本轮档案和资源

本报告及机器可读的31个源内轴实例、15项严格一致性校验、源Git blob SHA记录于`research/analysis/2026-10-25_A461_G1_three_arm_logit_specificity_and_sham_dominance.{md,json}`，旧G0/G1/G2以及并行Agent正在更新的`G2_CORRECTED`原始文件**没有被覆写**。本轮为同一真实G1数据的独立再分析，没有再消耗模型forward/GPU或服务器运算；服务器与GPT Library双备份未由本会话另行核验。
