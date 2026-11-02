# A461-PSMI｜并行Agent G−1新签发时序审计与三种不可混淆的策略证据效应

**研究日期**：2026-10-25（America/New_York）。审查时主线最新在`5871f1f6fd5c0b04bc4290e2a34768a8f6f709a0`，由另一研究session提交。**本文件只读既有原始Github冻结证据，不覆盖另一Agent任何protocol/G−1，也没有学校服务器、原始语料新扫描、模型调用或GPU。** 同名JSON记录逐项证据、来源、算术和状态。

## 1. 新G−1是实质性推进，但不能追认已登记的旧protocol

在2026-10-25 04:00:46Z，另一Agent提交了`research/literature_preflight/A461_20261025_POLICY_SEMANTIC_MONOTONICITY_CPU_G_MINUS_1/G_MINUS_1_PRIOR_ART_AND_NOVELTY_DECISION.json`（blob`e0f5a631835274b886b6ae67b51f471339414f17`），决策`NOVELTY_DELTA_TESTABLE`，**适用范围严格限定CPU G0准入设计，不授权GPU**。这是相较旧的`HOLD_PRIOR_ART_INCOMPLETE`有意义的状态更新，未来判断不能继续声称仓库缺少A461-G−1文件。

**过程冲突**：GitHub file-path commit历史显示`research/literature/A461_20261025/A461_experiment_protocol.json`首次提交`a930540088423af01a7c7d98850cdbd6241dc415`，2026-10-25 **02:38:42Z**；G−1首次提交`5871f1f...`，**04:00:46Z**，晚**82分04秒**。新报告文字声称“任何A461-PSMI协议冻结之前”并不符合存档事实。因此不能将旧protocol追溯标成先文献再协议PASS；正确做法是保留旧协议为历史未执行草案，后续真正新G0需在新审查已存在的条件下**明确冻结新版**，签发与执行日志独立回读。

## 2. 本次进一步直接读取了最强论文的实际HTML全文

- **One Word Opens the Gate: The Option-Channel Attack on Typed Decision Models as Agent Guardrails**：`https://arxiv.org/html/2610.12292v1`，直接核对§3、§4、§5、§7.1、§11。该文在**6种可精确规则判断的GuardBench政策**上研究typed护栏，明确区分fail-open/fail-closed和baseline-clean-correct攻击成功。尤其§7.1显示：把政策字段解析成可信typed值之后，**直接确定性规则在其6个测试政策达到100%准确率**。这**不是SecJev Twins/LANL的实测准确率**，却提出了A461不可回避的竞争问题：在已有源内可执行规则、干净结构化字段的场景，直接使用Oracle便可做到该源政策语义精确判定，为什么还需要将模型充当该规则的最终决定者？若论文声称部署安全增益，必须有额外的感知/抽取/缺失证据等需要模型推理的真实工作；否则应把贡献限制为SecJev的**模型失效机理/结构一致性审计**。新G−1之前仅核过该篇摘要和间接研究概述，本轮弥补全文读取不足，**没有推翻其对不同机制和任务的初步差异判断**。
- **Monotonicity as an Architectural Bias for Robust Language Models** `https://arxiv.org/html/2602.02686v1`，直接看FFN约束、T5-small总结与HotFlip结果；限制架构单调性和测量真实SecJev源策略单调性是两种对象。一般单调性概念已非创新。
- **SecJev v2** `https://arxiv.org/html/2610.03073v2`，原论文§4.1、表11：原native Twins/LANL规则Gold、独立typed question、源组划分已存在；提供独立政策重算背景，而非A461模型漏洞先例。论文明确LANL为post-event**triage**（不是实际授权拒绝）。

因此**新审查`NOVELTY_DELTA_TESTABLE`可用于新版CPU G0设计**，但“已解决原始决策是否违反策略单调性”仍是待证命题；同行对本次新源干预是否合法和是否需要模型应另行审核。

## 3. 重新从A427历史328条派生Gold计算8个潜在格子：其中仅5格在DEV出现

原有A427 V2派生Gold JSONL blob `af2e68efff36a604b635bdf9402324a6ecf36508`，旧R0原始来源记录完全不重跑。记(B=1)表示近窗失败次数≥5，(S=1)表示不同失败目标≥3，(F=1)表示当前登录失败，(R=B\lor S)。

| B | S | F | 源内Gold | 既存DEV记录 |
|---|---|---|---|---:|
| 0 | 0 | 0 | continue_monitoring | 185 |
| 0 | 0 | 1 | record_failed_attempt | 66 |
| 0 | 1 | 0 | investigate | 0 |
| 0 | 1 | 1 | investigate | **3** |
| 1 | 0 | 0 | investigate | 0 |
| 1 | 0 | 1 | investigate | 64 |
| 1 | 1 | 0 | investigate | 0 |
| 1 | 1 | 1 | investigate | 10 |
| **合计** | | | | **328** |

**新辨识限制**：77条`Gold=investigate`均以**当前登录失败**作背景，没有`F=0,R=1`的原始DEV样本。因此如果修改“当前登录结果”还想证明同一风险顺序，就从已有自然支持跳出了；需要另行验证新语义状态合法性。3条真正由独立目标数触发`S=1,B=0`仍全部来自`lanl:day:50`，不能视为3个独立源组。

## 4. 一个决定性的研究定义问题：Gold改变、Gold保持与中性扰动是三个不同估计量

**(A) Gold改变时的策略响应性。** 旧真实DEV中31条（3日组）位于已知失败数4、目标<3的B边界，22条（2日组）位于已知目标数2、失败数≤3的S边界；若能在**原生合同**下合法追加一个可信、窗口内事件，分别令`B:0→1`、`S:0→1`，则两臂Gold从非investigate→investigate。原模型若clean正确、编辑后仍预测原非investigate，属于**未能响应Gold变化**；它不是严格的“风险证据增加后预测反向降级”（因为预测可能根本没变）。要独立报告，不可写成单调性逆转。

**(B) Gold保持时的真正风险非回归。** 旧真实DEV中已有**77条（3个日组）`R=1`并且Gold=investigate**。在其上合法增加另一条可信窗内失败事件而其他政策条件不变，R仍为1、Gold仍investigate。如果模型原来输出investigate，追加后反而输出record或monitor，才是**最直接、严格的策略非回归违例**。这一条原生候选支持是本轮新发现；**77只是可考虑的基础状态数，不代表存在77个合法编辑、验证通过或错例**。其中74条B触发、另外3条S-only来自同一day:50。

**(C) Gold保持时的无关时间/格式轴。** A428旧实测的`A428_021`与`A428_024`属于相同原生模板、同`lanl:day:48`与Gold（record failed），差异只在4个`seconds_before_current`值；原生token数**631 vs 633**，预测分别错误investigate/正确record，`z(investigate)-z(record)`变动3.5760。因此，它是**尚未长度配平的自然模板线索**，不是同一原始scene的受控反事实；今后必须另立**同场景、Gold不变**的中性时间变更/等原生token负对照。

不能用三类的不同分母计算一个笼统“安全单调性违例率”。至少冻结：

1. 主端点`Y_nonregression`：clean正确的`R=1`原生scene做合法可信单事件增加后，模型是否**反而从investigate退至非investigate**，按来源组聚合。Twins另用自己的C/Q半序、不能与LANL许可动作合并。
2. 并列端点`Y_response`：`R:0→1`且Gold变化的合法配对上，模型是否响应新Gold；clean正确的基线缺口与非单调违例分开。
3. 负对照`Y_nuisance`：Gold保持、R不变、仅变时间/格式的等token或报告不等token样本上，动作是否错误翻转；另记录logit margin和token长度、首差分位置。
4. 如果Gold必须先由可信源内规则完整计算，增加`rule-only baseline`。其性能在源内Gold定义上是定义性上限，并非独立部署安全保障。论文目标必须说明为何模型在原生任务上仍有不可替代功能，或把研究明确定义为表征归因而非部署防御。
5. 同源日组不是独立新环境。77高风险原始场景只来自day48/49/50三个日组，不要当77组置信区间或补齐第二来源族。Twins仍须单独验证policy-valid新配对与严格本族端点。

## 5. 并行执行及正式下一步

当前有效信息：

- 另Agent **G−1决定为CPU-only `NOVELTY_DELTA_TESTABLE`**；我方历史旧文本里`HOLD_PRIOR_ART_INCOMPLETE`应作为当时状态，不能继续当当前仓库“没有G−1”。
- **G−1时间顺序冲突待新版协议补正**；旧A461 candidate protocol 02:38:42Z，G−1 04:00:46Z。不要重写历史。
- **G0原始双臂合法编辑、双Oracle、真实token冻结仍为0对**；3090 GPU许可为0小时，旧FP32事实是来源内普通动作错，不是本研究新结论。
- 若另Agent下一步提交新版A461协议或实际CPU工件，先独立读取其`git commit`、source SHA、trace、完整Gold与group分布、程序和回读收据，避免本分析与其CPU构造工件重复。
- 不得使用TEST或事后在CAL挑阳性，不得将dev的既有模型错例再次当独立确认；新版本协议要明确合格停止条件`STOP_NO_RULE_PRESERVING_PAIRS`、`STOP_NO_STRICT_CLEAN_TO_NONREGRESSION_ERROR`、`STOP_ONLY_GENERIC_NUMERIC_FORMAT_SENSITIVITY`及缺少第二来源族`STOP_SINGLE_SOURCE`。
- **正式A461原候选名称仍为**`A461_20261025_POLICY_SEMANTIC_MONOTONICITY_CPU_G_MINUS_1`；本轮不自造一个声称已获准的新G0/GPU实验名称。

本次仅重读328条**历史派生Gold**、GitHub原文+论文HTML；未直接读取任何新的原始TRAIN/DEV/CAL/TEST语料行、模型FP32重放或GPU/训练。新工件只增加`research/analysis/`独立路径并GitHub回读，学校服务器`~/wjc`与GPT Library双备份未核验。
