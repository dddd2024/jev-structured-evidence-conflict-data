# A461-G5 最小双向因果 patch pilot — G1 窄增量独立复审 V2

**评审裁决：PASS — PRE-GPU CODE/SOURCE-CONTRACT ADMISSION REVIEW ONLY.**  
日期：2026-10-25。**不是用户 GPU 授权；不是已执行真实 patching；不是因果机制论文结论。**  
复审请求：GitHub Issue #2 评论 [6398697255](https://github.com/dddd2024/jev/issues/2#issuecomment-6398697255)。  
之前 REJECT：`research/analysis/2026-10-25_A461_G5_MINIMAL_PILOT_G1_INDEPENDENT_BLIND_REVIEW_V1_REJECT.md`，commit `ed537ae1`。  
本次修复提交：`9be367970dfcf247196e027a9fb50961c353c613`；随后仅新添 CPU 后处理分析脚本 commit `61c57cb54e3d01d36bf96c5be631dbb457c1e827`。

## 冻结审查范围（不可挪用 PASS）

| Object | Git blob |
|---|---|
| `research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/A461_g5_pilot_gpu_v1.py` | **`c5dd9e0cd376c20c50b75348f9aed4dad5e67418`** |
| `.../A461_g5_pilot_cpu_closed_loop_v1.py` | `a8b507c1d0f5890575f882930bfd5a145f5e1b29` |
| `.../A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_PROTOCOL_V1.json` | `111595a31f3fb18268142501602cf6d91df848dd` |
| `.../G1_PREFLIGHT_REAL/execution_receipt.json` | `e0676890fdc0ccb779d5228c29e8ba2ba4cbea9a` |
| `.../G0_PILOT_CPU_GATE_REAL/execution_receipt.json` | `bf8c25961fe857e795e24ac3740fecc7e99ef6ed` |

评审方法：GitHub 原始冻结 blob 逐行核查、旧 runner `d2efc395...` 与新 runner `c5dd9e0c...` 代码差分；服务器实际 `G1_PREFLIGHT_REAL` 归档回执、`SHA256SUMS` 和准入文件的静态回读。**未连接服务器执行 GPU，未独立重跑实际服务器 corpus/tokenizer，未声称模型推理成功。**

## 针对之前 REJECT 的逐项复审

### P0 gzip 读取：CLOSED

- 新 runner 行 **22** 已导入 `gzip`；行 **136** 改为 `with gzip.open(CORPUS, "rt", encoding="utf8")`；原 `Path.open("rt")` 错误已清除。
- 新增 `--preflight-only` 使用同一个 runner 的**前置 CPU 执行路径**（行 83–85、124–236）。真实服务器归档 `G1_PREFLIGHT_REAL/execution_receipt.json` 报 `COMPLETE_A461_G5_PILOT_PREFLIGHT`，twins 记录 **797**，名册 old 的 SHA64 分别为 run83 `433890d19a...`、run114 `1b0e96fb22c6...`、run182 `231b919006dc...`，三个 pair 的 new/SA 均建立正确追加 span **[624,658)、[493,527)、[456,490)**；runner 对归档的 9 个原生请求全数执行完整 token-ids SHA 对照才会到达 COMPLETE，因此基于该执行路径及记录，可接受 **9/9 CPU 预检完成**的证据。
- preflight 回据 `self_blob=c5dd9e0cd376c20c50b75348f9aed4dad5e67418` 对应本次已提交 runner；当时记录的 admission `blind_review_runner_blob=d2efc395...` 为**运行预检时的旧回据**，现在仓库回据已更新为 `c5dd9e0c...`。preflight-only **故意不验证盲审 PASS/用户授权**，但该分支始终在第 238 行实际 model load 之前退出；**完整 GPU 分支仍在行 120–122 强制检查 PASS、相同 runner blob 和独立用户显式授权。** 这不构成授权绕过。
- 新代码将 `roster_reqs` 的 new/SA 键恢复为存档真实 `row_id`（例如 `G5_...`），old 为 `pair_key:old`，修复上轮未通过真实 preflight 暴露的键映射问题；后续所有 `run_forward` 使用 helper `arm_rowid`，与冻结 V2 Git 数据接口吻合。

### 边界和账本调整：CLOSED for pre-GPU

- 行 323–328 将 donor-old `[624,658)` 在旧 state_len=652 的 6 个超出状态位置，单独标记 `MIXED_STATE_BRANCH_UNUSED`，并仅此条件允许 capture 超界；所有真实 patch span 以行 296–297 / 329–330 再次断言 `<= state_len`。此未使用的 donor-old 状态不能归因于旧状态里的“新增票”表征。
- 失败回据行 425–431 尝试写入 `physical_prehook_count_at_failure`，减少模型 forward 抛错后 `native_model_forward_calls` 少记的风险。正常执行行 411–413 仍要求 physical prehook 与记录数、冻结预算 **28/28** 相等。
- 新 runner 的双向真实模型方案未修改：两个不同 source run 宿主、2 层（11、23）、两方向、identity/SA sham/permute，恰 28 次计划物理前向；同一个 `conflicting_vote` row 动态解析、在 post-layer hook 中按同一 row 捕获并 patch，hook 活性断言保持。GPU 真正结果必须运行时单独核验。

## 限制、附注与执行时必须坚持的停止条件

1. **PASS 不证明 GPU 可确定性成功。** G0/C1 CPU 回据声称 12/12、108/108、G1 实际预检 9/9，均为归档代码/回据证据；真实 backbone 加载、PEFT hook 模块路径、GPU 数值 bitwise baseline、identity self patch 的首次结果尚**未经模型实跑验证**。若其中任何一项出错，立刻留存 FAIL 和所有实际物理 forward，停止，不可静默替换参数或跳过验收。
2. 当前 `admission_receipt_pilot_gpu.json` 的 `blind_review_verdict=null`、`explicit_user_gpu_approval=false`：**本审稿不直接修改/签发回据，也不代表用户已授权 28 次前向**。执行 owner 必须将本审稿编号/runner Git blob 正确写入后续独立准入回据，并取得**用户明确的模型执行批准**，再冻结同一 runner SHA 执行。
3. **第 23 层 post-layer state span patch 的结构性限制**：在最后一层输出上替换较早的 state 位置，不会经后续 decoder 层传播至 later question candidate readout；对于该具体 patch 形式，第 23 层的零效应很可能是结构性预期，不能作为反证“末层无冲突特征”的证据。第 11 层更有因果传播的可解释性。两层均需原样报告、不得事后选择性删掉 23。
4. 独立问题行的 action/quorum logits 若不变，是结构性互不传播；**不能将 C-only patch 对 action 无影响写成“安全动作效用被保持”的因果证明**。
5. 实验仅一个严格合格供体 + 两个 DEV 来源组宿主，未补 donor-side matched sham/permute 的必要性对照，仍只允许 `single-donor / 2-host / DEV exploratory causal probe`。不能据此声称普遍白盒漏洞、论文独立创新或真正防御有效性。
6. 目录校验 `str(out).startswith(str(ROOT))` 是不严格的路径前缀判定，需由执行 owner 明确验证 **out.resolve().is_relative_to(ROOT)** 及独一 run ID，防止输出跑到 `~/wjc_other`；本次预检的归档实际路径位于 `~/wjc`，因此不构成本轮 P0。
7. 后处理分析脚本（commit `61c57cb`）只在合成 outcome 上通过，与本次 runner SHA 或实际模型效果无关，真实 logits 出现后才开展独立校验；本次 PASS **不自动覆盖其他变更的脚本版本**。

## 最终裁决

**PASS：仅针对已冻结的 G1 runner blob `c5dd9e0cd376c20c50b75348f9aed4dad5e67418` 的“窄增量独立 GPU 前代码/来源合同审查”**。此前 REJECT 的压缩文件读取阻断已由真实服务器同 runner preflight 成功回据纠正；新增 row-ID 修复、donor-old 注记和物理失败计数均已记录；未在本次差分和现有项目证据范围内发现其他确定性 pre-GPU P0。

**此 PASS 不解除独立的用户 GPU 显式批准门，也不是执行后科学结论。** 下一目标是：按精确 Git blob 和批准预算单次运行冻结 pilot，拿到 28 次逐前向日志与完整 receipt；若运行中触发 STOP，保存原始失败并做最小增量修复和针对性审计。不得再返回无休止实验准备或新增论文方向。
