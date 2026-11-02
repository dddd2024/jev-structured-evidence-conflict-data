# A461-PSMI / A463-VQPI：真实G0四格策略边覆盖、T3法定人数交互与共基线双干预

**日期**：2026-10-25（America/New_York）。**性质**：只读已归档的A461真实CPU G0源内Gold、原生token长度和N1B记录；没有运行SecJev模型、CPU G0、GPU、训练或新原始DEV数据。本轮实际15种旧state前缀、16个Twins轴实例、8个独立run组的聚类结构由GitHub冻结JSONL直接计算。逐pair证据和Git blob见同名JSON。

## 1. 先基于真实源内Gold重建C×Q，而非继续只使用实验标签

记 **C=1** 为同一候选投票者在同轮对不同块投票（来源规则意义上的冲突），**Q=1** 为来自不同有效验证者的候选票达quorum。源内certificate action的确定性判定为 `C?reject_conflict:(Q?accept:wait)`。注意这只是**Gold规则、不是SecJev模型预测**。

| C | Q | 正确动作Gold |
|---:|---:|---|
| 0 | 0 | wait |
| 0 | 1 | accept |
| 1 | 0 | reject_conflict |
| 1 | 1 | reject_conflict |

在`G0_REAL_20261025/pair_rows.jsonl`逐 `pair_key` 联结`new`与`neutral`的冲突和法定人数Gold，再通过`token_audit.jsonl`核对new/neutral原生**state-token总数相等**：

| 已冻结配对的C,Q变化 | 例数 | 等token长度 | 所覆盖source run组数 | 正确动作变化 |
|---|---:|---:|---:|---|
| 00→01（C=0, Q跨阈值） | 6 | 6/6 | 6 | wait→accept |
| 00→10（Q=0, C跨阈值） | 4 | 4/4 | 4 | wait→reject_conflict |
| **01→11（Q=1, C跨阈值）** | **2** | **0/2** | **2** | **accept→reject_conflict** |
| 10→11（C=1, Q跨阈值） | 2 | 2/2 | 2 | reject_conflict→reject_conflict |
| 11→11（C=1, Q不变） | 2 | 2/2 | 2 | reject_conflict→reject_conflict |
| **合计** | **16** | **14/16** | **8个不同run组（并集，不是各行求和）** | |

因此**四种2x2相邻变化在Gold层面齐备，但严格等长度控制只覆盖其中三种相邻变化**。缺失的是A463-VQPI最值得检验的`C0Q1→C1Q1`，分别来自`twins_streamlet:run-100`和`run-125`。此前N1B 14条恰好覆盖14条已等长度的原生N1，无法补这两条。

## 2. 旧的T3不只是“泛中性扰动”：其中2/4是准确的C固定、Q增加

逐行比较已执行的T3`new`和`neutral`：
- run105、run125的两条：`C=1,Q:0→1`，源内Gold始终`reject_conflict`。这是可用来检验**在已存在冲突否决时，增加quorum不应恢复accept**的非补偿性优先级，而不只是无关文字干扰。
- run114、run129两条：`C=1,Q=1→1`，Gold仍`reject_conflict`，更接近Gold不变的额外合法投票稳定性检验。

两类不能全部汇总成一种无变化控制。前者改变**auxiliary quorum Gold**，虽然certificate action不变；后者连quorum也保持不变。之后如出现native action翻转，必须结合`quorum`与`conflicting_vote`独立模型头的logits定位解释。如果预测Q或C本身就偏离源内Gold，则可能是事实读入问题；如果两个辅助头Gold都正确但action错误，则优先排查动作整合/读出。但**仅凭多头不一致是观察性证据，仍不是MLP/QK的因果归因**。

## 3. 一个真正的共原始状态双干预：run121

`twins_streamlet:run-121`同时对应
`TWINS_T1_QUORUM_AXIS:e5b68bed342aaa85` 和 `TWINS_T2_CONFLICT_AXIS:e5b68bed342aaa85`。

不只是来源组标签相同；本轮把两条`new`请求中按`declared_edit.message`追加的消息分别移除，并对恢复的**整个旧state做结构一致性核对**；两条旧state相同、同一native questions菜单。原始`C=0,Q=0,Gold=wait`，从这一**同一个状态**向两个方向合法增加证据：
- 只推进quorum：`(C,Q)=(0,1)`，Gold应`accept`；
- 只触发冲突：`(C,Q)=(1,0)`，Gold应`reject_conflict`。

这是真实G0数据中最干净的**common-baseline fork**，适合将来观察同一基线下SecJev不同typed决策头的响应与干预路径；但只有**一个基础state/一个run组**，不是两个独立实验，不能把它称为完整同状态四角因子实验，更没有任何新的模型预测或机制阳性。

## 4. 推论与GPU前分析方案（不单独申请/执行新GPU）

实际16条Twins轴实例只来自**8个source run组、15个不同old state SHA前缀**（T1与T2的run121共用一个）。把每条都当IID并做16个独立Bernoulli检验，会严重高估独立证据量。特别是核心`01→11`虽然有2条来源run，但**0条严格token等长对照**。当G1真实logits出现，应冻结各组的`source_group`和`Gold(C,Q,A)`后，逐边报告：
1. 基线`action`是否clean正确，新增真实证据后动作是否偏离新Gold；Gold-changing响应缺口与Gold-invariant回退分别计算。
2. 处理与同源中性臂的动作差异，并按`TOKEN_COUNT_MATCHED`分层；尤其不能拿00→10代替01→11。
3. `conflicting_vote`和`quorum`头对各自Gold的正确性与`certificate_action`头错误的交叉表；明确是感知读入头错误、模型内部动作整合不一致，还是两者都偏离。
4. 多头观察模式得到严格正例后，再考虑有理由、双向反事实的Q/K或LoRA干预；**不得因为Gold四格具备或token等长就认为白盒机制已证明**。

执行职责仍属于 [GitHub Issue #2](https://github.com/dddd2024/jev/issues/2) 的并行Agent。CPU G0真实Gold/tokens已经通过独立实现技术核验，但仍有历史CPU模型加载合同勘误、N1 manifest错误和新G1程序可靠性问题。**本报告不要求另起方向、扩容GPU或绕过许可**。

**资源记录：** GitHub的真实G0归档只读，研究分析无新模型forward/GPU/训练，未读取新SecJev原始DEV或TEST/CAL，未登录服务器，也未独立完成GPT Library/服务器双备份。
