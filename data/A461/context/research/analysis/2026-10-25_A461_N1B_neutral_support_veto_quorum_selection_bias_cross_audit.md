# A461-PSMI / A463-VQPI｜N1B中性对照的选择偏差：不能丢掉法定人数已满足后的冲突否决格子

**核算日期：2026-10-25（纽约）。** 本轮继续独立分析GitHub上并行Agent的G0准备及新N1B构造器，**不重复执行正式G0**，也未加载模型或新读取原始DEV gzip、TEST/CAL。机器可复核逐案例记录、Github Git blob、计算和科学限制见同名JSON。

## 一、最新并行版本已修复崩溃，但科研准入风险并未随之消失

并行Agent先后提交：
- `a06d71e`：N1B CPU等token长度中性对照构造器（Twins T1/T3用相同新增票、不同轮次；Twins T2改为未投票的合法验证者；LANL直接判定`INFEASIBLE_IN_CONTRACT`）。
- `0f80028`：LANL先跳过再取Twins原始state，避免来源哈希查询失败。
- `6ffe680`：T2没有可用新作者时逐行`no_candidate; continue`，不再全轮抛异常；T1/T3没有观察到其他轮次时退化为`candidate_round−1`（若负数则+1）的**新造轮次**。这是相较首次提交的代码有效修复，不能继续报告“当前会因没有候选立刻崩溃”。

最新N1B脚本Git blob `b805221c12d35dd1dbfd1540fa2efd3a15ccc84d`；主G0 runner仍由另一Agent管理，正式运行结果需其独立回执。原计划物理forward脚本先前已确定存在`neutral-vs-old`错误匹配判定，此轮尚未观察到该脚本的修复版本。

## 二、使用8个冻结真实历史state，重新按「state×轴」计9个资格实例

只读旧 `A428 G0A/frozen_model_inputs.jsonl`（Git blob `13adf301dd67c5cc787c72b4b9ace695c52fef4e`）与旧G2预测/Gold（`f02741bb8cfea2f45c1c73c435d90f8cb064cd6b`）。先直接复核旧source-local Gold，再在内存里对来源规则的C（同作者异块冲突）和Q（合法候选票法定人数）做单字段中性修改。**模型推理0，真实新G0合法对0，原生token重新编码0。**

| 分支 | 历史有资格的轴样本 | 最初N1B候选数（无需保证token等长） | 本轮提出的单字段替代中性Gold保持 |
|---|---:|---:|---:|
| T1：wait→accept（增加法定人数） | 1 | 1 | 1/1 |
| **T2：原正常状态→冲突拒绝** | **4** | **1** | **4/4** |
| T3：已有冲突继续稳定拒绝 | 4 | 3 | 4/4 |
| **合计** | **9轴实例、8个旧scene** | **5** | **9** |

**T2最严重：** `A428_004`（run-220）、`A428_005`（run-272）、`A428_006`（run-68）的Gold原本全是`accept`，新增可信异块冲突票后的Gold应当`reject_conflict`。但这三个old state中的**每个验证者已经在当前轮次投过合资格票**，新N1B T2必须找到“当前轮次完全未投票的合法验证者”才能构造neutral，所以**全部三个样本被它按`no_candidate`跳过**。唯一N1B初始可构造的T2旧场景`A428_001`则为`wait→reject_conflict`。

这不是已经证明全DEV的分布或模型错误率，而是在旧实际样本上暴露的**结构性选择机制**：若仅用有fresh作者者作为中性可配平人群，可能直接排除研究A463/VQPI最想评估的`(V=1,Q=1)`否决主导格子。后续须按`old Gold × veto/quorum cells × source group × N1B candidate status`报告attrition和幸存范围，不能只报总体matched数。

另`A428_009`（run-125）原source仅看到round4。更新版N1B的T3会造round3，可能符合字段模式，但**原scene从未观察到该轮次**。独立验证目前只检查`round != candidate_round`，不能据此宣称原生已观察轮次或来源可信性。应与真实`observed_round`对照分开报告为`SYNTHETIC_UNOBSERVED_ROUND`，独立复核真实输入合同后才能决定资格。

## 三、真实旧state上的规则Oracle表明替代中性构造有可行的研究入口

本轮直接从相同的8个旧真实state构造**只改变处理臂一个字段**、并保持当前被评估的源内全部Oracle标签`conflicting_vote/quorum/certificate_action`不变的替代候选：

- **T2（4/4）**：保留新增异块票的author、block、kind、received，仅把`round`改成**该old scene中实际出现过的另一个round**。这样新票不参与当前候选轮次C/Q，四个旧Gold不变，包括上述三个最重要的`accept→reject`样本。
- **T1（1/1）**：保留新的fresh-author、round、kind、received，只把投给候选块的`block`改成old scene中已出现的另一块；该票不增加候选Q，原`wait`保持。
- **T3（4/4）**：同样让fresh-author投已出现的其他块，不再增加候选Q且已有C无法被删除，原`reject_conflict`保持；对`A428_009`无需制造不存在于该old scene的round。

以上**9/9仅是一个独立写出的浅层当前轮次规则Oracle成功，不是正式G0**。没有做官方模拟器来源权限/时间/签名验证，也没有两条完全独立Gold实现、没有模型renderer/native-token数据。替代的一个字段虽然语义上足够令Gold保持，但是否与处理臂真正等token长度必须由真实原生模型编码确认，*字符宽度相等不保证token等长*。不得把9/9上升为9对已批准实验、更不得在看到新模型结果后挑选这些controls。应该由执行Agent在新模型推理前将备选策略明确登记为**N1B_V2协议增补**，独立验证后按事实解释，保留旧V1失败审计。

## 四、其它仍在的准入限制

1. 新N1B脚本依然调用`checkpoint.load("cpu")`，报告`cpu_model_loads=1`；冻结V1的G0资源合同`model_loads=0`。这不是GPU前向，但须有正式新版本的CPU内存/权重加载许可或改用真正无权重token编码。
2. 新N1B即使全体token不配平，也可终态为`COMPLETE_A461_PSMI_G0_N1B_CPU_ONLY`，所以**工件生成成功≠至少一个有效matched控制成功**；独立verifier参数`--n1b`目前是可选的，必须在最终G0验收里证明带此参数、未使用`--skip-render`。
3. “LANL所有窗内失败事件都会改变布尔B”这一N1B注释不正确：当B已有true、再次增加失败时B保持true。这不会自动证明有可行的LANL等token中性臂，但`INFEASIBLE_IN_CONTRACT`不能仅凭这句错误的布尔断言签发；应按L1/L3A分别列出来源契约、可替代控制搜索和具体停止原因。
4. A463的2x2合成政策Oracle与4096组QK双线性恒等式，是A461机制分析的增强控制而非新增模型阳性；此次合格自然Gold因果现象仍为0，已批准GPU依然为0。

**研究决策**：A461继续P1 CPU研究，保留A463-VQPI为其细化；正式A461 G0继续由并行Agent执行，我方只独立审查和归档。当前最佳新增量是**找到了中性对照构造机制会丢失最重要否决/法定人数格子的可复核证据，并发现可修复这一缺口的原生来源条件**。只有正式双Gold、token等长、source group及无歧义原生控制完整通过后，才能进入申请G1行为pilot的环节，更不能因新增4/4静态控制而申请GPU。

**运行与归档声明**：本轮没有新SecJev模型forward/GPU/训练，未读新TEST/CAL或原始DEV gzip，仅回读既有旧真实模型输入与GitHub新增脚本。服务器`~/wjc`与GPT Library备份未核验，文档只在GitHub新增独立`research/analysis/`路径，不覆盖执行Agent任何脚本和协议。
