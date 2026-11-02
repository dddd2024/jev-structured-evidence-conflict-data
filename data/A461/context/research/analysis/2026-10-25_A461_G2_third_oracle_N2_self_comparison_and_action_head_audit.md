# A461 G2 数据分析准入审查：第三Oracle的N2自比较、真实三组复核和缺失的多头机制诊断

日期：2026-10-25（America/New_York）。独立研究范围：GitHub最新G2分析器源码与真实已归档G0中的LANL时间扰动数据。不运行模型、GPU、G0或G2；并行Agent继续负责所有正式实验和模型结果上传。逐项机器可核算证据见同名JSON。

## 一、当前实证状态

执行方在commit `4d939191`上传`A461_psmi_g1_replay_verify_v1.py`并说明G1的103/103次GPU前向已经在服务器上执行、真实logits已保存、4组replay与原forward一致；这不同于上一轮完全没有GPU行为的状态。不过GitHub当前未提供那103条真实原生logits、原始失败收据和校正后的新PASS执行收据。本审查无法独立复算任何模型预测/准确率，故结论只能是 **`G1_103_EXECUTOR_REPORTED_AWAIT_ARCHIVED_READBACK`**，不能写成“G1无GPU实验”，亦不能把声明当实测阳性。

并行Agent随后提交G2 CPU分析脚本，`A461_psmi_g2_independent_analysis_v1.py`，当前Git blob `58e90fe8cea92e2d6784b68b7359942ac8fb2c21`，主实验31对已经改成从`pair_key:old`原始G1行读取旧动作、从固定原始语料取旧state，不再误把新state当旧state；这是一次正确修复。但以下限制仍须独立审查后再接受G2正式终态。

## 二、N2时间对照存在old-vs-new Gold自比较

G2脚本第230–231行：

```python
old_state = next(x["native_request"]["state"] for x in prows if x["pair_key"] == r["pair_key"])
g_old = gold_lanl(old_state)["triage"]
```

冻结G0中的3条N2，各自`pair_key`均仅对应唯一一条`arm=retimed`记录；`next(...)`取回的是**同一个已修改后的state**。所以`old_gold`与`retimed_gold`相同只是恒等计算，而非第三独立Oracle验证。本错误不否定此前真正的G0两个Oracle通过，只会使G2额外声称的N2第三路径检验无效，也不会产生所谓模型预测错误的证据。

### 独立替代计算：真实N2三个组均确实保持Gold

本轮不是只指出代码问题；在G0归档`pair_rows.jsonl`中对3组N2做了两条相互独立的旧状态恢复路径：

1. 从**同一原始状态SHA前缀**对应的LANL-L1 treatment中，撤销其合法新增的`Fail` prior event；
2. 从N2的`retimed`状态中，对所有窗内LogOn失败事件年龄`seconds_before_current`逆向应用`delta=1`。

这两条路径每组恢复的整个原始JSON state**逐字段严格一致**；随后独立计算策略Gold：

| 来源组 | L1主处理臂 | N2重排臂 | 原始/新近窗失败计数 | 原始/新Gold | 时间排序 |
|---|---|---|---|---|---|
| day48 | `A461P_0001` | `A461P_0031` | 4/4 | `record_failed_attempt` | PASS |
| day49 | `A461P_0007` | `A461P_0032` | 4/4 | `record_failed_attempt` | PASS |
| day50 | `A461P_0013` | `A461P_0033` | 4/4 | `record_failed_attempt` | PASS |

三组均只有1个有效失败目的地，故`failure_burst=false`，Gold前后不变。结论是**`N2_REAL_SOURCE_POLICY_GOLD_STABLE_3_OF_3`**，但因未获取真实103条G1 logits，无法核算N2时间扰动是否造成任何**模型**误拒、误判或非回归失败。

## 三、尚未完成的A463机制识别所需多头分析

G2脚本现在对Twins只提取`certificate_action`输出、对LANL只提取`triage`输出。实际SecJev原生G1每个Twins请求包含`conflicting_vote`、`quorum`、`certificate_action`三个typed问题，且C/Q源内Gold独立可得。若只算动作正确率，将混淆几种完全不同的候选解释：

- 模型`pred_C`或`pred_Q`先读错源事实，动作只是跟随错误事实；
- 模型`pred_C`、`pred_Q`都正确，但`pred_action`与来源动作Gold不一致——可优先检验决策整合；
- `pred_action != f(pred_C,pred_Q)`，即模型各输出头可观察地逻辑不自洽——仍**不能直接断言**内部动作头由前两头因果生成，更不能没有干预就宣称QK/LoRA机制。

因此正式G2需要逐run记录三个模型头、各自的Gold、选项顺序/logits及交叉表；4类2×2政策变化和T3的两种Q变化亚型分开统计，并且不把16个轴实例当16个独立run。只有得到严格、可重复的行为异常才可能为独立白盒干预设计目标位置。

## 四、另一个数值指标命名错误：单个原始Gold logit变化不是margin

当前G2 nonregression分支第197行用`logit_new(Gold)-logit_old(Gold)`命名为`new_margin_old2new`。但这**不是Gold与竞争动作的margin**；例如某次输入所有三个动作logits同时增加100，模型决定边界可能完全不动，该差值却大幅为正。应该报告：

`M_Gold(x)=logit_x(Gold)-max_{a≠Gold}(logit_x(a))`，以及`ΔM=M_Gold(new)-M_Gold(old)`；同时保留完整raw logits和严格tie标志。Gold-changing分支除new-vs-old action的分数变化外，也要记录Gold相对**所有**错误动作的强弱，避免第三个动作占优却未显示。

第三Oracle LANL会生成`ambiguous`标志但当前G2没有强制排除/单独报告歧义，实际准入时需与冻结G0全数有效样本对账，而不是简单忽略警告。

## 五、研究决策与备份

当前A461 CPU G0真正双Oracle/token审查已PASS；G1 103次GPU物理执行由执行方报告，仍无GitHub可读的103条logits和对应SHA回读；G2独立CPU分析器代码已开始迭代，未有独立可确认的真实G2统计结果。**必须先上传G1原始证据，修复G2 N2自比较及行动margin定义、输出多头交叉表，再决定是否存在足以开启白盒Q/K/LoRA因果机制实验的模型阳性。** A463仍属于A461否决×法定人数机制细化，不是新增独立GPU方向。

新发现与对应源行已报至[GitHub Issue #2](https://github.com/dddd2024/jev/issues/2)评论`6393998687`和`6394006577`。本分析不覆盖执行方任何源文件或实验日志；所有新增结果保存至GitHub `research/analysis/`并独立回读。服务器`~/wjc`与GPT Library双端备份本会话未核验。

本轮分析资源：新模型前向0、GPU0、新SecJev原始DEV/CAL/TEST读取0；仅GitHub归档已有G0数据和G2源码；未连接远端服务器。
