# A461-G5 最小双向 patching pilot：执行后独立原始 logits 审计 V1

**审查时间：2026-10-25**。**结论：VALID_EXECUTION / EXPLORATORY_CAUSAL_SIGNAL / NOT_FULL_RESTORATION / NOT_YET_PAPER_MECHANISM**。

本审计基于 GitHub 已归档的原始文件，通过**独立于研究方 `A461_g5_pilot_analysis_v1.py` 的重新解析与数学计算**核对。没有重新运行 GPU，未直连服务器原始文件目录；“独立”是指 **GitHub 副本、预注册执行图及旧归档 logits 的独立回读和数值复算**，不等同于第二台机器/第二批 source group 复现。

## 1. 冻结证据

| 文件 | Git blob |
|---|---|
| `research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/PATCHING_PILOT_REAL_R2/execution_receipt.json` | `2ab28abd8d2fe47feeb15c335f47fc6e0140e382` |
| `.../PATCHING_PILOT_REAL_R2/raw_native_logits_pilot.jsonl` | `790a71a55b99ea3a362158f2a389f05a49626f92` |
| `.../PILOT_ANALYSIS/analysis_results.json` | `bae4cc1668dd83a58c320c9b99a1b9391fb21b93` |
| `.../G0_PILOT_CPU_GATE_REAL/pilot_execution_plan.jsonl` | `53768d8762568ef37fb6458eeadbc118a329759a` |
| `research/rounds/A461_G5_DONOR_RESOLUTION_AND_PATCHING/G1S_V2_REAL/raw_native_logits_112_requests.jsonl` | `13400252b360863a80baea66b39b9a7dbe0ca633` |
| GPU runner (frozen) | `d05b070e0723de5af70c6afbfd312ac99fdbdbb3` |

运行回执 `COMPLETE_A461_G5_PILOT_GPU`：一个模型加载，28/28 次真实原生 forward，28 行原始 logits，0 backprop、0 网络调用；成功轮时长 8.465 秒。上轮 `PATCHING_PILOT_ATTEMPT1_STOPPED` 物理消耗另 1 次，**研究线累计 29 次**。批准/评审分别在 `admission_receipt_pilot_gpu.json` 和本轮回执中绑定同一 runner blob。所有服务端路径限于 `~/wjc`。

## 2. 独立数值复核

采用 `M=logit(conflicting_vote:true)-logit(conflicting_vote:false)`，不是四问题 action 头的 margin。每条主记录独立解析并检查 finite logits、4 个问题、动态 C row index 1、forward_index 1–28 连续、执行 `condition/target/layer/patch-span/capture-span` 与冻结 `pilot_execution_plan.jsonl` **28/28 一致**；3 个新鲜无 patch baseline 根据 token SHA 联结到 V2 存档的 **对应各问题 keys 与所有 logits 完全相等（逐位数值一致）**；identity self patch 第 8、9 次与各宿主 SA 基线在**所有问题头 logits 完全一致**。需注意 V2 存档对象附带 `probs` 而新原始结果没有此字段，对齐时正确地只比较 `keys+logits`，不应把对象 JSON 整体不相等误判成 logits 不一致。

### 2.1 方向 A：恢复（donor NEW → host SA），所有四格报告

| Host / layer | Host SA M0 | Restoration M | ΔM_rest | ΔM_SA-sham | ΔM_permuted | Δrest − Δsham | Δrest − Δperm | 判断翻转 | 预注册支持 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| run114 / 11 | −9.577639 | −7.776229 | **+1.801410** | +1.440941 | +0.982751 | **+0.360469** | **+0.818660** | 否，仍 false | **是** |
| run114 / 23 | −9.577639 | −9.577639 | 0 | 0 | 0 | 0 | 0 | 否 | 否 |
| run182 / 11 | −9.390018 | −7.451414 | **+1.938604** | +1.044948 | +0.982465 | **+0.893656** | **+0.956139** | 否，仍 false | **是** |
| run182 / 23 | −9.390018 | −9.390018 | 0 | 0 | 0 | 0 | 0 | 否 | 否 |

**解释**：预注册门 `Δrest>0` 且严格超过两个负对照在第 11 层的 **2/2 宿主成立**，总 4 层×宿主格子中 **2/4 supportive**；但 **0/4 恢复判断翻转**。SA-sham 和 permuted 均产生非零正向 margin 改变，说明不能把 +1.8/+1.9 全部归因为“冲突证据特异信息”；第 11 层的对照净优势仅为 0.36/0.82（run114）及 0.89/0.96（run182）。不允许写“恢复了错误分类”。

### 2.2 方向 B：抑制（host treatment → donor NEW）

donor NEW 基线 `M=+1.446688`（C=true）。

| Host donor source / layer | ΔM | Donor new M after | 是否翻转 |
|---|---:|---:|---|
| run114 / 11 | **−4.640155** | **−3.193467** | **是，true→false** |
| run114 / 23 | 0 | +1.446688 | 否 |
| run182 / 11 | **−2.751554** | **−1.304866** | **是，true→false** |
| run182 / 23 | 0 | +1.446688 | 否 |

**解释**：第 11 层的两个宿主来源分别实现真正的 donor 正确读出抑制，属于方向特异的因果可操控证据。但本轮**没有 donor-side matched SA-sham、position permutation 和范数匹配随机补丁**，不能由这 2 个 flip 直接判定为“未识别冲突证据”的语义特异机制；也不能据此推出原始模型在安全动作头产生未经授权的真实行为。

### 2.3 其他观察

- 第 23 层全部相关 patch 恰好零改动：由于该层输出的**较早 state-token**补丁不再通过后续层传播到 decision readout token，属于当前干预几何可能预期的结构 null；**不能把它当作“第 23 层不含安全证据”的定位结论**。
- 每个 patch 的 action/quorum/evidence 独立 question-row logits 与对应未干预输入的 baseline 完全相等：这是混合 backbone 四 question 独立 causal row 架构的自然对照，不是“安全动作效用被保护”的证据。
- 本实验在 backbone layer-output span 上操作，而非单独 patch Pointer Head `K` 侧；故尽管 G4 读出代数分解提示 key-side 贡献，**G5 不能证明作用专属于 key 侧**，也没有隔离 LoRA/attention/MLP/DeltaNet 的内部路径。

## 3. 证据等级与论文限制

**已经建立的内容**：
1. 第一次 **模型真实内部 post-layer activation patching** 全阶段回执和原始 logits 完整可核；
2. frozen C row 的 `layer 11` causal perturbation 可以跨来源改变冲突识别 margin，且恢复方向超过现有 two controls；
3. 从两类失败宿主注入的 states 可以在 `layer 11` 使同一个正确供体的冲突识别读出 `true→false`；
4. 运行身份、token 原始定位、物理前向及 identity/baseline 通过，较此前只有 G3 行为现象与 G4 Q/K 代数读出的证据等级明显提高。

**没有建立的内容**：
- 双向 **正确分类恢复**（恢复方向没有任何 false→true flip）；
- 语义专属性/安全政策边界漏洞：suppression 缺 matched negative controls；cross-context activation transplantation 仍可能包含幅度、token位置、层间分布差异；
- Key-only mediator 因果证明、model-independent 适用性或新来源 group 确认；
- 统计显著性/论文独立创新：样本仅 **1 个 donor + 2 个 DEV host**，**不可用4个层×宿主格子充当4个独立样本**。

论文现阶段措辞建议：`Exploratory bidirectional intervention shows layer-11 sensitivity of conflict-recognition margins; donor-side suppression flips occur in 2/2 target sources, whereas restoration improves margins without reversing the erroneous classification; causal specificity and independent replication remain unresolved.`

## 4. 下一轮设计决定（先 CPU G−1，不擅自启动 GPU）

**拟实验名称：`A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION`。** 此处属于**实验设计草案**，状态 `CPU_G_MINUS_1_DESIGN_NOT_EXECUTED`；不构成批准新 GPU。

**第一阶段 CPU 准入（可与论文证据评估并行）**：
- 读取 A471–A474/G4/G5 的原始实验数据与竞争论文卡，锁定本实验相对 activation patching best practices、generic donor swap、pointer mediation 的确切 novelty delta；**不得称原有控制/patching 技术为创新**。
- 按场景/source group 定义独立单元，列出未使用原始组的可用性、构造性 Gold 双 oracle、合法 author/timestamp/validator_set、相同 token 宽度的源/宿主配对；防止将相同 run 的 edits 当成独立数据。若无新的独立 source-group 合格正供体，则先开发严格的 CPU 样本筛选协议，**不扩大 GPU**。
- 基于 G1 `layer11` 结果预先定义 confirmatory 与 exploratory 子集（不得把 run83/run114/run182 上的同层重复观测报告成独立复现）；层 23 若保留仅作为结构空白对照。
- **必要性方向强制增补负对照**：host new→donor new、host SA→donor new、host new span permutation→donor new、同范数/同位置的随机激活（建议至少每对每层有同位配对）。也需要 restoration 方向的逐对范数、幅度/激活分布量化与可替代 cheap heuristic。
- 后续真正的 Key-specific attribution 必须有 **K/Q 或同等独立可干预读取路径** 的 component-controlled protocol，对 LoRA/backbone 表征与头读出分离做竞争解释；不能只用层 11 的整体 state patch 重述 G4 的键侧代数分解。
- 资源：CPU 日志/解析/配对/模拟为 0 native forwards；GPU 预算按新增样本×层数×两个方向×四控制条件、必需 baseline/capture/identity 明确动态推导，再独立审查并获用户新授权。停止条件：无新独立来源合格正供体；双 oracle 不一致；样本 token 对齐不能保证；随机/SA sham 同样能解释 flip；Key-specific 效应不能超 cheap baseline。任何触发时 downgrade/HOLD。

**优先级：P0 本轮后验独立审计归档与论文主张边界；P1 G2 CPU source-group 可行性审计；P2 通过后新来源的因果控制试验；P3 其他 A47x 论文筛选。不要在 P0/P1 未结案前开新的 GPU 路线。**

## 5. 归档与审计性质

本报告只新增分析文档，不改写源原始数据、已批准 runner、回据或原协议。若仓库另一个执行代理继续推进，应保持仓库提交 append-only、在 Issue #2 发布独立复审请求、冻结新的具体资源预算。