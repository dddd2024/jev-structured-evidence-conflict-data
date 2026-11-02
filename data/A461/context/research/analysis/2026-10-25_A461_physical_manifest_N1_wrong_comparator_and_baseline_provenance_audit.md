# A461｜并行G0第一次尝试后的独立复核：N1 等长标志反向定义、基线可追溯性和真实GPU预算

**2026-10-25，America/New_York。性质：已提交真实脚本的静态计算审计，不是新的正式SecJev模型实验。** 只用GitHub可回读源代码、Issue ACK和已归档预算/协议；CPU G0执行归并行Agent所有，不代执行、GPU不准入。机器可验证结构化反例/计算见同名JSON。

## 1. 另一个Agent已开始实际试跑，旧「未启动」状态更新

最新日志可证据链：`495dde0`新增G0主程序和独立验证程序；`823e9bd`提交说明**G0 attempt-1**发生row-33原生token SHA mismatch，根因是追加的Twins消息中JSON字段插入顺序在内存和写回之间不同。新增两个canonicalization改动。随后`791d80d`新增物理forward清单生成器，`1e172e2`修复token审计row_id和主表不一致。

**已观察的事实**：执行方确实至少尝试了模型零前向的G0 CPU/token环节、发现并修了一个真正的渲染序列化不一致，且新增了物理预算清单。**未获得的证据**：当前GitHub仍无可独立回读的最终G0 PASS/HOLD/STOP执行回执、双Oracle逐臂审查或真实token配平统计。因此不能宣称CPU G0已通过、原生规则配对已全部验证或GPU已批准。Issue #2现有执行方ACK `status=PREPARING`，与未取得完整终态一致。

A463新材料虽然有 4 个合成Twins 2x2政策格、4096个随机Query/Key双线性代数校验，候选登记明确是`A461-PSMI/A463-VQPI`**合并细化既有主线**，实际原始SecJev DEV新增场景0、模型forward0、GPU0；不得作为额外实验主线或突破。

## 2. N1对照匹配发生确定性的真假反转错误

新增脚本：
`research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/A461_psmi_physical_forward_manifest_v1.py`
，blob `c3dcc1949bdb2e8902689dafbba0ad4e78b33256`。关键表达式当前是：

```python
"N1_equal_token_count": (ta["token_len_delta_vs_old"] == 0) if r["arm"] == "neutral" else None
```

`token_len_delta_vs_old`定义为**该臂与原始场景**的token长度差。它检查的是`len(neutral)==len(old)`，而G−1竞争论文对照和本轮假设需要的是**`len(neutral)==len(treatment)`，同一旧状态/同一family下策略证据增加与中性事件增加严格等长**。

| 原始old | 处理treatment | 中性neutral | 现程序MATCHED？ | 实际应MATCHED？ |
|---:|---:|---:|---|---|
| 100 | 103 | 100 | **是（误报）** | 否 |
| 100 | 103 | 103 | **否（漏报）** | 是 |
| 100 | 100 | 100 | 是 | 是 |
| 100 | 103 | 102 | 否 | 否 |

这是源代码和整数同一性可确定证明的**false positive + false negative**，即使以后独立验证的per-arm token SHA完全一致也无法自动纠正错误的*跨臂比较关系*。需将匹配分组键固定为`(pair_key, family)`，从这一组取`new`与`neutral`的`state_token_len`，记录差异、双路径核验、选项顺序、第一差异位置和匹配状态。等长度必要但非充分；原生token长度完全相等也不能自动消除所有位次/词面混杂。对照不匹配的行只能按预注册声明作为未配平探索，不得视作因果特异性模型阳性。

**严重性**：这是阻断G1「已排除无关token/格式效应」主张的实质数据质量问题，而不是GPU性能/是否能运行的操作问题。已直接通知执行方Issue #2评论`6393585183`。

## 3. 原始基线未独立定锚

该manifest生成器有`old_baseline`行，但写入：
- `native_request_sha256: null`
- `old_rule_gold: null`
- `question_order: null`
- `original_scene_sha`实际上是hash前16字符，不是完整源record SHA256。

然而文件又主张按**exact native request hash**复用同一旧场景的基线前向。没有原始旧臂的完整原生请求及其全SHA，就无法**仅根据此manifest**审计复用的旧臂是否相同、策略Gold是什么、模型候选菜单是否与新臂一致。建议从经SHA固定的原始DEV记录重建old native request，写全量SHA、token IDs SHA、原生old Gold和choices顺序；如不导出原文，应给出完整来源record SHA和程序化可复现的渲染方法，签发独立第二路径回读。

## 4. 当前新CAPS预算并不超128，但必须准确理解103的条件性数字

冻结runner当前最多选择：LANL L1=每个day3、L3A=每个day2、Twins T1/T2/T3=6/6/4、LANL N2=至多3。仅在**三个LANL阳性day组均达到cap**的预算示例下，有31个主分支旧状态、62个new/neutral修改输入和3个N2重定时输入，合计**65个修改后臂**。因为`pair_key = family+old_state_hash_prefix`，N2分支是独立family，可能额外生成3个旧臂清单项，因此manifest的基线行上限**34**；加上预留4次精度重放，合计`65+34+4=103`次**条件性物理前向计划**。

**不是已经跑了103次GPU，也不能从当前仓库证明真实样本达到上述各cap。** 真正G1成本要依据G0实际输出的合法输入数量、真实token N1配平幸存者、唯一完整请求hash、按模型精度和重放预算复核。当前manifest虽给出了`forward_cap=128`，但未明确在生成后`assert total_planned_forwards<=128`；后继若改配额，不能默认仍满足。

## 5. 对后续实验结论的直接约束

- 对**Gold改变**的T1/T2/L1，需证明new Gold正确且中性Gold不变；处理后仍未变更动作是策略响应性缺口，不能混同严格预测逆向非单调。
- 对**Gold不变**的T3/L3A，统计clean-correct基线向错误动作的回退。旧A428 T3影子样本4个中3个旧状态已错，不能算strict clean→wrong。
- 对**Gold不变时间N2**，除了Gold不变还必须守住来源的完整事件时间顺序；前一轮已提供一个合成反例，代码仍需在真实DEV逐臂检查。
- 对物理forward清单，须与程序真实执行输入一一对应，Gold和原生token均可独立回读；GPU许可仍为0。
- 对并行新A463，四格Oracle和指针头QK双线性恒等式只是**现有A461机制对照与方法基础**，不构成另一个GPU队列，也不增加当前真实论文阳性。

**决策**：`HOLD_G1_CAUSAL_MATCHED_CONTROL_UNTIL_CORRECTED_AND_INDEPENDENTLY_VERIFIED`，**不要求停止合法CPU G0对数据和双Oracle的全面检查**。先由执行Agent修复该清单、证据来源和先前runbook问题、签发真实G0 PASS/HOLD/STOP，再在满足已冻结政策、负对照与资源账本之后单独申请GPU。研究本会话不覆写执行方脚本。

**资源及归档**：本轮新G0/model/GPU/TEST/CAL执行0；GitHub只读分析+追加新报告；school server与GPT Library双端备份未核验。
