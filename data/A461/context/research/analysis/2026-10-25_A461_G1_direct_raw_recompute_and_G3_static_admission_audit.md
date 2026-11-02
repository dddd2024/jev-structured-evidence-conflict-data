# A461 G1 真实原生 logits 直接复算与 G3 静态准入审计

日期：2026-10-25；研究仓库：dddd2024/jev；类型：只读历史数据复算 + 冻结G3代码静态审计。**没有新的GPU/模型推理，没有服务器执行，没有访问TEST/CAL；本文件不改变G0/G1/G2原始证据或G3已冻结协议。**

## 1. 数据来源与核查口径

- 原始G1：`research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/G1_REAL_20261025/raw_native_logits_103_requests.jsonl`；Git blob SHA1 `5b4a6903171d0a5848162a335530492f6e1a6046`。
- 来源 Gold / native requests：`.../G0_REAL_20261025/pair_rows.jsonl`；SHA1 `24526c643434544b9a02587abc2d57e2c13ef627`；65条old/new/相关记录，31个主研究配对。
- N1B来源记录：`.../G0_N1B_REAL_20261025/n1b_rows.jsonl`；SHA1 `02342e1dc0a188dd7390d0fd911710d29622a358`；14条。
- 已有派生分析：`research/analysis/2026-10-25_A461_G1_three_arm_logit_specificity_and_sham_dominance.json`；Git blob SHA1 `7bed6f005ba0ae6dc23636a6d53ea7b5937e3e05`。
- G3构造器：`research/rounds/A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE/A461_g3_conflict_gate_cpu_v1.py`；Git blob SHA1 `b62b9996c3daa46b578af9b22bc9252bfb061906`。
- G3独立核验器：同目录 `A461_g3_independent_verifier_v1.py`；Git blob SHA1 `a0e69f3fc3a5ce30c187eecce82d245df92086df`。

本轮通过GitHub原文件直接解析G1每条`questions[].keys/logits`，以`pair_rows`的`row_id`匹配treatment、`pair_key:old`匹配old、以N1B的`row_id`匹配neutral，重新计算`logit(true)-logit(false)`，不以既有分析JSON中的margin作为原始输入。得到原始103条：34 old，31 treatment，14 N1B，17 N1，3 N2，4 replay，与历史收据一致。

## 2. 直接逐行复算的Twins T2六个来源组

| run | old动作 | new动作 | new C | new Q | new evidence_level | new C margin (true−false) | 同源N1B控制的D_C |
|---|---|---|---|---|---|---:|---:|
|100|accept|accept|false|true|0|−1.680|无|
|101|wait|wait|false|false|1|−8.255|−1.075|
|105|wait|wait|false|false|1|−9.469|−0.535|
|114|wait|wait|false|false|1|−5.717|−0.311|
|121|wait|wait|false|false|1|−4.505|+2.097|
|125|accept|accept|false|true|0|−11.296|无|

六条treatment独立来源Gold均为`conflicting_vote=true`, `certificate_action=reject_conflict`, `evidence_level=2`。**C判错6/6、动作错误6/6，但此处不是六对中性对照；严格中性对照仅四组。** 模型quorum问题都正确；C/Q/A是单独渲染、共主干的三个问题，不能从输出一致性推断C神经中介导致A。

Q=1（old accept）两条新状态冲突判断margin分别为−1.680与−11.296，差异达到9.616 logit，且均无N1B实测中性臂；不得把它们视为相同置信程度的失效。T2六条新冲突预测true的成功率0/6也不代表未见总体上的准确率为零。

## 3. 来源组敏感性/leave-one-out（仅探索）

四条有N1B控制的T2，(D_C=M_C(treatment)-M_C(N1B))依次为run101 −1.075、105 −0.535、114 −0.311、121 +2.097；四组均值 +0.044。四组同原生问题、同候选菜单，N1B与treatment状态token总长匹配；总长匹配不代表位置和token内容完全一致。

逐一排除来源组后的 (D_C) 均值：
- 去101：+0.417；去105：+0.237；去114：+0.162；**去121：−0.640**。
- 对动作margin的特异性 (D_A)：全四组均值 +0.059，**去121：−0.253**。

该分析表明均值符号严重受单一run121影响；不能进行后验子集显著性主张，也不能据此宣称T2在未见来源组语义特异性为零。比较LANL-L1的3个day组内D_A均值（+3.345、+2.941、+3.742），三个来源组均为正；但只有3个day组且已被A428接触，不能当作9个独立泛化replication。

## 4. G3构造器/独立验证器发现的准入风险（静态可证，不是实际服务器执行结论）

**P0-1：SHAM_TS 的接收时序几乎必然违背构造器自己的合法输入条件。** 构造器对old来源状态显式要求`received_messages`按`received`非降序排列；真实treatment取`mx=max(received)`追加在末尾。而SHAM_TS选取未使用的`ts_val<mx`，却仍替换新消息的`received`并放在最后。只要old列表含最大时间`mx`（必然），末尾新时间更早就产生降序断点。脚本只核Gold未核编辑后chronology；独立验证器同样重建并比Gold/token，没有逐臂检查`received`非降序。因而SHAM_TS不可作为有效来源时序干预直接计入模型结论。修复：对新消息进行来源允许的时序重排，重新独立验证Gold和token，并确保治疗/中性格式控制匹配，或取消该SHAM及对应GPU臂。

**P0-2：SHAM_RO 反转整个消息列表，在原消息存在不同接收时间时破坏非降序。** 此问题已在先前G3 pre-execution QA确认15/16来源时间违例；新版把RO澄清为treatment-format控制仅修正Gold参照，并未在代码中修复chronology。必须逐臂拒绝/修复，不得把Oracle Gold不变当作来源合法。

**P0-3：T2 N1B 的fallback author可能不在`validator_set`。** 构造器在`fresh_voter(...)`不存在时置`author='z_neutral_outside_set'`，而独立Gold oracle明确只统计`validator_set`内投票。此时中性事件虽然不改变Gold，却不符合冻结协议的“合法新validator单字段对照”定义；独立验证器仅核编辑差异、Gold和token，不核N1B作者属于validator_set。建议无合法新validator时标记`N1B_UNAVAILABLE`、该scene不予入场并重选；不可静默转为名单外作者。

**P1-4：SHAM采样有单元格覆盖偏差。** `sham_pairs = T2_WAIT selections + T2_ACCEPT selections`，取首`SHAM_CAP=6`。在原计划十条wait足额时，6条SHAM全来自Q=0 wait场景，Q=1 accept→reject场景没有SHAM覆盖。正是后者为旧实验最关键的缺失控制。建议预注册按两种T2 cell分层（如各3组），保持总SHAM预算不变，更新独立统计。

**P1-5：不同T2 cell的run group被有意互斥。** `t2a_sel`明确排除`t2w_sel`中的run group，因此wait/accept cell差异是跨组比较，不能写成同一来源组的配对2×2因果交互。可保留互斥用于组独立性，但统计报告需明确分层/组级聚合；若要同组2×2应另设设计并核来源资格。

上述静态风险在真正G3 G0C服务器产物上尚未实测覆盖率；“主脚本+独立验证器在替代语料通过”不是这些来源语义合同的充分证明。**建议G3阶段判定：PENDING_SOURCE_CONTRACT_REVIEW；在P0问题修复并有服务器双路径逐臂合法性回执前，禁止将SHAM_TS/RO、fallback N1B视为有效控制；不据现有代码批准模型推理。**

## 5. 最小修正后的入场校验

1. 在构造器、独立验证器均实现每条arm的单调时间与`received<=decision_time`、author合法性（按arm契约）检查；失败`STOP_INVALID_SOURCE_CHRONOLOGY`或`STOP_INVALID_NEUTRAL_AUTHOR`。
2. N1B必须在合法validator内且来源Gold不变；没有可行中性控制的Q=1单元格明确排除或报告，不伪造“匹配”。
3. SHAM_TS/RO必须明确以treatment Gold为参照，同时满足来源实际排序语义；SHAM-SA以old Gold为参照，不混并。
4. SHAM分配显式覆盖Q=0及Q=1，报告真实每cell合格臂数；未达到预注册准入门时停止。
5. 修复后另行冻结新版协议/代码及独立SHA readback，才能开展预算上限内的真实模型G1C；全部统计以未见`source_group`为独立单位。
6. 因新增模型输出仍未发生，本轮不宣称白盒因果、不宣称安全攻击成功或论文创新已成立。

**结论**：旧G1直接复算支持“新增冲突难识别、正确quorum不保证正确冲突识别”；T2语义特异性均值不稳健。G3当前更重要的风险是输入来源合同可能在无提示下失效，而非GPU模型预算不足。
