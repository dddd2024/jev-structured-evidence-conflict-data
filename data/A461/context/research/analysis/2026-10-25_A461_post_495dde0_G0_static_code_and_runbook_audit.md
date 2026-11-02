# A461-PSMI｜并行Agent新G0主程序、独立验证器及运行手册的静态安全审计

**日期（America/New_York）**：2026-10-25。**不执行也不代替并行Agent的CPU G0**。研究状态依据GitHub commit `495dde06`：主程序606行和独立验证器529行已提交；来源旧A427-v2 328/328、旧A428-Twins 12/12校验是**Agent宣称的本地校验**，不是新的正式原生DEV双路径G0执行终态。本轮没有访问学校服务器、SecJev原始DEV gzip、模型或GPU，所有新研究工件通过独立analysis路径保存。

## 1. 新代码的进步及当前资源上限

新代码主程序：`research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/A461_psmi_counterfactual_cpu_gate_v1.py`，Git blob `9b814ed9096ad633ea729b1e7b4cf813eac734f4`；独立代码：同目录`A461_psmi_independent_gate_verifier_v1.py`，blob `bd98429bf245b6dab14afd006b0af651fad36772`。两份代码使用结构不同的规则Oracle，重复独立读取源内DEV、Gold和重构编辑输入；Twin和LANL原生动作不能合并为部署授权。此结构比仅写设计协议向正式G0迈出一步。

新runner CAPs：LANL L1每组3、L3A每组2；Twins T1/T2/T3=6/6/4；N2每个合格L1源组抽1、最多3。按LANL已有3个风险阳性日组作为上限，`2×(9+6+6+6+4)+3=65`条**修改后arm**（原始arm不在`pair_rows.jsonl`中，而由原始state及`pair_key`重建）；旧基线最多31个，故在每个唯一基线算一次时最多**96个独特前向输入**（还不含重复推理/precision replay）。128个条件性G1上限**现有CAPS下并未超出**，但只使用`len(emitted)`的65计数来宣称完整物理前向预算，仍属不完整。G0需将`old/new/neutral/retimed`及其实际token hash、重放、去重策略形成严格物理账本；并行Agent此前冻结V1上限示例160次因本次缩减已不再是实际代码上限。

## 2. 正式G0仍存在两项违反冻结实验合同的情况

**（A）原协议只准CPU tokenizer，主脚本却加载CPU模型权重。** 冻结V1：`hard_resource_bounds.model_loads=0`；`tokenizer_encode_allowed`明确`no model weight load`。主脚本L533–536:`checkpoint.load("cpu", LoadOptions(dtype=torch.float32,merge=False,attn="sdpa"))`，随后的receipt上报`cpu_model_loads=1`；独立验证L470–473同样完整调用`cp.load("cpu",...)`。这不同于实际GPU forward（模型前向仍为0），但它是**资源合同不一致**，潜在占用几GB内存。GPU未获准入，不能用“CPU不是GPU”来豁免冻结G0模型权重加载硬门；必须**在执行前**改成无模型权重载入的合法原生token/renderer方案，或者独立签发未来CPU G0资源补充协议（并核内存上限），不能回填已发生的运行。

**（B）N1只报告old→修改的token长度，不判new与neutral等长。** 主代码L572–580记录`token_len_delta_vs_old`、第一不同token位置，独立验证L474–505逐arm重渲染一致性，但是都**没有**同一pair`new`与`neutral`真正native-token数相等的声明/门，更没有`N1_TOKEN_MATCHED/UNMATCHED`结果。即使完整CPU G0其他路径PASS，不能据此宣称“对照已排除一般数字/文本扰动”。建议在独立审查后生成每轴`token_match_matrix`，将不匹配者预注册归类为探索性或剔除，不可看到GPU预测后再筛样。N2合法时间值的digit width也不等于token匹配。

**（C）独立验证器的`--skip-render`绕过token验证仍输出一般PASS。** L329允许该参数，L459–505仅在未指定参数时独立CPU渲染，L507无条件将整体状态标成`PASS_A461_PSMI_G0_INDEPENDENT_VERIFICATION`（若前面其它步骤未报错）。实际Runbook不要求skip，故不能声称当前执行必然绕过；但需将跳过时状态明确标成`PARTIAL_ORACLE_ONLY`，正式G0 PASS应强制token重渲染。

## 3. 新发现的两项Runbook硬故障

手册 `research/experiments/2026-10-25_A461_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE_RUNBOOK.md`，blob `2d39e26de66547abb15c1b5674f447f986f11d91`：

- **手册L19预创建`"$RUN"/G0`和`"$RUN"/G0_VERIFY`，但主脚本L251/Verifier L337均硬性要求输出目录** `not out.exists()`；因此原样运行手册会在创建正式数据前直接失败。正确做法是只提前创建`"$RUN"`及manifests/logs/receipts，让各runner独占创建自己G0/G0_VERIFY目录。
- **独立验证器Runbook L29漏传必需参数`--repo-root`**；实际独立脚本L327将其标记`required=True`，所以即使修复第一项，手册原指令也会直接发生argparse错误。应加入`--repo-root ~/wjc/jev-checkout`。

这些是由原始手册与源码的确定性语句推导出的**运行前阻塞**，不是试图重跑Agent实验得到的新日志。修复后才可能执行CPU G0，而非要求GPU放宽任何条件。

## 4. N2时间扰动可能违反真实来源事件顺序：已构造最小的数学反例

主程序`lanl_retime_edit`（L186–201）只把合法窗内**失败**事件的`seconds_before_current`统一加最小可行正数delta，并检查时间窗/同秒冲突，却不重新排列整个历史事件数组，也不检查全体事件的时间排序。第二验证器L217–240复做相同编辑，不校验全体时序有序性。

**纯内存合成单元证人（明确不是SecJev原始数据或已观察到模型错误）**：

```
原始：[(240,Fail), (220,Fail), (200,Success), (199,Fail), (150,Fail)]
       ↓  按整个历史年龄降序，是合法有序列表
delta=1：199+1=200，碰撞200秒的Success，按代码跳过
delta=2：全部Fail年龄+2、Success保持200
修改后：[(242,Fail), (222,Fail), (200,Success), (201,Fail), (152,Fail)]
        200 < 201，原始降序时序已经破坏
```

两个状态都包含4条失败，只有同一已知目的地，**Gold在当前事件失败时都为`record_failed_attempt`**，所以双Oracle Gold一致无法排除此类来源时序invalid。若原始LANL `recent_prior_events`确实要求从较旧到较新的时间顺序，必须新增来源时间排序门：N2重新采样delta并保持所有events的年龄非增序；或在事件顺序明确不属于契约时显式证明并记录，否则`INVALID_N2_ORDER`。不允许以Gold不变替代原生合同有效性。此反例不证明当前真实DEV中一定有这样的N2场景；那需要并行Agent真正执行G0的逐行审计。

## 5. 独立统计结论及通知

已读取旧FP32证据：Twins T3的4条静态规则起点`A428_007..010`中仅`A428_007`基线预测正确，其余3条原本已错；不能把这些当clean→wrong严格非回归。这一有限样本不能代表全体DEV。我们的独立GPU预算/统计报告（GitHub `research/analysis/2026-10-25_A461_G1_forward_budget_statistical_power_and_clean_baseline_gate.md`）已证明中性对照和source-group聚类的重要性，见MacKinnon等 `https://doi.org/10.1016/j.jeconom.2022.04.001`，且6个彼此独立、所有方向相同的discordant pair才使双侧Exact McNemar达到P=0.03125。当前从未发生新G0模型对或G1统计推断。

以上问题已直接加入并行Agent执行[Issue #2](https://github.com/dddd2024/jev/issues/2)评论：`6393452464`、`6393468274`；仅独立审查，不抢写其源码/Runbook，也不取代它的最终PASS/HOLD/STOP回执。建议并行Agent在执行前修复Runbook硬故障、模型加载合同和N1等token配平，接着进行DEV全量CPU双Oracle/token审批；**当前尚无从GitHub可验证的正式G0执行日志或GPU许可**。

**本轮资源：** GitHub已有脚本/协议/旧派生FP32只读，合成纯数学时序例子0模型；新原始语料扫描0、学校服务器登录0、模型load/forward0、GPU0、训练0。仅研究新增工件写入GitHub并回读；GPT Library/服务器双备份未核验。
