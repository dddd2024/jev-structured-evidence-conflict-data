# A461-G5 第三轮独立窄增量复审：PASS_CODE / HOLD_GPU_AUTH_RECONCILIATION

**日期**：2026-10-25。**复审请求**：[GitHub Issue #2 评论 6399056722](https://github.com/dddd2024/jev/issues/2#issuecomment-6399056722)。**目标新提交**：`2e8d93fe54cddf3317e03861d5bdcbe0ee5eb34d`。**新 GPU runner Git blob：`d05b070e0723de5af70c6afbfd312ac99fdbdbb3`**。旧审查通过 blob `c5dd9e0cd376c20c50b75348f9aed4dad5e67418`，本次新 blob 不继承旧 PASS，独立针对改动重审。

## 结论与限定

- **PASS_CODE（新 runner 的增量静态代码/冻结计划一致性审查）**：三类修复实现了其声称的执行一致性目标，未在本次差异中发现新的确定性 P0；保留冻结的 G0 CPU 12/12、真实语料预检与双向 patching 协议。
- **HOLD_GPU_AUTH_RECONCILIATION**：已记录前次真实尝试 **物理 forward 1 次**；如用户原明确批准的“28 native forwards”是整个 pilot 的**总授权上限**，重新完整运行 28 次将合计 **29 次**，不可自行解释为同一批准。必须取得用户明确认可额外完整 28 次（总累计 29），或冻结一个科学上可解释且真实调用不超原授权总上限的重启方案，再执行。用户这次要求“复审”，**不是新增 GPU 授权**。
- **没有真实完成的双向因果干预数据**。审查方没有启动服务器 GPU，没有对用户帐户/设备做任何执行调用。

## A. 失败真实性及缺失证据

`research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/PATCHING_PILOT_ATTEMPT1_STOPPED/execution_receipt.json`：

- `status=FAIL_A461_G5_PILOT_GPU`
- `gpu_model_loads=1`
- `native_model_forward_calls=1`
- `physical_prehook_count_at_failure=1`
- `error_message="unexpected capture overhang"`
- 原版 runner 提交旧条件 `capture_donor_old`，而只准许旧 span 混合状态的条件名为 `capture_donor_old_at_new_span_coords`。
- 此尝试 `SHA256SUMS` 只有 `execution_receipt.json`，**第一物理 forward 的 logits 因后置断言先于写盘而丢失**，必须说明为数据缺失，不能补造或声称已分析成功。
- 原冻结协议的 28 次干预没有完成；保留失败回据及物理消耗。

## B. 变更逐项独立复审

独立读取并对比 `c5dd9e0c` 和 `d05b070e` 完整 runner blob；新建的 `FROZEN_CONDITIONS` 解析出 28 个顺序条件，逐项与归档 `G0_PILOT_CPU_GATE_REAL/pilot_execution_plan.jsonl` 的 **28/28 `condition` 字段完全一致**；真实 `G1_PREFLIGHT_REAL3/execution_receipt.json` blob 为 `4bad07a8a9f7177cdc2259e0f3d552e559a652bf`（已回读核对）。新预检回执：`self_blob=d05b070e...`、`status=COMPLETE_A461_G5_PILOT_PREFLIGHT`、`twins_census=797`、同 3 组 old-state SHA64 / new+SA span、模型加载/forward **0**；它支持真实 corpus/tokenizer 到模型加载前合同，不是模拟整个 GPU forward。

1. **条件名**：第 369–374 行 donor 捕获条件改为 `capture_donor_old_at_new_span_coords`、`capture_donor_new`、`capture_donor_sa` 三个冻结原名；独立 diff 显示后续 25 项实验调用序列与已审过的 runner 保持一致。原导致 P0 的首项断言现可通过。
2. **执行序列守卫**：第 47–62 行 `FROZEN_CONDITIONS` 完整 28 元素；第 306–307 行在 `model.forward` **之前**按已完成的物理记录数校验当前条件名。条件数量、顺序与原计划 28/28 一致；它检查 **condition 字符串顺序**，未检查 layer/target/span/source 全元组，因而是必要但非充分的完整计划一致性条件。冻结代码的那些其余分量在本次 diff 未变化；下一轮可把 full-plan tuple contract 放入 CPU 静态测试，而非再拖延已有试点。
3. **保存优先顺序**：第 331–351 行在模型返回、logits 形状/有限性通过后，先将原始行以 append 模式写入 `raw_native_logits_pilot.jsonl`，再执行 hook 活性/捕获等后置校验（第 353–357 行）。此前导致第一次读出丢失的 `unexpected capture overhang` 已移至 `model.forward` 之前（第 311–315 行），其他 patch 越界亦在发起模型前受校验。故不会因相同后置过界/活性断言再次丢失一次成功生成的**可序列化有效 logits**。若模型内部 forward 抛异常或 logits 本身损坏，仍不保证有可记录的读出；此边界须如实报告。
4. **物理计数**：保留 `model.lm` prehook 物理计数、运行成功后 `physical==receipt==28`，失败时写 `physical_prehook_count_at_failure`。任何实际调用均记入总资源消耗，不得跨失败尝试重置资源审计口径。
5. **因果对象与限制**：`conflicting_vote` 仍是独立 C row；供体/宿主同一层与 34-token append span 的 patch、identity、SA-sham、token permutation、正反两方向与源输入均未发生变更。层 23 末层 post-hook patch 的 null 可能结构上不可传播；独立 action 行不会因 C-only patch 改变。即使获得正结果也仅为 1 donor × 2 DEV hosts 的探索性机制线索。

## C. 独立证据与剩余门槛

- 既往冻结 G0 CPU 12/12 和 108/108 tokenizer parity：`G0_PILOT_CPU_GATE_REAL/execution_receipt.json`。
- 同 runner 的最新 G1 预检：`G1_PREFLIGHT_REAL3/execution_receipt.json`（服务器原始回据 GitHub 副本；审查未在模型端重新执行）。
- 旧 GPU 失败：`PATCHING_PILOT_ATTEMPT1_STOPPED/execution_receipt.json`；只 1 次前向，不是双向有效实验。
- 用户授权在仓库 `admission_receipt_pilot_gpu.json` 显示 `explicit_user_gpu_approval=true`，来源描述为此前对 **28-forward pilot** 的批准；但第一次物理消耗已是 1，要求执行 owner 明确累计数与新运行上限，不得仅按该布尔值自动重新使用同一总额度。
- 审稿 PASS 仅可签给 **runner blob `d05b070e0723de5af70c6afbfd312ac99fdbdbb3`**；与 CPU runner blob `a8b507c1`、协议 blob `111595a3`、冻样本和预算 28 联合约束。以后变动 runner 或 protocol 需差分复审。真正 GPU 仍需满足 user-scope authorization、runner self-hash、首次 baseline determinism 与 identity 自补丁检查；失败须保留日志而非升级科研结论。

**最终裁决：该代码的本轮窄增量复审 PASS；当前不允许把此 PASS 解释成对累计 29 次调用的 GPU 许可。新任务是资源授权对账后按冻结执行图取得首个完整模型 patching 结果；不再额外启动 G0 重做或无关新方向。**
