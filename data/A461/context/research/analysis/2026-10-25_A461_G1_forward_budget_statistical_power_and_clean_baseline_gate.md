# A461-PSMI｜128次GPU前向预算、负对照开销与小来源组统计效力审计

**日期：2026-10-25，纽约当地。** 研究边界：只读已经冻结的 GitHub V1+V2 G0 协议与旧A428原生FP32来源内Gold/预测；未启动被交给并行Agent的G0；无新模型推理、GPU或学校服务器操作。本报告为独立预算/统计设计审计，**不是对当前G0规范的静默修改，也不授予GPU权限**。结构化复核与计算公式见同名JSON。

## 1. 并行 Agent 当前状态

GitHub Issue [#2](https://github.com/dddd2024/jev/issues/2)（执行交接）在本次检查仍 **open、assignee 为空、comments=0**；实验正式G0 runner与独立verifier所在的`research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/`尚在当前HEAD返回404。最新交接文件commit `f07d206`。这证明任务已存档，**不能证明执行Agent已读到、接单或已在远端启动**。未来新的执行/失败产物以实际git HEAD、服务器receipt为准。

V1协议Git blob `2519620e105bd8fadcae17fb20b1e6026608b0c5`，V2追加独立非回归L3A blob `470349015b8d13c831db4afe3268187e9feb9871`。这两份是本审计唯一预算合同来源。G−1允许CPU G0；GPU当前合法预算为**0**。

## 2. 预算存在“每行两个arms”与“是否去重执行baseline”的解释缺口

V1描述未来pilot上限`128 native forwards`，且`pair_budget.hard_cap`明确“pair+control rows 每行两臂”。既然每个真正干预有一个同源旧臂，且每个负对照亦产生自己的 old/new row，**不在运行时去重时**单个原scene物理成本为：

- Twins **T1/T2/T3**：处理(old,new)2次 + N1中性(old,new)2次，合计 **4次模型前向/原scene**。额外可行的Twins N2尚未计。
- LANL **L1**：处理2次 + N1中性2次 + N2时间对照2次，合计 **6次/原scene**。
- LANL **L3A**（V2）：处理2次 + N1中性2次，合计 **4次/原scene**；如要求额外N2会更高。

按V1的上限候选（**上限不等于承诺全部执行**）：Twins T1=8，T2=8，T3=6，共22个分支候选，预算至少`22×4=88`；LANL L1=每组上限4 × 3个历史阳性日组=12，预算`12×6=72`；合计 **160次**，超过128次**32次**。V2尚未明确冻结L3A单独总配额，若仅为预算示例假设增加12个L3A处理场景、每个仅配N1，则再增加`12×4=48`次，总计**208次**，比原上限多80次；这**不是已确定的新配额**，而是条件性上限试算。

另一极端是同一原scene baseline的重复臂按**确切native请求哈希**安全复用一次，不每条control pair都重新推理：Twins3次、LANL L1 4次、LANL L3A 3次。则V1候选`22×3+12×4=114`次，可在128以内；V2加入假设12个L3A后共**150次**，依然超22次，且都**没有计入baseline精度重放、Hook、Twins N2、重复随机种子等**。所以**G0不是只要找到合法pair就能认为GPU预算足够**；还必须提前冻结每个case的unique-native-input-hash与每次实际模型执行、缓存/重放是否可复用的规则，不能事后按实验结论改预算。

纯算术上的一个128次可行示例（**仅说明可调整、不是预注册新版协议、无实际资格审查**）：Twins T1=2、T2=6、T3=6，共14scene×4=56；LANL L1=6×6=36；L3A=7×4=28；留8次用于重放。**56+36+28+8=128**。该例缺少足够T1跨组检验，也没有证实原始数据能提供这些数量；建议执行Agent按真实CPU G0的合法对数与组数，在任何G1 GPU批准之前重新冻结目标配额，而不是直接采用此示例。

## 3. 旧FP32复核揭示“达到Gold资格”和“基线正确”不能混同

旧A428 G2 原生结果（blob `f02741bb8cfea2f45c1c73c435d90f8cb064cd6b`）已在前一轮对旧12个Twins场景进行静态规则资格检查，T1只有`A428_001`，T2有`A428_001,004,005,006`，T3有`A428_007,008,009,010`。本轮再独立核对其**真实老模型Gold与old预测**：

| A461分支 | 旧影子资格 | 原旧模型Gold=预测（clean-correct） | 已错误的old-arm |
|---|---:|---:|---:|
| Twins T1 | 1 | 1 | 0 |
| Twins T2 | 4 | 4 | 0 |
| **Twins T3** | **4** | **1（A428_007）** | **3（A428_008/009/010）** |
| LANL L3A（旧12条LANL样本中的3个资格起点） | 3 | 3 | 0 |

V2的`GOLD_INVARIANT_RISK_NONREGRESSION`主终点是“old-arm原本正确，追加合法正向风险证据后new-arm转为错误”。因此**历史T3的三个原本已经错误的候选绝不能计入这种clean-to-wrong事件**，而要另列baseline错误、改善、不变。T1/T2如Gold合法发生变化，基线正确仍须单独报告，不能把“模型没有响应Gold变化”自动认定为“输出发生了逆向非单调翻转”。

**限制：** A428旧样本本来就非随机且已反复查看，T3的1/4 clean不代表全体797个Twins DEV中clean率25%，也不能以A428先验清洁性挑选新确认数据。未来G0基于source/Gold/资格条件冻scene，G1单独报告实际clean基线分母与来源组，而不按已见模型预测事后决定统计总体。应将旧FP32作为烟测和独立回放参考，不作为全新的确证阳性。

## 4. 小样本统计：与格式对照的比较，需要足够独立的discordant pair

假设未来“同一个原scene上的策略真实增量”与“同一个原scene上的token配平中性增量”可以构造可解释的二元动作正确/错误，并且分析单位之间近似独立。则二元配对McNemar精确检验只依赖**处理错误、对照正确**与**处理正确、对照错误**的discordant单元数。最理想情况下若`k`个discordant全部支持处理臂使错误更多、没有反向单元，则**双侧精确P = min(1,2×(1/2)^k)**：

| 互相独立、方向全同的discordant对 | 双侧最小P |
|---:|---:|
| 3 | 0.2500 |
| 4 | 0.1250 |
| 5 | 0.0625 |
| **6** | **0.03125** |

这不表示做6对就能显著：必须先有6个确实discordant、方向全同且独立的对；超过一个反向单元/同组依赖/多重检验/候选事后筛选都会改变P值与结论。**现阶段从未运行这样的新pair，以上是预算/功效最低阈值的代数示例，不是实验P值。** 小discordant计数须采用精确配对检验而非大样本近似，参见 StatPearls McNemar介绍及 [StatsDirect exact matched pairs](https://www.statsdirect.com/help/chi_square_tests/mcnemar.htm)。

与之同样重要的是**来源组相关性**。旧LANL DEV真正Risk Gold=investigate的77条全部集中day48/49/50**仅三个日组**；即使每组抽10条也不是30个独立日组。MacKinnon、Nielsen、Webb，《[Cluster-robust inference: A guide to empirical practice](https://doi.org/10.1016/j.jeconom.2022.04.001)》，明确说明少量cluster、样本量不均衡时常规渐近置信区间不可靠。若仅有三组，无论使用小样本bootstrap还是场景级P值，都不应声称跨日稳定的确认性结论。

另用独立Bernoulli场景的纯数学模型说明零阳性也不意味着排除错误风险：如果有0/12独立测试阳性，单侧95%精确上限仍约**22.09%**；如果只有0/3独立的日组级阳性，类比上限高达**63.16%**。这些只是条件算术，不能把同日样本直接当IID场景或把组当实际二值试验。**G1更合理的定位是有限预算寻找/筛除显著严格行为信号的探索性pilot，不能自动等同已独立确认论文发现**。

## 5. 为GPU前的CPU验收增加一份明确的物理预算审查

不干扰并行Agent的G0开发，建议让它在正式G0回执中提供：`physical_forward_manifest.json`，至少字段 `source_family, source_group, axis, original_scene_sha, arm(role=old/treatment/N1/N2), native_request_SHA, original_rule_Gold, new_rule_Gold, token_count, token_sha, N1_equal_token_count, query_choice_order, model_precision, intended_forward_count, cached_baseline_policy, repeated_baseline_precision_replays`。这个文件**只由CPU构造，不运行GPU**。

GPU核验要求：每个被计费的独特模型前向与重放次数可从manifest精确加总≤128；若同一old-arm跨control重复，只有在同版本、同输入token id、同选择顺序和推理配置且允许复用的情况下才可计一次；不合格N1对照不能被强行当“matched”。将`X_response`（Gold改变）、`X_nonregression`（Gold不变）、`X_nuisance`（Gold不变的格式）三类统计分开，报告`old_clean`分母/每source group显著性，留出confirmatory独立验证才可在论文主张跨族机制。

**当前实际状态：** G−1对新版CPU协议已具备合法前置决定；新CPU G0在Issue #2尚无认领及归档执行回执；实际双Oracle pair=0，现有已批准GPU=0。以上风险不要求立刻批准增加GPU预算，但若不先固定资源与对照计量，就可能在G1把无法实施的全部配置误当成完成的验证。

**独立资源账本：** GitHub现有协议、旧A428派生FP32样本与Issue只读；服务器访问0、新原始SecJev语料读取0、模型前向0、GPU0、训练0。新增审计归档只占用GitHub，未完成服务器/GPT Library SHA双备份。
