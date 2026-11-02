# A461-MECH-M5 — Context Dose vs Source-Specific Causal Contribution
## Design draft V1 | 2026-10-28 | DESIGN_ONLY / NOT_PREREGISTERED / NO_GPU_ADMISSION

**任务状态**：研究设计草案，不是正式冻结预注册、CPU G−1 PASS、GPU 执行许可或 M5 的实验结果。主线继续 A461 合法新增冲突证据遗漏的因果机制研究；不创建新研究方向，不撤销 M1–M4 的冻结裁决。

**主问题**：M4 的 L11 attention write 主要依赖 CONTEXT + OTHER_ITEMS 的 donor patch 贡献，究竟因为这两个类的真实证据特异性，还是因为它们的张量范数较大、提供了更大的通用激活剂量？在同样的作用量下，真实供体的上下文更新是否仍优于错配第三供体/非信息方向？

### 先验和硬边界
- M4 R1 真实执行 2956/2956 forwards、24/24 batches，208/208 full 与 M3 all bitwise 相等；S(full)=51/104。
- M4 冻结裁决 LOCUS:CONTEXT+OTHER_ITEMS（补丁内 NEC：drop OTHER_ITEMS S=8、drop CONTEXT S=23；无单类 SUF），vswap PARTNER V_NONE（S_V=0）、drop PARTNER S=41。
- OTHER_ITEMS、CONTEXT 的 donor median class norm 分别约 4.66、3.56，大于 PARTNER 等 1.2–1.9 数量级；补丁内必要性可能只是“激活剂量”。
- new 与 ROUND 的 pre-span keys/values token 完全一致；新增投票的 round token 位于 span 尾部，specificity 可能来自 donor 的 span-side Query/gate。**本轮不能用 bulk-class patch 自身推论 bulk 内容编码冲突，亦不能推断 host natural source-edge necessity。**
- 104 cells 共享 14 donor groups 和 8 hosts，不可当作 104 IID；单 kev-4B、一个 simulator family，不能宣称普适性或真实安全攻击。

### 相互竞争、可证伪假设
- H_dose：M4 drop OTHER_ITEMS / CONTEXT 的损失主要由激活范数/剂量减少解释，匹配剂量的错配供体或非语义方向可以产生近似修复。
- H_source：控制更新范数后，合法 donor 的 bulk contribution 显著优于错配第三 donor 和随机方向；说明其向量方向/条件化内容有额外作用，但仍需更细语义控制，不能直接证明“证据真实性”。
- H_gate：new 与 ROUND 的方向性差别在匹配剂量后仍存在，符合 span-side Q/gate 条件化而非 pre-span 内容直接变化的解释。
- 零结果及混合结果必须保留，不以 post hoc 选择配对/阈值制造阳性。

### 操作对象及符号
- 冻结 M4 的 14 donors × 8 hosts，排除同来源后的 104 cross-group cells；同一 kev-4B 权重、Gold、token identities、span definition。
- 第 11 层 o_proj 输入，31-token append span，按 M4 已验证的 key-class contribution 分解；目标始终是宿主自身的 forward，模型权重不变。
- 每个源 s∈{donor NEW, donor ROUND}，令 z_H 为 host NEW 的 L11 o_proj-input，z_s 为 donor 相应 span 激活，z_{H,C}/z_{s,C} 为同一 key 类 C 的激活贡献；Δ_full=z_s−z_H，Δ_C=z_{s,C}−z_{H,C}。BULK=CONTEXT+OTHER_ITEMS。
- 对相同形状 [span, heads×head_dim] 的张量，在 span 全体元素计算 Frobenius 范数；Dose_C= z_H + α_C Δ_C，α_C=||Δ_full||_F / ||Δ_C||_F（无标签、逐 cell/source 计算）。若零范数、非有限、缩放超出 CPU 预冻结安全范围，一律记录不可构造，不偷偷裁剪或填零；各臂有效覆盖率在 GPU 前冻结。
- 三方错配 donor D' 必须与 host 和原 donor 不同来源组；只能用冻结的上下文身份/长度/轮次/角色匹配规则选择，不按 logits、成功率或距离上的实验输出事后挑选。对于 D' 按同样范数进行剂量匹配。
- 随机方向臂使用固定 seed、同一维度的确定性单位方向；不推断其必然代表自然模型内分布；需报告 OOD 风险。

### 候选实验臂（正式 Arm 清单和顺序必须在 CPU G−1 后冻结）
1. FULL_ANCHOR：z_s，208 行逐位复现 M4 full / M3 all，失败则 STOP。
2. ONLY_OTHER_ANCHOR：z_H+Δ_OTHER_ITEMS，逐位或数值容差复现 M4 only_OTHER_ITEMS。
3. ONLY_BULK：z_H+Δ_BULK（新增联合类，不是 full）。
4. DOSE_OTHER：z_H+normalize(Δ_OTHER_ITEMS)×||Δ_full||_F。
5. DOSE_BULK：z_H+normalize(Δ_BULK)×||Δ_full||_F。
6. DOSE_SHAM_OTHER：z_H+normalize(Δ_{D',OTHER_ITEMS})×||Δ_full||_F，独立第三 donor 错配。
7. DOSE_SHAM_BULK：z_H+normalize(Δ_{D',BULK})×||Δ_full||_F，独立第三 donor 错配。
8. DOSE_RANDOM：z_H+u_seed×||Δ_full||_F，非信息同剂量方向负对照。

所有主臂必须同时运行 donor NEW 与 donor ROUND 两种源；不允许只汇报有利的 NEW。除宿主 NEW 外，使用宿主 ROUND（Gold=无冲突、不得错误拒绝）作安全负对照；真正的 target Gold 与 typed action 在 CPU 阶段由独立 oracle 确认。宿主 ROUND 的跨场景配对兼容性要在 G−1 先证明，失败则不得假称完成该负对照。

### 主读出 / 判据草案
- 继续 M4 的 S(arm)、SPEC、JOINT：C/conflict 与 A/action 均按 Gold 判定；同时逐项报告每个 typed head、false rejection 和 margin ΔM，不允许仅凭边际变大宣称修复。
- 主比较：同 cell、同源、同范数条件下 DOSE_BULK vs DOSE_SHAM_BULK、DOSE_OTHER vs DOSE_SHAM_OTHER、DOSE_BULK vs DOSE_RANDOM；按 donor group 和 host group 两个聚类维度报告，留一来源组并报告稳健性。
- 次比较：对照 M4 原始 ONLY_OTHER / FULL；测量缩放因子分布、平均剂量、异常值、非有限及 OOD，确认“等范数”不是数值假象。
- 至少区分 SOURCE_SPECIFIC_SUPPORTED、DOSE_COMPATIBLE、INCONCLUSIVE、STOP_INCONSISTENT 四类；具体数值阈值、负对照误拒绝上限和分组覆盖率在 **GPU 前的正式 prereg JSON** 中一次冻结。不能在看到 GPU 结果后改变。
- 如果 DOSE_BULK ≈ DOSE_SHAM_BULK 或 RANDOM，说明“CONTEXT+OTHER_ITEMS 的位置特异语义”解释未获支持；如果存在稳定差异，才考虑后续更精准的 provenance/role/round×authority 语义控制。

### CPU G−1：强制准入（0 GPU）
1. 从 GitHub blob SHA 和真实服务器 captures 核对 M4 manifest/raw/activation 文件、model identity、Gold、token SHA；所有服务器产物必须位于 ~/wjc 所辖目录。
2. 证明每个 target 的 span/token shape 兼容（31 positions）、class 分解/加和与 pre-span NEW/ROUND 身份；三方 donor 选择固定且排除来源泄漏；same-author 和 diff-author 分层。
3. 实算 α 分布与非有限数量，检验同剂量精确度、数值稳定性、伪随机复现与预设最大缩放；不满足覆盖门槛即 STOP/修订草案，不启动 GPU。
4. 构造正式四格/两种目标 Gold 对照：宿主 NEW 应拒绝；宿主 ROUND 应允许。独立 oracle 需全量 PASS、不得以模型本身做 Gold。
5. 基于上面可行性重新冻结预算、arm 数、host-ROUND 负对照数、SHA、source-group 分层和完整 prereg 决策阈值；脚本 fake-model self-test 和原始 M4 full anchor 一致性检查先 PASS。
6. 只在 CPU G−1、权限、ledger、批次预算全部确认后讨论 GPU 准入；不得把此设计草案称为实验完成。

### 潜在后续机制门（本 M5 不自动宣称完成）
- 即使通过等剂量控制，仍需对自然 forward 中的原生 source-edge 做损毁/救援、QK/gate 对 V/OV 消融、角色/轮次/权威/位置正交 Gold 控制、四 typed 读出的作用中介与 held-out group 测试。
- 对真实 Agent 安全威胁及防御策略的端到端检验属于外部效度阶段；不得从模拟器激活 patch 成功率推出攻击成功率。
- 文献 preflight：对照 A546 的 Tracing Contextual Override、Trust Cascade、注意力安全锚点和之前的 TrustJev/CEA/SCIT；普通电路定位或激活移植不是独立创新贡献。

### 归档与状态
- 主要依据：M4_RESULT_R1.md；M4_ANALYSIS_R1/m4_analysis.json；M3_RESULT_R1.md；A546_20261028/研究索引。
- 本文件仅记录可执行科学设计的起点。下一个明确任务名为 **A461_MECH_M5_CONTEXT_DOSE_AND_SOURCE_SPECIFICITY_CPU_G_MINUS_1**；在 CPU PASS 前没有正式 M5 GPU 实验。
