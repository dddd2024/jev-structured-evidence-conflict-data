# A461 / A463｜G1执行声明与可独立验收证据的边界，以及A428→A461来源组复用审计

**审查日期**：2026-10-25（America/New_York）。**证据状态**：本轮没有运行GPU/CPU模型；从GitHub最新提交 `4d939191ebb61a8310ea5fd144f98c6ee977daa5` 的真实执行程序说明读取到 G1 已用掉103次物理forward、4组replay与primary一致的执行方声明。但GitHub目前仅新增验证代码，没有G1原始103行logits、第一次FAIL收据、修订后的PASS收据、pre-forward gate或SHA256SUMS。因此必须把`EXECUTOR_REPORTED_103_FORWARDS`与`INDEPENDENTLY_VERIFIED_103_PREDICTIONS`区别开，不能复述上一轮“完全没有GPU推理”，也不能将代码说明当可复核模型阳性。

## 一、新的G1执行信息——报告103/103，尚不能验证模型预测

执行方新增`research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/A461_psmi_g1_replay_verify_v1.py`（Git blob `07087180f9710f777dec0966754d17452e64458f`），其源代码说明称：（1）103次模型前向在服务器已执行并保存`raw_native_logits_103_requests.jsonl`；（2）原G1 V1`FAIL`只来自其按`replay vs replay`而非`replay vs primary`对账的程序错误；（3）4组replay与primary完全一致；（4）修订脚本无需再次调用GPU，可从已有logits出具`execution_receipt_corrected.json`、`replay_receipt.json`和新的SHA256SUMS。

静态审查确认该新脚本的确实现`primary[base]`与`replay`的逐数组比较，并检查token_ids_sha256相同、总行数103、replay行4、pre-forward gate状态为PASS。这**有能力纠正某种V1纯后处理误报**，但仅说明算法存在，还不能证明真实数据确实通过。该脚本也缺少：强制primary/replay的question数和key顺序相等（Python `zip`默认静默截短）、103个forward_index唯一且连续、4个不同base、各角色分配与冻结plan一致、pre-forward每行token SHAs关联检查、对应源内Gold和模型/输入版本SHA的完整对账。

**已交接执行方**：[Issue #2](https://github.com/dddd2024/jev/issues/2) 评论 `6393972086`：请将103行原始logits、原始V1 FAIL、修订V2 PASS、pre-forward gate、4个replay实际对账结果及每个非敏感文件SHA256保存到独立`G1_REAL_20261025/`目录并逐blob回读。禁止覆写失败源文件；如果无法上传原始logits，只能依实际能独立验证的下游数据降低结论强度。用户要求的服务器`~/wjc`和GitHub双端证据备份仍需根据真实文件核算。

## 二、上一轮主张“不是完全重复”得到更精细的计算边界

使用`G0_REAL_20261025/pair_rows.jsonl`真实31条处理臂，通过`declared_edit`精确撤回每条新增message或LANL prior-event，得到31个old state（去重后30个）。将**完整canonical JSON旧state**与旧`A428 G0A/frozen_model_inputs.jsonl`全部24份状态逐项比较：

| 两种重合定义 | 独立结果 |
|---|---:|
| A461 轴实例 | 31 |
| 其不同原始state | 30 |
| A428历史原始state | 24 |
| **与A428完全相同的A461原始state** | **1** |
| A461不同source group | 11 |
| **与A428来源组重合的A461主轴实例** | **18/31** |
| 重合source group（并集） | 5 |

唯一相同状态是`LANL_L1_B_THRESHOLD:7affc3f35f85fa15`，`lanl:day:50`，即A428的`A428_023`。历史A428对这一个**旧基线**的真实FP32判断：Gold与预测均`failure_burst=false, triage=record_failed_attempt`；top2 action margin`1.5392920970916748`，burst margin`4.6229389905929565`；历史token_ids SHA256为`e4eba881620aadb294c9ea2da0d0c489fa611ea0185333e787541d076f7dffaf`。这是未来G1 old-arm重放/跨轮一致性的既有锚点，**不是这次G1模型表现**。

来源组重合比完全相同的旧scene广泛得多：所有LANL L1 9条和L3A 6条均在历史已观察的`day48/49/50`组；Twins T1 6条来源组均未出现在A428，T2有两条重合`run100/run125`，T3有一条重合`run125`。**两条最重要的`C=0,Q=1→C=1,Q=1`、旧accept→新reject，就是这两个历史组中的新scene，且两条原N1长度都不匹配、G1原始plan没有选择其neutral。** 这进一步确定 G1 对机制主张最多提供**探索性组内证据**，不是对核心否决支配边的来源组独立、等token对照的确认。

这里不是把`same source group`错误地等同于`same source state`：确实只有一个A461旧state和A428完全相同。**已曝光组与真实相同输入是两类必须分开报告的依赖性。** 即使从今后的103行logs发现严格模型错误，确认性重复也需要新的未使用来源组与严格配平/双向干预，而非在已见DEV组继续抽相似记录。

## 三、已经执行的G1控制分配不能依据结果倒改

G1原程序（截至Git blob`92974bd102f3a16e93471f483a656f37ef6bae54`）仍按`n1_keep=n1_all[:17]`选择17条N1，其真实构成是LANL L1=9、LANL L3A=6、Twins T1=2，**17/17均已经在实际G0的new-vs-neutral中等state-token长度**；本程序仅以错误的历史标签称之为`N1_unmatched`。这17条不包含2个最关键的T2 `accept→reject_conflict`的neutral。另14条N1B来自已经被旧N1匹配的14个Twins scene。总计划角色`34 old+31 treatment+14 N1B+17 N1+3 N2+4 replay=103`可以保留103预算，但**如果103条实际已经生成，必须按已经执行的实际选择集进行解释**。

此前我们提供的103次、含全部31个pair_key中性对照的重新分配，是**GPU执行前的一份前瞻性备选方案**；如果执行方已实际完成原方案，则不能在查看模型预测后把二者混为同一个实证运行或声称实际给两条T2匹配了中性输入。那2条仍可分析`old→treatment`的Gold变化响应，但由于缺少等token中性臂、又重复使用已研究来源组，不能升级为完全隔离格式混杂的否决整合因果结论。

## 四、下一步实验分析设计（尚无具体模型logits，不能报告任何阳性）

接收真实103条logits时，首先核对每条forward_index与plan_row、model/config SHA、旧/新/N1B/N1/N2角色、各branch keys/原生token SHA、Gold label和source_group；在代码纠错后，保留V1失败原始收据并仅新写V2验证收据。然后基于真实Gold计算`strict action errors`，将`Gold-changing response deficits`和`Gold-invariant nonregression`分开报告。Twins四条策略转移类`00→01`、`00→10`、`01→11`、`10→11`及两个`11→11`稳定控制必须逐来源组统计，不可把16个轴实例当IID。

进一步对同时输出`conflicting_vote`、`quorum`、`certificate_action`的Twins辅助头，构造以下观察性诊断：（a）C/Q预测都错误时属于证据解析候选；（b）C/Q都与Gold相同但动作错误时，优先调查多头决策整合；（c）动作预测不同于把**模型自己预测的C/Q**代入来源策略规则所得到的动作，是多头逻辑不一致，但**不自动证明模型内部C/Q头因果支配动作**。这三种还需要新白盒双向干预和独立复现才能构成论文机制结论。

**结论**：有新的执行进度信息，G1 physical-forward=103由执行方报告、校正脚本存在；**直到原始103行logits及修订回执GitHub可回读，本审查不能给出任何准确率、行为违例率、QK/LoRA机制结论**。A461继续主线，A463为其否决-法定人数交互细化；原CPU G0真实双路径PASS仍成立，但计划token误标及CPU资源旧合同勘误需在报告中保留。

**本轮资源**：只有只读GitHub真实CPU G0/A428存档+G1静态代码；我方新增GPU/CPU模型forward0、原始DEV/TEST/CAL读取0、学校服务器连接0。远程Desktop Commander设备`dd`处于Offline，无法自行从`~/wjc`取103条logits；服务器/GPT Library双端备份未由本会话核验。
