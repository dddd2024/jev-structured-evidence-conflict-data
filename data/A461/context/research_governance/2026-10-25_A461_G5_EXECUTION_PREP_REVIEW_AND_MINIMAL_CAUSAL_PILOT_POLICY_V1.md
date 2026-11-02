# A461-G5 实验前准备效率复盘与最小合格因果试验执行规范 V1

**日期**：2026-10-25。**性质**：研究流程决策 / 执行门槛，不是 GPU 执行许可，不替代冻结实验协议，不是白盒因果证据。**状态**：`POLICY_FROZEN_PILOT_CPU_DESIGN_PENDING`。

## 1. 用户反馈与科研决策

用户指出：G5 双向 activation patching 在下午就已进入“执行前准备”，但迟迟未产生首次有效因果干预结果。**反馈成立**。严格来源约束、精确 Gold、位置/问题行对齐、预算上限和独立评审是必要的；但多次因未定义变量、JSON、输入 schema、循环调用记账、错误行、hook 闭包等基础程序问题而被退回，属于可预防的工程低效。不得将版本迭代数量、静态审查文件数或 CPU 门数当作论文科研进度。

研究目的改为：**在安全且可审计的前提下，尽快取得首次可解释的真实因果干预观测，而不是继续扩大实验准备范围**。其后再决定是否扩大样本、层数与模型；绝不因为“赶进度”跳过 source-valid 对照或双向因果必要条件。

## 2. 已取得的科研资产（不得重置/重复）

- A461-G3：真实低信任/来源内新增冲突识别异常，附 G3 P0/P1 后验勘误；仅探索性行为现象，非已证因果机制。
- A461-G4：G0 实际 CPU 准入、G1R 26 对三项指针 Q/K 读出精确会计；25/26 的**分数变化分解**最大项为键侧，224/224 分支复算通过；不把代数归因说成神经中介因果。
- A461-G5：**V2** 严格修复 G3 初始状态重复；36 对、112 次原生模型前向，1 个合格 donor（T2 wait / run83）、2 partial、33 failed；SA 读出 C=false 34/36。数据为 DEV 探索性结果，不是新的独立 source-group 确认。
- 至 2026-10-25 11:43 UTC 检索：G5 patching V1→V4 多轮修复，**仓库没有已核验的成功 172A/172B 双向 patching 原始结果**；V4 仍未获独立可执行 PASS。已知独立拒绝 `research/analysis/2026-10-25_A461_G5_V3_independent_blind_review_REJECT_before_GPU.md`（commit `7098a190`）；A471 最新静态审计 `research/literature/A471_20261025/A471_repository_evidence_audit.json` 记录 V4 仍有 6 个 P0，包括原始读入/变量、宿主数与物理预算的不一致。禁止因 “V4 已上传”推断可运行。

## 3. 造成反复准备的工程根因

1. **缺少从 GitHub 存档产物出发的一次性端到端 CPU dry-run**：只检查个别函数而未覆盖真实 `G0D_CONS_V2/pair_rows.jsonl`（只有 new/SA，旧状态需重建）、`G1S_V2_REAL/render_token_lengths.json`（是 `{schema,rows}` 单个 JSON 对象，而非 JSONL）、`G1S_V2_REAL/raw_native_logits_112_requests.jsonl`（旧臂 row ID 为 `pair_key:old`）。
2. **没有静态输入输出合同和 schema 测试**：`q_tw`、`state_by`、`hosts` 等变量缺定义；V1→V4 错误在后续审查才暴露。
3. **没用原生前向契约确定 intervention row**：SecJev Qwen3.5 hybrid 为各 question 的独立 causal row；`conflicting_vote` 在冻结 questions 中为 index 1；不能在 index 0 `certificate_action` 行 patch 却用 C 作为效果终点。
4. **未以真实 tokenizer/渲染器验证内部插入点**：`received_messages` 后仍有 `validator_set` 字段，追加新票不是旧序列的简单后缀；必须保存前缀/插入 span/尾部后缀锚点的原生 token 坐标。
5. **预算根据文案手工填写而非执行图自动计数**：不同版本的 `84/88→95/88→97/93→97/94`，以及 V4 动态 host_pool 未限制导致独立 A471 估计实际可能超过 128；**批准数不能代替物理调用计数**。
6. **一次次补丁代替系统性回归**：评审发现一个 bug 后只修单项，未对完整 runner、全部分支和真实 schema 统一复检。

## 4. 新的强制执行制度（立即适用 G5，建议后续白盒实验复用）

### A. 一次 CPU 闭环，先通过再提交评审

- **冻结原始输入指针**：固定 git commit + blob SHA，确保仓库/服务器 run 输入等价；原始实验数据与失败日志 append-only。
- **真实 schema 可读性**：逐文件 `json.load`/`jsonl`，样本/arm/row IDs/预测键存在且一一匹配；`old` arm 从原始 corpus 重建并用 canonical SHA 独立交叉核验。
- **合法性**：独立双 Oracle、作者/区块/时间顺序/Gold/接收时间单调；中性 SA 真的 Gold 不变，且模型旧/新/SA 的严格合格性以真实 logits 判别，而不是仅看 source Gold。
- **token 门**：冻结同一 native tokenizer、完整请求 SHA、C question 对应因果行、确切 appended 票据 span + 可能保留的尾随字段；不以“首差异 == 旧 state 最末端”为假设。
- **CPU mock hook 端到端**：在完全同形状的四 question 行 tensor 上确认仅命中命名的 C 行、各层捕获键不覆盖、正确位置不越界、identity self-patch 不改变输出、宿主长度/供体长度相等或映射保留语义；模拟必要性和充分性两支。
- **物理预算自动生成**：从冻结 host 清单、层数、每种 baseline/capture/patch/sham/random 真实次数计算，不由人手改总数。先将 runner trace 与 receipt 和预算逐项对账，`predicted == observed_mock == approved <= hard_cap`，不一致 `STOP`。禁止启动后才发现超额。
- **落盘与失败恢复**：每次原生 forward/capture/patch 归档输入指针、序号、目标 question/layer/span、读出、SHA；异常时保留已经发生的物理调用和原始中间数据，独立回读；不覆盖失败尝试。
- **评审门**：只有上述逐项测试证据全部 PASS，才对冻结的**同一个 commit/blob/源输入/预算**组织一次真正独立盲审；改动任何实验关键逻辑都要重跑受影响测试与差分评审。不允许用“用户希望尽快实验”或其他阶段通过证明代替本阶段 PASS。

### B. 先做“最小合格白盒因果试验”，而非首轮就追求完整 10 宿主 × 6 层

建议新实验名：`A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1`。

- **CPU 候选**：经 archived V2 G1S 独立筛查的唯一合格 donor `run83`；两个候选失败 host `T2_WAIT run114` 与 `T2_ACCEPT run182`。两者与 donor 不同 run group；目前冻结 token-length 清单显示 donor 的 new/SA 为 +34，两宿主的 new/SA 也为 +34，且各自 old/new/SA C=false。**这只是一份可复查的候选名单，不是 CPU 门已经通过**；必须重跑 native anchor、source-valid 双 Gold、token SHA 检查，并证实各自独立且时序合法。
- **实验单位**：2 个合法等宽宿主，C 相关独立 row，先选择 **两层**作为技术可行性试点（冻结选层依据，不做从结果倒选层）；一个 donor，两个方向：recognized-donor treatment span→host neutral SA span（充分性），failed-host treatment span→donor recognized new span（必要性）。
- **不可省的控制**：宿主原生 C 基线、donor new 基线、identity self-patch、合法 SA-sham 供体、位置打乱的 donor span、同一 host question row 的定向/非定向完整性检查；所有干预按 host、layer 与控制条件配对报告。
- **示例物理调用预算（仅规划，不代表批准）**：donor old/new/SA 捕获各一次 **3** + 两个 host SA 基线 **2** + 两 host identity 捕获与回填 **4** + 2 hosts×2 layers 双方向恢复 **4** + SA sham **4** + random span **4** + 2 host treatment 捕获 **2** + donor new baseline **1** + 2 hosts×2 layers suppression **4** = **28 原生调用**。真实预算由 CPU runner trace 自动导出；共享一次多层捕获是否物理可复用必须实测，否则重算后申请。*28 并非 GPU 额度或 standing authorization*。
- **评估门**：identity、token 对齐、off-target 恒等及对照有效性必须先 PASS。实际恢复或抑制即便存在，也只能解释为**single-donor DEV exploratory causal probe**；若效果不胜随机/SA 控制，不能宣称语义特异性；若无效，及时更新可证伪假设，不循环堆轮次。首次两层 negative 不等于全深度机制已被证伪。
- **扩展条件**：最小试验有效且各类对照成立之后，才扩到 10 host × 6 layers 完整 G5；独立新 source group、跨模型验证、既有 Tang/activation patching 文献 novelty gap 是论文机制主张的额外强制门，不能以试点替代。

### C. 协调责任和停止条件

- 唯一执行 owner 与 run_id 通过 GitHub Issue #2 登记；不要多 Agent 重复触发同一 GPU run。**其他 Agent 可并行做 CPU 静态分析、文献与独立复核，但不能并行破坏冻结的 GPU 前向计数。**
- 预检不通过时标为 `STOP_PRE_GPU_<CAUSE>` 并在**同一测试套件**内修复；后续提交必须附 `PASS`、真实文件 SHA、最小可复现命令、physical-call ledger。不要将单纯版本号累加作为产出。
- 若最小试验多次因工程原因仍不能进入 GPU，开展一次工程任务重构（提取可测试 pure functions 与依赖注入、通用 schema、自动回归）而不是无限 Vn；科研解释与工程缺陷分别记账。
- 修复/评审/测试可以前进，但**在 GPU 独立准入通过之前，严禁提交“已完成因果实验/有创新机制”的论文表述**。

## 5. 明确优先级

**P0** 实际输入 schema + 测量目标问题行 + tokenizer 真锚点 + runner CPU/mock + 物理 ledger；**P1** 最小两宿主双向试验的冻结和独立评审；**P2** 已证有效后扩大 10×6 与独立新来源；**P3** 新候选方向筛选。仅当 P0/P1 已有 owner 且进度不受干扰时并行推进 P3。

## 6. 关联可追溯证据

- Issue #2 的 V3 评审请求：`https://github.com/dddd2024/jev/issues/2#issuecomment-6396659022`
- 独立 V3 REJECT 回复：`https://github.com/dddd2024/jev/issues/2#issuecomment-6396921878`
- V3 独立拒绝报告：`research/analysis/2026-10-25_A461_G5_V3_independent_blind_review_REJECT_before_GPU.md`。
- V4 independent P0 audit：`research/literature/A471_20261025/A471_repository_evidence_audit.json`；其静态估算不是已执行 GPU call。
- G5 V2 对照原始数据：`research/rounds/A461_G5_DONOR_RESOLUTION_AND_PATCHING/{G0D_CONS_V2,G1S_V2_REAL}`。
- G4 native anchors：`research/rounds/A461_G4_POINTER_READOUT_AND_BIDIRECTIONAL_PATCHING/G0ABC_REAL_20261025/g0c_anchor_map.jsonl`。

**决议：科学约束不放松，工程准入一次性做好；下一有价值里程碑是首个通过独立门槛的真实双向因果干预结果，而非 V5/V6 的提交数量。**
