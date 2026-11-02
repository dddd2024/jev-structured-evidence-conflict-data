# A461｜LANL源内真实DEV策略分支、边界候选与旧两家族模型错误的独立复核

**日期（America/New_York）：2026-10-24；范围：已经执行的旧实验的原始衍生证据二次核算。** 当前仓库最近研究方向为A461-P1、A462-P2（原生可信字段共同支持缺失）、A453-P2/HOLD。此文件不修改原始G−1协议或任何过去实验终态，不宣称已开始A461实验，也没有读取新的SecJev原始DEV gzip行、CAL、TEST或加载模型。所有计数出自此前真实A427 v2和A428 G2的归档JSONL，另保存同名机读JSON和SHA钉定的Python只读复算脚本。

## 1. 先看原始竞品文献，不将“单调变异测试”冒充新方法

- 原始 SecJev v2 `https://arxiv.org/html/2610.03073v2` §3.1–4.1：Twins原生cert action、LANL原生triage、独立typed question行、共用LoRA+pointer head皆为原作者已发布。两个问题预测一致性≠串行计算。
- `Safety Evaluation for Large Language Models with Metamorphic Testing: An Empirical Study`，Journal of Computer Science and Technology 2026，`https://doi.org/10.1007/s11390-026-5705-z`：安全LLM上的七类变异关系及测试研究已发表。不能靠“受控输入后输出不一致”单独主张创新。
- `LGMT: Logic-Grounded Metamorphic Testing for evaluating the reasoning reliability of LLMs`，Knowledge-Based Systems 2026，`https://doi.org/10.1016/j.knosys.2026.116324`：一阶逻辑变异关系是已有测试方法。
- `Security Properties of Neural Networks as Decision Problems`，`https://arxiv.org/abs/2609.39768`：正式研究神经网络的单调性/非干扰/公平性验证复杂性，其ReLU理论不能直接等同SecJev混合架构的证明。

前两篇只审了出版方摘要/方法概述，后两篇中LGMT审了出版方摘要、Security Properties读了原始arXiv引言与理论摘要；尚未完成本轮SOP定义的系统全文G−1与独立审查。**当前G−1=HOLD_PRIOR_ART_INCOMPLETE**。剩余可能新增量必须是独立可执行安全策略Gold上的新严格动作错、双向pointer Q/K/LoRA因果干预、跨组/跨来源特异性，并排除普通形式扰动与模型共同偏差。

## 2. 本轮确实读取了以前真实归档的328条独立Gold逐行衍生证据

证据：`research/rounds/A427_20261023_LANL_TRIAGE_FAIL_VOCABULARY_V2_CPU_GATE/P0_REAL_20261023/independent_gold_rows.jsonl`；**Git blob** `af2e68efff36a604b635bdf9402324a6ecf36508`。这是2026-10-23已执行的P0派生结果，不是新审计原始record、也不是新标签。冻结源原始`development.jsonl.gz` SHA256 `2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56`；原独立rule-Gold和源标签328/328一致；7个`lanl:day:44..50`独立日组。

LANL的两个Gold谓词：

```
B := 最近合法时间窗内 prior failed LogOn 次数 >= 5
S := 最近合法时间窗内已知不同失败目的计算机数 >= 3
R := B OR S
triage := investigate if R else
          (record_failed_attempt if current_event is a failed LogOn
           else continue_monitoring)
```

| 来源组 | 已归档样本 | B=true | investigate | B=false且investigate | 潜在B单阈值起点 | 潜在S单阈值起点 |
|---|---:|---:|---:|---:|---:|---:|
| lanl:day:50 | 96 | 25 | 28 | **3** | 8 | 11 |
| lanl:day:49 | 102 | 32 | 32 | 0 | 12 | 11 |
| lanl:day:48 | 76 | 17 | 17 | 0 | 11 | 0 |
| lanl:day:47 | 42 | 0 | 0 | 0 | 0 | 0 |
| lanl:day:46 | 10 | 0 | 0 | 0 | 0 | 0 |
| lanl:day:45 | 1 | 0 | 0 | 0 | 0 | 0 |
| lanl:day:44 | 1 | 0 | 0 | 0 | 0 | 0 |
| **总计** | **328** | **74** | **77** | **3** | **31** | **22** |

**关键新发现A：全部3条`B=false, investigate=true`来自`lanl:day:50`单个来源组**，原始派生ID`LANL_POLICY_0048`（f=3,d=3）、`LANL_POLICY_0119`（f=4,d=3）、`LANL_POLICY_0307`（f=4,d=3）。它们确实证明`S`可以独立触发Gold，但不提供跨日的自然机制重复；77个investigate场景中有74个`B=true`，仅3个`B=false`。另有13条`d>=3`全部来自day50，其中10条同时`B=true`，不构成独立只由S触发的例子。

**关键新发现B：从旧逐行Gold可计算出受控单事件反事实的必要条件起点**：

- **B-only阈值起点31条、3个日组**：当前仅4个可见合法prior failures，失败目标数1或2，`B=false/S=false`、当前非investigate且无旧摘要/未知目的地歧义。若原始输入存在可信可追加的同窗失败事件，选**已有目的地**追加1条，可使`B:0→1`而`S`不变。
- **S-only阈值起点22条、2个日组**：当前已知2个失败目的地，prior failures最多3条，`B=false/S=false`。若可追加一条可信同窗失败事件到**第三个新目的地**，则`S:0→1`，同时失败总数不超过4，`B`仍假。
- 这些31/22只是**原始源内字段的必要支持情况**；缺少同一原始scene中包含时间戳、历史摘要契约、目的地允许集合、追加是否改变来源真实性、encoded token长度/位置的完整再判。**成功生成并双Oracle验证的合法反事实对=0**，模型成对推理次数=0。不许称已发现单调性违例。
- 值得保留的统计限制：7个日组按旧scene分布的`1/Σ(n_g/328)^2≈3.946`，仅是实际来源**曝光集中度等价组数**，不是独立统计样本数、置信区间或模型准确率估计。

## 3. 把已经执行的旧FP32小样本也加入全局机制判断

复算证据：`research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G2_REAL_20261023/G2_per_scene_predictions.jsonl`，Git blob `f02741bb8cfea2f45c1c73c435d90f8cb064cd6b`，**24条曾经实际执行的FP32请求、非本轮新模型运行**。

| 来源家族 | 旧原生动作正确 | 源内动作错误 | 能否证明单调性违例 |
|---|---:|---:|---|
| Twins | 8/12 | 4/12，均Gold `reject_conflict`却预测`wait`或`accept` | **不能**：没有同一状态合法证据递增配对 |
| LANL | 11/12 | **1/12**：`A428_021`，Gold `record_failed_attempt`却预测`investigate` | **不能**：也是单点源内分类错误 |

`A428_021`同源组`lanl:day:48`，模型`failure_burst=false`正确，但独立triage问题错误升级到investigate。它只能称为**源内过度调查/假阳性**，不是现实系统执行拒绝，也不是“识别模型输出在串行动作头被忽略”。SecJev两问是独立causal rows。旧Twins四条错误中原始C预测亦错误；此前A451记录另一个SHAM处理下的`A428_011` C正确而Action错误属于不同arm，不能混同。

**跨两个来源出现普通动作错误≠跨两个来源复现同一个单调性机制。** Twins此处更多为冲突漏拒，LANL为过度升级，方向和策略语义均不同；历史组已消费、不能包装成新的外部确认结果。

## 4. 纠正另一项潜在误读

旧A430 V2 DEV记录`has_repeated_author=0/797`，但有`reject_conflict=230`并不矛盾：A430代码的`has_repeated_author`仅指**同一候选块**的重复作者投票，冲突判断却基于**同一作者**对另一候选块投票。没有同块重复票，不排除跨块双投导致的冲突。**不能错误利用A430 negative声称Twins不可能出现自然veto；但也不能利用其230个冲突宣称存在可以改动认证通道的真实攻击。**

## 5. 对A461原实验的明确准入建议

当前正式研究名：`A461_20261025_POLICY_SEMANTIC_MONOTONICITY_CPU_G_MINUS_1`（**DESIGNED_NOT_EXECUTED**）。本轮只读归档分析进展标记`PARTIAL_SOURCE_LOCAL_BOUNDARY_SUPPORT`；绝不将其追认为G0真实执行或G−1完备通过。

若下一次能访问`~/wjc`服务器，先在正式G−1签发后使用上面的31/22 **起点而非预设有效实验对**，对原始DEV做只读源字段可编辑性/时序检查；禁止拿TEST/CAL做补样。对每一候选拟合法增量均要求old/new两臂独立策略Oracle与时间窗/目的地/来源语义检查通过，维持策略文本与原生choice菜单不变；另准备同长度中性事件、旧组去重、四格真假组合和非安全格式负对照。由`S`支路仅覆盖**一个天然已触发日组**，不能以22个拟造`S`对照代替多来源家族的自然复现。若合法编辑与来源权限不成立，必须`STOP_NO_RULE_PRESERVING_PAIR`，不是强行GPU。

模型指标优先按Gold逐臂动作错误（Twins false accept/reject-conflict、LANL investigate误升级/遗漏，互不合并）与source-group配对计数；沿同一事实变化的signed margin为次要量，不得因为margin非单调就直接宣称安全错误。Q/K/LoRA patch必须等到严格行为阳性、基线正确与SHAM配对、G−1创新差异及独立审查全部通过之后才提出资源申请。

**本轮真实资源：** GitHub旧派生Gold文件重新解析328条、旧FP32预测文件解析24条；没有新原始SecJev DEV/TRAIN/CAL/TEST语料行扫描，模型forward=0、GPU=0、训练=0、学校服务器访问=0、GPT Library双备份未核验。全部新分析证据写GitHub并回读，原始归档记录不覆盖。
