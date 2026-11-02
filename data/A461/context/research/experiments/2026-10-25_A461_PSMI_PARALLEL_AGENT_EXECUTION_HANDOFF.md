# A461-PSMI G0 实验执行交接：仅并行 Agent 执行

**用户指令（2026-10-25）**：让正在独立推进 A461 的并行 Agent 执行本轮实验；当前分析会话不重复实现或运行它。

**主要任务/确认入口**：[GitHub Issue #2 — A461 CPU G0 execution handoff](https://github.com/dddd2024/jev/issues/2)。执行方请先在 Issue 回复 `ACK A461 G0 | HEAD=<sha> | RUN_ID=<id> | scripts=<commit> | status=PREPARING/RUNNING/HOLD`；没有认领回执不能声称已执行。

## 冻结对象

- 实验：`A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE_V1`。
- V2 修订必须同时应用：`A461_20261025_PSMI_CPU_GATE_AMENDMENT_V2_ENDPOINTS_AND_CHRONOLOGY`（LANL L3A、三类不同端点、G−1时序更正）。
- G−1：commit `5871f1f`，`NOVELTY_DELTA_TESTABLE`，**仅同意 CPU G0**。
- V1：commit `20898b8`；V2：commit `311b349`。
- 独立审查 [QA 约束](https://github.com/dddd2024/jev/blob/main/research/analysis/2026-10-25_A461_V1_V2_parallel_preexecution_shadow_QA.md)：CPU runner/verifier 未见于交接时 main；N1同结构≠同token长度；N1/N2控制选择需确定性代码；不匹配时必须标记，不能据此声称超出普通格式效应。

## 工作边界与交付

CPU-only：不加载backbone，不使用GPU，不做模型前向/训练；不读取CAL/TEST。所有新服务器工件在 `~/wjc/`，唯一RUN_ID、先读Git HEAD和是否已有实验回执。执行Twins T1/T2/T3、LANL L1/L3A、N1/N2/N3，双独立Oracle逐臂Gold、来源身份/时间合法性、CPU tokenizer真token数/哈希与负对照匹配、按来源组检查；保存STOP和invalid详情。

完成后向 `research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/` 归档脚本、原始非敏感证据、规则Gold、token审计、执行receipt、SHA256SUMS，提交GitHub并回读；在Issue #2回报 **PASS/HOLD/STOP**、实际有效对数、独立审查、资源账本。GPU仍需下一轮单独批准，条件性128次原生forward不构成当前授权。

**协调约束**：其他会话不抢跑、不覆盖执行方产物；如并行Agent未主动监看本仓库或Issues，须由控制该Agent的会话打开本链接。GitHub写入不能自行启动另一个独立Agent。
