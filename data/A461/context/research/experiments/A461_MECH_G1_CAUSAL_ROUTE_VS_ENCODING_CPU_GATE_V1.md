# A461-MECH-G1｜新增安全证据：编码、读取、交互及类原型机制的 CPU 准入

**状态：DESIGNED_CPU_GATE_ONLY / GPU_NOT_ADMITTED / NOT_EXECUTED。** 当前 v9 论文的限定范围审计 PASS 不变。本方案不是新的整稿审计。

## 核心可证伪问题

1. H-ENC：遗漏的追加冲突是否没有在相关中间层形成可用的关系特征？
2. H-READ：是否存在相关关系特征，但它不能沿目标 typed question 的读出路径影响结果？
3. H-INT：全片段 patch 是否通过与宿主其余中介的交互而修复，而非单独由一项关系特征决定？
4. H-CLS：成功移植是否仅转移一般拒绝/正类倾向，与作者—轮次—区块的具体见证绑定无关？

这四个解释不必互斥。若 CPU 无法构造彼此独立的匹配对照，不能仅凭组间结果在四者中选胜者。

## 已有 CPU 证据

见 research/analysis/2026-10-27_A461_POSTPASS_MECHANISM_FOUR_HEAD_CPU_G0.md 以及可执行分析脚本 research/analysis/scripts/A461_kc_fourhead_cpu_v1.js。本轮 K-C 从真实 FP32 logits 复算：104 个跨组对、53 次 C∩A 联合修复；E 有序 logit softmax 期望相对 sham 在 103/104 上升，Q argmax 在 0/104 变化；冻结 host Gold 显示 2/8 个 host 的 quorum 预测原本错误，联合修复中仍有 6 次保留这一错误。E 的分析温度分数不是经 native API 确认的官方 score。

## 下一项明确任务：A461-MECH-G1.0（CPU Gold + witness 匹配准入）

**不要调用 GPU。**

- 阅读冻结 Stage-A roster Git blob 1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8（172 个候选），K-C design blob cd4cd9e5632cfa1b8aa476b94a332e3705af2f0f 与 FP32 raw blob 19d3a06c27953b1f2b4dcd2770394d28741a69fd。
- 在**可信原始 corpus**中重新恢复全部 donor/host 的 state，不得用 roster 中仅有的 appended event 推断完整 witness。原始 corpus 路径来自冻结 GPU runner：~/wjc/a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz；其预期 SHA256 为 2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56。严格复算 scene SHA 与 oracle_old / oracle_new / oracle_sa（C/Q/A/E）。
- 官方 kev score 接口必须与 evidence_level 的**有序评分**而非仅 argmax 对齐。Gold E 的合法性及实现须分别由原始协议与独立 oracle 复核，不能把 T=1 的预测期望视为 native score。
- 在每个独立 host 下构造 **合法冲突 witness 角色匹配与角色错配、同决策类但不同证据见证、未识别新增冲突、duplicate/sham** 的严格候选。比较前冻结 Gold、author/round/block 的相对角色、nonce/签名有效性、Token SHA、片段宽度和场景长度。**来自不同模拟器 run 的 v0、b3 只是局部标签，文本相同不能证明实体相同**。
- 按真正独立的来源组计数，登记每个格子的 donor/host 覆盖度，K-B 和 K-C 已用 source groups 的重叠，不能把所有 104 个交叉单元当 IID。
- **CPU 准入 STOP 规则：** 任何关键语义对照格子为空、反事实改变了本应固定的 Gold、原始 state 身份无法核对、token/长度条件无法满足，就记录 NOT_ADMITTED 和真实原因，不运行 GPU。不允许重新定义格子来获得阳性。

## 可能的后续 G1.1：路径级因果机制实验（当前未冻结、不得声称完成）

仅在 G1.0 实际 PASS 后，再预注册最小 GPU 实验，区分 row-specific 的表征、下游 attention/MLP 或 query/key 路由，以及 donor × host 的高阶交互；保留 original full-span positive、SA/dose/permutation/null、同类错 witness、未识别 conflict 与非 witness 负对照。评价所有四个 native typed readout，分别报告原生 C margin、A margin、E 官方分数、Q margin，以及联合 Gold，一律报告 negative outcomes。不得从激活移植本身推断已经辨认“唯一的编码失败机制”。

新的 GPU 批次须在运行前冻结输入/模型 pin、预注册样本和阈值、CPU self-test、持久 quota ledger，服务器所有产物限定 ~/wjc；用户的既有研究授权规则及预算边界持续适用。现阶段不重复已完成的 3628 次 A461-G2 GPU 前向。

## 直接相关文献和竞争边界

- Lepori et al., ACL 2026: https://aclanthology.org/2026.acl-long.676/ （有表示但不能用）
- Vaidyanathan et al., NeurIPS 2026: https://arxiv.org/abs/2606.27510 （激活 patch 中介交互）
- Brunello et al., BlackboxNLP 2025: https://aclanthology.org/2025.blackboxnlp-1.30/ （路径效应隔离）
- Mueller et al., ICML 2025 MIB: https://proceedings.mlr.press/v267/mueller25a.html （因果变量及电路评估）
- Pandere et al., BlackboxNLP 2026: https://aclanthology.org/2026.blackboxnlp-1.28/ （冲突电路的 gating vs rewiring）

**成功标准：** 某一严格对照的机制预测在事先固定的 source-group 复验中成立，且至少排除一个原先不可排除的替代解释；并非只增加 patch 方向显著的样本数量。
