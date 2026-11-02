# A461-PSMI / A463-VQPI｜实际完成的G0后独立复算：N1真实配平29/31，两个最重要的否决主导格子仍未配平

**日期**：2026-10-25（America/New_York）。**证据类别**：GitHub上已实际执行CPU G0并通过第二实现审核后，对其完整65条`pair_rows`、65条`token_audit`、14条`N1B`和103预算manifest作逐`pair_key`、`row_id`独立交叉复核。没有启动新的G0、GPU、SecJev模型前向、服务器SSH或TEST/CAL；同名JSON包含完整每轴计数、逐例差异、Git blob及自动断言。

## 一、CPU G0真实完成，不应再汇报“尚无执行”

并行执行方commit `bd8d2cf83a5b3dcbc52fda52bbe6a45c161089f3`上传真实`G0_REAL_20261025`、`G0_VERIFY_REAL_20261025`、`G0_N1B_REAL_20261025`及物理前向manifest。主CPU收据`COMPLETE_A461_PSMI_G0_CPU_GATE_IMPL1`；第二独立验证`PASS_A461_PSMI_G0_INDEPENDENT_VERIFICATION`；归档原始CPU交叉核对LANL 328/328、Twins旧示例12/12；实际冻结34个`pair_key`、65个修改后臂，65/65 native token重新渲染一致；14个N1B独立重核一致；**全部GPU前向0**。新的G0 corpus census原生DEV支持：LANL L1 30潜在旧状态（冻结9），L3A 75（冻结6），Twins T1 93（冻结6）、T2 331（冻结6）、T3 77（冻结4），N2冻结3。

**这是CPU准入、来源内规则和序列化技术结果，不是已测模型动作错误或白盒因果机制。** 同时旧G0冻结合同`model_loads=0`但主/第二CPU收据均`cpu_model_loads=1`，需要独立程序化资源勘误，不能将GPU=0视为所有程序门自然PASS。

## 二、N1匹配报告用错了比较对象

实际冻结来源（Git blob）：
- `G0_REAL_20261025/pair_rows.jsonl`：`24526c643434544b9a02587abc2d57e2c13ef627`
- `G0_REAL_20261025/token_audit.jsonl`：`f2bd1e5de0a6cfeb69d9b6e2d90d9979c4e642f7`
- `G0_N1B_REAL_20261025/n1b_rows.jsonl`：`02342e1dc0a188dd7390d0fd911710d29622a358`
- `G0_FORWARD_MANIFEST_20261025/physical_forward_manifest.json`：`f54bac29a1b90b663096ed900b356318062c3c86`

联合方法：逐`pair_key`识别`arm=new`和`arm=neutral`，逐`row_id`联结CPU真实token审计，在native`questions`字段完全相同的条件下判定**`len(state_tokens(new)) == len(state_tokens(neutral))`**。原脚本误定义为`len(state_tokens(neutral)) == len(state_tokens(old))`，故在manifest错误报告`n1_token_matched=0,n1_token_mismatched=31`。**当前原始审计真实统计是29/31匹配**：

| 原生政策轴 | new与neutral真实等长 | 不等长 | Gold含义 |
|---|---:|---:|---|
| LANL-L1-B阈值 | **9/9** | 0 | Gold从record_failed_attempt转为investigate；neutral仍为record |
| LANL-L3A风险非回归 | **6/6** | 0 | Gold始终investigate |
| Twins-T1法定人数跨越 | **6/6** | 0 | wait→accept，neutral仍wait |
| Twins-T2新增冲突否决 | **4/6** | **2** | 4个原wait→reject等长；2个原accept→reject不等长 |
| Twins-T3冲突稳定 | **4/4** | 0 | Gold保持reject_conflict |
| **合计** | **29/31** | **2** | N1B不是上述29的唯一来源 |

源G0冻结文件中，LANL L1输入old约520/521个state token，new与neutral均为580/581；LANL L3A同样new与neutral长度一致。**“全部LANL N1不等长”与“LANL N1 token长度必不可配平”均不受这些实际数据支持。** 但等长度仅排除总token数量这一混杂，不排除有效事件类型文本、字段位置、注意力路径等差异。

## 三、缺口恰好集中在A463-VQPI真正的核心安全判定格子

两条N1未匹配来自：
- `TWINS_T2_CONFLICT_AXIS`，`twins_streamlet:run-100`，源内原Gold`accept`，新增冲突Gold`reject_conflict`；new **1086** state token，neutral **1090**；
- `TWINS_T2_CONFLICT_AXIS`，`twins_streamlet:run-125`，old`accept`，new`reject_conflict`；new **411**，neutral **415**。

这两条测试的是**Q已满足后新增真实冲突V，应否决accept而变reject**的非补偿式否决关系。恰巧T2其它四条从`wait`→`reject_conflict`均已匹配。因此如果未来只对“匹配集”宣称机制，**Veto-after-Quorum最重要的格子会被系统性剔除**，不能把四个wait→reject替代两个accept→reject来证明Q=1情形。

实际N1B `14/14` matched的14条全来自Twins T1 6、T2 4、T3 4，并且它们**逐一属于原来N1就已经等长的14个原始`pair_key`**。N1B可作为另一种中性事实变化的独立*方法学控制*，但**在补齐新/中性等长资格这一指标上的净新增覆盖=0**，仍没有处理上述两条旧Gold accept。

先前针对旧A428八个场景的静态单字段Gold分析建议：T2把新增异块票`round`改到该old scene确实观察过的其他round，有望保持原Gold并避免新作者不可用；但它仅是旧state浅层来源Oracle可行性，**尚未在本次两个新G0场景完成true native tokenizer/独立来源资格审查**。任何新中性臂方案需在G1之前独立登记版本、复核协议和按source group报告损耗，不得在看到GPU预测后临时选择成功方案。

## 四、真实N2验证、独立单位和物理forward账本

旧理论反例曾证明N2只调整失败事件时间、未重新排序可能破坏完整chronology。**但本次3个真实N2冻结臂**分别位于LANL day48/49/50，变更delta均为+1；输出完整年龄列表为
`[234,152,79,70]`、
`[232,156,148,78]`、
`[235,155,79,75]`。
各自严格降序、时间互异且均在合法时间窗；原来的**潜在源码问题没有出现在这三条记录中**。不能把合成反例算作真实invalid或取消已验证G0 N2审计。

预算manifest `34`个`pair_key`的old_baseline中所有`native_request_sha256=null`、`old_rule_gold=null`，同时旧state哈希前缀去重实际只有**30**种。四次重复中三次是LANL N2重复L1 old scene，一次是同一Twins old scene跨T1/T2分支。原计划`34 old +65 modified +4 precision replays=103`次，算术可在128条件上限内；但`34 old`并不等于34个独特原始state，且**state哈希前缀≠完整native request/token IDs hash**。基线复用需要每臂同版本、相同原生问题配置、实际token SHA和推理精度核对，不可仅凭30这个数字宣布可以跳过4次物理模型推理。

## 五、最新G1代码与“批准”证据必须区别于本次实验结论

最新并行提交 `aee53628d902b7f0f9a385fb280202c708209444` 新增G1 FP32 runner与`admission_receipt_a461_g1.json`。回执**自述**另一个ZCode会话中用户已明确批准103次GPU forward，并载入run_id、模型、禁项；本独立会话没有访问那次用户批准交互本身，**既不否认其可能确已授权，也不将仓库自填文字单独当作已验证批准证据**。当前尚未观察到G1实际模型forward结果或GPU终态。

**更关键是G1前向计划仍基于错误的旧统计！** 代码`n1_keep = n1_all[:17]`并把其角色命名`N1_unmatched`。按照已存档manifest的真实顺序，17个N1恰好是**9个LANL L1＋6个LANL L3A＋2个Twins T1**，它们**17/17真实new-neutral已等token长**，完全不包含任何T2，也没有包括唯一两条真正不等长的旧accept→new reject。于是G1口头计划的“17 unmatched-N1 +14 matched-N1B对照”在实证分层上错误，无法按预注册宣称已为两个最重要的V/Q交互样本配好因果中性对照。

在执行任何后续GPU调用前，执行方必须纠正真实`new-vs-neutral`配平统计、保留基线/两臂请求及Gold完整SHA、发布新版forward manifest与pilot分层和资源合同勘误；涉及对照分配与批准范围变化，应由相应授权流程重新确认，不得事后依据模型结果改组。如果G1已在其他会话实际启动/完成，必须保存原始结果并以**探索性、未满足原拟匹配计划**来解释，不能对已看到的模型输出事后重写G1假设。

本次新分析已作为GitHub Issue [#2](https://github.com/dddd2024/jev/issues/2)评论`6393713309`、`6393745090`、`6393752142`通知并行执行方；我们不覆写其源脚本、不接管正在执行的物理任务。

**阶段判断**：A461-PSMI/A463-VQPI仍为同一P1方向；**实际CPU G0双路径PASS**，但“全部N1未配平”的报告已被本轮推翻。真正阻塞具有机制识别价值的G1，是两个最关键accept→reject格子的中性等长证据、旧baseline归档与物理计划正确性；SecJev真实模型单调性违例和Q/K/LoRA因果贡献仍未由本轮证明。

**本轮实际资源账本**：只读GitHub真实G0存档、脚本与收据；新SecJev模型forward0、GPU0、训练0、新原始SecJev语料扫描0，服务器和GPT Library双备份未验证。数据分析及本Markdown、JSON、回读收据均另增`research/analysis/`独立路径。
