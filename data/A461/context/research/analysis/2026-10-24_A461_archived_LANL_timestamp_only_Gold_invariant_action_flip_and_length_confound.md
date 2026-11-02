# A461｜已完成FP32中的LANL时间扰动同Gold动作翻转：必须新增的负对照，而非新GPU阳性

**审计日**：2026-10-24（纽约）；**范围**：只读再分析2026-10-23已经完成的A428原生FP32输出和冻结G0A/G0B，不扫描任何新原始SecJev语料，不重跑模型、GPU、LoRA、Hook或训练。**当前G−1=HOLD、G0未执行、GPU未准入**。其他Agent可能并行写GitHub；本轮只用新路径追加分析，不改冻结实验协议与已有终态，执行之前应再次检查最新main及独立收据。

## 1. A461原假设的一个直接竞争解释已在历史原生模型日志中出现

本轮直接跨源文件匹配：

| 证据 | 冻结位置 | Git blob |
|---|---|---|
| 24份原生输入（A428 G0A） | `research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0A_REAL_20261023/frozen_model_inputs.jsonl` | `13adf301dd67c5cc787c72b4b9ace695c52fef4e` |
| 原生token清单（G0B） | `research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0B_REAL_20261023/native_token_manifest.json` | `d36a2012a34feabdaa883abc5b5bbffb555f0c31` |
| 24次旧FP32前向/Logits（G1） | `research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G1_REAL_20261023/G1_raw_native_logits_and_probs.jsonl` | `9d2da80374f3a34cc3e24362779f786f8d23e36c` |
| 独立旧Gold/预测复核（G2） | `research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G2_REAL_20261023/G2_per_scene_predictions.jsonl` | `f02741bb8cfea2f45c1c73c435d90f8cb064cd6b` |

在两份Native请求中，将`state.recent_prior_events[0..3].seconds_before_current`去掉后，其余**所有原生state与两typed问题配置按结构一致**。它们有相同来源家族LANL、相同`lanl:day:48`日组，相同模型答案备选顺序、相同source-local Gold SHA256 `6ea73ced3662b72fa4abf701b54f24ca636f73e92db0260de676ab4da9a63e2c`。其当前事件均为`Fail`、在300秒合法窗内有4条此前失败记录、只有1个已知失败目标，规则既未达到5次burst，也未达到3个目标，因此两边Gold必须是`record_failed_attempt`。

| 旧实测值 | A428_021 | A428_024 |
|---|---:|---:|
| source group | day:48 | day:48 |
| 先前失败相对秒数 | [238,157,76,5] | [187,155,147,77] |
| Gold | **record_failed_attempt** | **record_failed_attempt** |
| 实际FP32动作预测 | **investigate（错误）** | **record_failed_attempt（正确）** |
| `p(investigate)` | 0.765357 | 0.083508 |
| `z(investigate)-z(record)` | **+1.186387** | **−2.389619** |
| 已冻结native token数 | **631** | **633** |
| native token sha | `20ef68d3...` | `4eb41a93...` |

两个原生logit的带符号margin差为**3.576006**，不是tie或读头小数截断现象。两条请求不是同一物理原始record进行同样编辑得到的合法配对，而是旧已经冻结的两个自然模板相同的来源场景，**所以既不能把它们当成随机化时间干预，也不能当A461新实验已完成**。A428 12条LANL旧请求中另有同一去时间字段模板下的`A428_022`（day49）与`A428_023`（day50）均Gold相同且预测正确，形成4条同模板记录、其中1错3对，但不能用6个成对组合冒充6个独立证据。

## 2. 关键归因限制：时间语义与token长度没有分离

`021→024`的唯一原生数值差异是四条事件时间；其真实token化长度却从**631→633**，且`5`→`77`使字符串数字位数变化。两typed问题仍独立渲染，所以`failure_burst`与`triage`虽然会同时受同一个state改变影响，其一个分支预测正确不能推断它传值给另一分支。

可允许的严格结论只有：

> 一组**Gold保持不变、原生状态除有效时间秒数字段外相同**的已执行FP32天然旧场景中，模型原生triage动作发生了错误/正确翻转。它属于**时间数值或其呈现方式相关的不变性问题候选**，不是一个已被孤立的时间语义因果机制。

未排除：模型对最近失败的非政策启发式关注、数值位宽/token分割、两个长度不同的渲染、位置和最近事件数值差别、旧场景筛选与单组依赖等；也没有重复相同输入的不同精度/seed重放。

## 3. 先例核对后，不能把通用数值敏感性作为A461新增安全研究贡献

1. **Are AI Decision Models Biased? A Case Study of Jev** `https://arxiv.org/html/2610.19619v1`，本轮读原文 §3/§5/§8 相关论述：Jev在无关数字、选项排列以及概率输出层面已有直接敏感性证据。该论文面向通用Jev任务，并非SecJev规则Gold。
2. **What Really Controls Temporal Reasoning in Large Language Models: Tokenisation or Representation of Time?** `https://aclanthology.org/2026.findings-emnlp.2149/`，ACL Anthology原始摘要：时间数值的token fragmentation与语义时间表达之间的关系已有比较研究。这不是对SecJev做过相同实验，但禁止一看到数字相关变化就假定安全规则语义特殊机制。
3. **LGMT** `https://www.sciencedirect.com/science/article/pii/S0950705126010506`，已核出版方论文摘要/方法要点；逻辑Gold不变情况下作变异测试属已知测试范式。
4. **SecJev v2** `https://arxiv.org/html/2610.03073v2`：不同typed问题分别形成causal row，当前安全标签为来源内策略动作，并非真实部署授权。

**A461的新增量仍未通过G−1审核**：只有可复现的strict Gold动作违例、确认性独立来源组，以及Q/K/LoRA对**策略证据阈值变化**与“仅改变无关时间/格式”的对照之间有机制差别，才有机会证明此研究比通用数字敏感性更强。

## 4. 对接当前A461新CPU准入而不跨越门禁

保持原研究命名 `A461_20261025_POLICY_SEMANTIC_MONOTONICITY_CPU_G_MINUS_1`。在将来符合新G−1并另行冻结版本的G0中，应当把因果设计拆为：

1. **政策谓词真正翻转的轴**（B或S单阈值）：原来LANL 31条B阈值起点/3 day组、22条S阈值起点/2 day组均只是必要条件，生成原生old/new时严格检查时间窗、已知目的地、样本来源、合法事件资格和双臂独立Gold。
2. **政策Gold保持不变的时间轴负对照**：只修改合法窗口内真实事件时间，不让历史失败数量、唯一目的地数量、事件格式与Gold变化；先验证来源身份及时间合法性，不能直接把不同自然样本当受控干预。
3. **数字token/格式对照**：尽量使用同位宽整数并用**真正的native tokenizer**验证token长度、candidate-order、原生答案候选、位置与token-id SHA。**同字符宽度不保证同token数量**。新增高低时间数值的分词长度差必须报告并作为混杂，而不是强行填“matched”。
4. **主结果**：按家族和source group报告**策略Gold错误率**，同一证据增量前后合法动作保持与误升级/漏升级独立报告；次要为带符号`z(investigate)-z(record)`，不能用一个margin的数值变化充当安全错误。
5. **机制**：只有确认性阳性且排除普通token/格式/时间轴解释之后，才能申请双向Q/K/LoRA白盒Hook预算。旧A428_021 vs _024只能用于事先注册必要负对照与线索，不能重当新发现或独立保留组。

**优先结论**：此轮最有价值的进展不是“GPU已可运行”，而是找到了一个直接竞争A461因果解释的已执行old FP32对比。若未来只出现与时间/格式轴同样大小的效果，而策略阈值特异性不能单独成立，则`STOP_ONLY_GENERIC_NUMERIC_FORMAT_SENSITIVITY`，A461降级而不扩大算力。

**资源及并行Agent协作**：本轮实际新模型前向0、GPU0、训练0、原始TRAIN/DEV/CAL/TEST gzip 读取0；直接读取冻结GitHub G0/G1/G2文件。其他Agent的提交需要下一次读取最新HEAD重新协调；不覆写其协议、代码、运行结果或后续Gold，不从提交消息推断运行已经完成。本报告只在GitHub独立追加并逐Blob回读，服务器及GPT Library备份暂未验证。
