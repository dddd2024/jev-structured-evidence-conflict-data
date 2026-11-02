# A461 G1 独立静态审查｜103 次前向内恢复全部配对，重放校验存在确定性失败

**审计日期：2026-10-25（America/New_York）**。本分析仅读取 GitHub 上真实 G0 归档的 65 条请求、65 条 native token 审计、14 条 N1B 和 G1 runner。没有执行正式 G1、不接手并行 Agent 的实验，也没有 GPU 前向。具体行级名单和 SHA、自动断言见同名 JSON。

## 1. 最新代码状态与已经得到修复的错误

并行 Agent commit `5be7c65e7f7afe8a79571e0e23e2151c5449da47` 修复了此前 G1 `old_baseline` 的 `None` 引用错误：源码现在使用 `r0["original_scene_sha"]`。**不得继续把这个错误列为当前 G1 阻塞**。此外此前 `96fe77c` 增加了失败 traceback，可保留错误终态；但仍未观察到 G1 推理结果正式回读。

## 2. 独立复算一个严格不超 103 次 forward 的分配

G0 真实归档：31 个主干预对，另有3个 LANL N2 时间对照，34 个 `pair_key`，14 条独立N1B，原来31条N1。只按`pair_key`将源内 treatment、N1、N1B 对齐，再逐row检查 G0 冻结token数与 Gold，发现**不需要增加一次模型前向**就能修复当前试验分层：

| 物理forward角色 | 建议次数 | 规则 |
|---|---:|---|
| 旧基线（原计划，不自作主张按 SHA 前缀去重） | 34 | 保持原manifest预订 |
| 主干预 treatment | 31 | 每个冻结主pair一次 |
| N1B 已配平中性对照 | 14 | 保留14个原来Twins场景 |
| 原生 N1 结构中性对照 | **17** | **保留没有N1B的17个pair_key** |
| N2 时间干扰对照 | 3 | 保留已冻结3个 |
| 旧基线精度重放 | 4 | 原始primary对照其replay |
| **合计** | **103** | 不扩大另一会话所述条件预算 |

**当前代码实际挑选N1的方法有问题。** G1 `n1_keep = n1_all[:17]`，选择LANL L1全部9、L3A全部6、Twins T1两条，**17/17本来已跟treatment等token数**，但标签写为`N1_unmatched`；它没有包含一条T2。

**建议的预注册、只依赖已冻G0来源而与模型输出无关的替换规则**为 `keep N1 iff pair_key NOT in matched N1B source pairs`。由真实数据核算，恰好得到：LANL L1 9、L3A 6、Twins T2 **2**（`run-100`、`run-125`）。这17条中15条等长、2条不等长；14条N1B均有独立等长复核。因此该103次计划保留**31/31个主场景的中性对照**、其中**29/31个等state-token长度**，2个重要T2是未配平的探索性数据，不允许升级为已排除格式混杂的机制阳性。14条N1B之前与原N1的14条等长pair完全重叠，但N1B仍可有*不同语义干扰轴*的对照价值。

源码下游的forward/Gold读出需要区分`Gold-changing response`（L1/T1/T2）与`Gold-invariant nonregression`（L3A/T3）。真正T2 old accept→new reject只2对，而且都不等长度，无法仅凭其他4条old wait→reject的matched样本来断言“法定人数后否决优先”的特异性因果机制。

## 3. 另一个确定性的G1执行Bug：重放永远失败，可能丢失全部推理输出

在 commit `5be7c65e...` 的脚本 `A461_psmi_g1_paired_pilot_fp32_v1.py`：

- 第223–226行从4个primary旧基线为每个仅追加**一条** replay。
- 第247–248行只有`kind=="replay"`才写进`replay_state[base_row]`；primary行不会写进该字典。
- 第251–255行对每个base row调用`ck(len(rrs)==2,"replay count")`，然而该字典在当前设计下每个base row必然**恰有1条**，独立于模型logits是什么。
- `raw_native_logits_103_requests.jsonl`的持久化在上述重放断言**之后**（第259行）。因此即使全部103次FP32前向都真正完成，也会在重放核验时抛错，并且**不保存这103次真实logits文件**。终态失败receipt可能记录错误，但不能代替每次请求的原始预测日志。

**修复方式（请交给执行Agent，不覆盖它的代码）**：按同一基础row id在`rows_out`查找primary，与`:replay`一一组成二元对；确保每个old row至少一条原始和一条重放，逐 logits/precision 与native token SHA比对，而不是收集两条replay。**在执行模型推理时先把每次raw logits以只追加日志持久化**（适当flush/fsync和校验hash），后验验证失败也不会丢掉本来昂贵的实验结果。通过只读模拟/小CPU mock单测验收这些逻辑，再开启真正GPU循环。

## 4. 当前治理结论

G0 已提交真实双Oracle/CPU token rerender PASS；本次复核发现其manifest把N1误算为0/31等长，真实是**29/31**。GitHub现有G1 admission receipt**自述**另一ZCode会话获得用户103次forward许可；本会话无法直接核验该独立授权交互，**不否认可能有效**，但代码中的对照分配和回放逻辑必须先修复、重新冻结并在授权范围内办理，不可因“有103额度”就冒险直接启动。

当前没有可回读的新G1 GPU结果或严格SecJev模型策略阳性。G0技术结果应予承认，但 G1 实验完整性仍存在**P1 执行可靠性**和**P1因果对照分层**两个必须修复的缺口。A463仍只是A461的否决支配机制细化，而非新增GPU方向。

**资源账本：** 本会话只读GitHub既存工件（G0 65条请求/65条token+14条N1B）、纯静态算术与G1源码；真实模型forward=0，GPU=0，服务器访问=0，CAL/TEST=0，G0/实验代码/并行执行产物均未修改。未核验服务器或GPT Library额外备份。
