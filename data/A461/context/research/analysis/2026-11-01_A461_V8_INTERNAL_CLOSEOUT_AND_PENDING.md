# A461 V8 研究收尾与内部复核记录（2026-11-01）

**状态：INTERNAL_CPU_RECOUNT_PASS / FULL_PAPER_AUDIT_PENDING。** 老师反馈尚未到达。本记录不改变既有论文级裁决，不构成投稿批准或对外发布许可。

## 1. 冻结依据与操作边界

- 截至本次复核，私有仓库 `dddd2024/jev` 已检查基线：`937fdd4c5e22f231f3d4acf05eb41b80c784c7cb`（随后本次收尾的独立复核脚本、报告与 JSON 另有新增提交）。
- 论文包：`research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/PAPER_CLAIM_PACKAGE_V8/`，稿件 v14（DOCX/PDF）；仓库 README 明确状态 `UNVERIFIED_PAPER_READY_CLAIM`，即**未经过该版本的最终论文审计**。
- 服务器：Linux `dell-PowerEdge-R740`，所有新校验文件均写在 `~/wjc/a461_closeout_20261101/`；访问入口为已授权 Windows `dd` 设备。服务器既有 `~/wjc/jev-checkout` 工作树未重置/切换；仅更新了 `origin/main` 远端引用。
- 未启动新的模型前向、GPU 实验、重训或破坏性清理。原始实验和冻结文件未修改。

## 2. 本轮新完成的独立 CPU 核对

**原始文件完整性。** M23K 和 M23S 的 `GPU_RUNS/ATTEMPT_R1/SHA256SUMS` 各有 253 条，`sha256sum -c --status SHA256SUMS` 两者均退出 0（各 **253/253 PASS**）。从 GitHub 获取的 V8 `numbers_mech_v5.json` SHA-256 为
`e4ec02a2d9438272a92047b900ec90bd6721bedff7e051f8d7b2686d81aa0453`，与 V8 已提交的 `SHA256SUMS` 对应项一致。

**独立原生 logits 计数。** 不调用原 M23 分析脚本，而是逐行读取 248+248 条真实 JSONL，用三动作 `certificate_action` logits 的 argmax 重算结果，逐场景核对 Gold、new/TWIN 配对、17 个来源组及 `conflicting_vote` margin；与 V8 `numbers_mech_v5.json` 的全部 TWIN Gold × prediction 矩阵一致。

| 项目 | kev-4B | SecJev-0.8B |
|---|---:|---:|
| 新冲突预测 accept / reject_conflict / wait | 83 / 40 / 1 | 69 / 14 / 41 |
| 合法 TWIN 预测 accept / reject_conflict / wait | 72 / 45 / 7 | 56 / 15 / 53 |
| 新冲突被拒绝 | 40/124 | 14/124 |
| 合法 TWIN 错误拒绝 | 45/124 | 15/124 |
| 发生 TWIN 错拒的来源组 | 14/17 | 9/17 |
| 在 new 已拒绝的场景中，TWIN 仍遭拒绝 | 37/40 | 14/14 |

两个模型都是同一批 124 个场景；每模型合法 TWIN 的规则 Gold 为 `accept=102`、`wait=22`。两份 JSONL 的 SHA-256 分别为：
- kev-4B：`57c7a84d0ed8cce5ae010af65b2974061ebf21718ba5fe78e60703c6165f9b93`
- SecJev-0.8B：`5110c8f42b1360c5f37b58736348e642fe810ebe0eff9968a08afff2a1794285`

复核结果及脚本：
- `research/analysis/2026-11-01_A461_V8_M23_NATIVE_INDEPENDENT_RECOUNT.json`
- `research/analysis/2026-11-01_A461_V8_M23_NATIVE_INDEPENDENT_RECOUNT.md`
- `research/analysis/scripts/A461_v8_m23_native_independent_recount_20261101.py`
- 服务器原始记录位于 `~/wjc/a461_closeout_20261101/`。

**证据级别：** 上述只是本轮独立的 CPU 原始输出**计数核对**；不是独立模型重跑、独立实现的机制因果复现，亦不是外部真实安全系统验证。此前 22/22 阶段复算来自冻结的作者分析脚本，不应冒充独立机制复验。

## 3. 论文结论边界与未完成事项

- 已支持：在一个结构化追加投票/冲突规则任务中，对合法性改变的配对证据，两个 typed scorer 的动作决策存在明显不稳健性；Kev-4B 的 L11 局部状态干预表明有条件因果可控性；已观察到三动作误拒与漏拒的双侧风险。
- 不支持：对自然推理链条的完整机制辨认、通用 AI 系统安全漏洞、实际部署系统影响、可靠防御方案、跨任务/跨架构普适性。
- V8 既有状态继续为 `NOVELTY_NOT_YET_PASS`、`MECHANISM_NOT_IDENTIFIED`，G2.4 为 `NO-GO → PIVOT_TO_PAPER`。本轮 PASS **不能**提升这些裁决。
- **待办 P0：** 老师反馈整合；V8 稿件完整、独立的论文级审计（尚未授权触发）；与真实提交前的匿名化及格式校验分开进行。
- **待办 P1：** V8 文档全包 SHA 文件级核对尚未完成。本轮服务器稀疏 Git 对象按需提取发生远端对象获取卡住，已停止该提取。不能将 GitHub 已提交的哈希清单等同于逐文件复核。
- **TMLR 提前检查：** 官方要求以 TMLR LaTeX 模板生成 PDF、双盲匿名；补充材料不超过 100 MB、使用 PDF/ZIP 且需匿名。当前 V8 是 Word 输出，README 也标注仓库链接尚待匿名。现阶段只整理清单，不提交、上传或公开任何稿件/模型权重/证据资产。官方要求：https://www.jmlr.org/tmlr/author-guide.html 和 https://www.jmlr.org/tmlr/submissions.html。

## 4. 交接和停止规则

老师回复前，不再为了实验编号增加 M 系列 GPU 阶段，不继续 G2.4 已判定 NO-GO 的机制辨认分支，不修改规则 Gold 或冻结数据。下一次工作以老师具体意见、V8 完整证据校验和最终论文审计的明确授权为起点；保持旧审计和负结果可追溯。