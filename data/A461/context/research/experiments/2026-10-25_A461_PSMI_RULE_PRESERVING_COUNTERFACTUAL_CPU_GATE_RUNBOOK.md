# A461-PSMI G0 执行手册（CPU-only）

**协议**：`2026-10-25_A461_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE_PROTOCOL_V1.json`
**前置**：G−1 `NOVELTY_DELTA_TESTABLE`（commit `5871f1f`，先于本协议提交）；并发会话分析 `5fb35e9`/`522f566` 的三条设计约束已并入（N2 时间不变性对照、N3 位宽/token 如实报告、STOP_ONLY_GENERIC_NUMERIC_FORMAT_SENSITIVITY）。

## 资源边界

CPU-only：模型加载 0、GPU 0、backbone forward 0、网络 0、TEST/CAL 行 0。允许 CPU tokenizer encode（A428 G0B / A430 G0C 先例）。

## 服务器步骤

```bash
# 0) 同步仓库（先 fetch；若发现其他会话已冻结同研究 G0 协议，停止并协调）
cd ~/wjc/jev-checkout && git fetch origin && git pull --ff-only origin main
git sparse-checkout add research/experiments research/rounds/A427_20261023_LANL_TRIAGE_FAIL_VOCABULARY_V2_CPU_GATE

# 1) 新建独占输出目录（不得覆盖已存在目录）
RUN=~/wjc/a461-psmi-counterfactual-cpu-gate-20261025-v1
test ! -e "$RUN" && mkdir -p "$RUN"/{G0,G0_VERIFY,manifests,receipts,logs}

# 2) 主实现（构造 + 双 oracle 之一 + token 审计）
~/wjc/kev08b-smoke-20261001-153041/venv/bin/python \
  research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/A461_psmi_counterfactual_cpu_gate_v1.py \
  --repo-root ~/wjc/jev-checkout --out "$RUN"/G0

# 3) 独立第二路径复核（独立重写 oracle 与配对重算，不 import 主实现）
~/wjc/kev08b-smoke-20261001-153041/venv/bin/python \
  research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/A461_psmi_independent_gate_verifier_v1.py \
  --g0 "$RUN"/G0 --out "$RUN"/G0_VERIFY

# 4) SHA 清单 + GitHub 归档 + 回读收据（在 akzeptiere 任何 GPU 之前完成）
```

## 执行要点（从历史轮次经验）

- corpus 钉：`development.jsonl.gz` SHA256 必须 == `2920e1c9…`；先验 SHA 再读行。
- 构造全确定性：scene、作者、块、seconds 全部用协议规则选择，稳定排序，无随机数，不询问 tokenizer/模型。
- LANL 追加事件插入后保持 `recent_prior_events` 原有序列约定（`seconds_before_current` 降序 = 旧→新）。
- Twins 追加消息 `received = max(existing received)` 且必须 ≤ `decision_time`，保持非递减。
- 每臂 Gold 由主实现与独立实现各自从 state 重算，100% 一致；基线臂 Gold 与归档 A427/A430 oracle 值抽查比对。
- 渲染：`kev.api.SystemOneRequest → to_record → encode(strict=True)`，max 8192；逐臂记录 token 数、token SHA、首差异下标、编辑数字位宽；**不得声称 matched 除非 token 数严格相等**。
- 停止条件见协议；STOP 后保留全部产物，不改 Gold、不删目录。
- 服务器裸 `python` 是 2.7；一切用 pinned venv。ssh heredoc 用 `<<'PYEOF'` 防嵌套引号。

## 产物清单（G0）

`pair_rows.jsonl`（每行一个 pair/control，含 old/new 臂完整 native_request 与 scene diff）、`oracle_report.json`（双实现逐臂 Gold + 与归档值比对）、`token_audit.jsonl`（逐臂 token 计数/SHA/首差异）、`census.json`（各轴起点计数与排除理由）、`execution_receipt.json`、`SHA256SUMS(_V2)`；`G0_VERIFY/independent_review.json`。
