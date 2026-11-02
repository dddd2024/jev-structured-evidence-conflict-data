# A461-G5 V4 增量执行审计：CPU mock 失败、输入合同及账本门槛

**日期**：2026-10-25。**状态**：`REJECT_V4_GPU_NOT_ADMITTED`（本报告仅核验已有代码/归档数据，不执行真实模型或 GPU）。**审查目标**：`A461_g5_patching_runner_v4.py` blob `4b812062d4d5ad3b33ac17526424ce20e1f43eb8`、`A461_g5_mock_patch_test_v1.py`、A471/A472 新审计与冻结 G5 V2 数据；最新审查前 main `4f22ce588cc4`。

## 一、实际新增进展

- A461-G5 最小 2-host / 2-layer 双向因果 patch CPU 准入草案与执行制度已归档，**计划** donor `run83`、等宽且 C 错误宿主 `run114(wait)` 和 `run182(accept)`；28 前向仅为草案估算，**未经准入，不允许据此启动 GPU**。
- V4 迭代新增对原始 JSON 长度对象解析的修订（`cb3286c6`）、旧臂 row ID 更正（`d73ff0ff`）、随后 `953dc5d` 改动宽度索引；这些是部分工程修正，并非模型因果结果。
- A472 已归档 20 篇文献分级复筛及新备选 `A472-SGTI`（共享 LoRA 任务梯度干扰）；状态 `P2/HOLD`、CPU G−1 **仅设计未执行**，没有新增 GPU 调用、独立创新或已证漏洞。主线仍为 A461-G5。
- 截至该 checkpoint，G5 仓库目录中没有可独立回读的 `PATCHING_*_REAL` 成功产物；Issue #2 未出现新的 V4 独立 PASS。

## 二、增量独立核查发现

### P0-A：已提交的 CPU mock 本身 FAIL，不能作为准入 PASS

`research/rounds/A461_G5_DONOR_RESOLUTION_AND_PATCHING/A461_g5_mock_patch_test_v1.py` 的 `run` 对 six `FakeLayer` 连续使用 `x+1`；在 `layer_idx=2` **之前**真正的当前层输入为 `x0+2`。但身份控制设置 `own=x0[C_ROW,START:START+W,:]`，不是该层相应的原始激活。将 `x0` 写回会使该位置最终输出比基线少 `2*D=16`，因此 `own_state_patch_is_identity=False` 且总 `verdict=FAIL`。在本次隔离的 CPU PyTorch 2.10.0 环境中按 GitHub mock 逻辑独立复现：

```json
{
  "others_unchanged": true,
  "c_changed": true,
  "span_changed": true,
  "outside_span_unchanged": true,
  "identity_ok": false,
  "verdict": "FAIL",
  "identity_max_abs_diff": 16.000003814697266
}
```

此结果不等于 G5 真模型已经失败，它只证明 **“mock 已通过”声明不能凭当前代码成立**。正确测试需捕获实际**对应层/对应 C 行**的激活，再对同一层真实宿主执行 identity patch；修后实跑 mock 并归档成功回执、源 SHA。

### P0-B：真实 V4 runner 的供体/identity 激活依然从错误问题行取

尽管 V4 的 `forward_patched(enc,L,(C_ROW,...))` 在每个 host 上以 `C_ROW = meta.id=="conflicting_vote"` 定位 **C 行**（约 297/322/334 行），实际从层 hook 的 `cap[("new",L)][0,...]`、`cap[("sa",L)][0,...]`（约 275–276 行）仍取 **batch row 0 action**，identity `cap2[11][0,...]`（约 321 行）也是 action 行。冻结 G5 四问题顺序为 `certificate_action=0`、`conflicting_vote=1`、`evidence_level=2`、`quorum=3`；SecJev/Qwen hybrid 的四行在同一 forward 内**彼此独立**。因此 V4 的 patch 操作目标虽然改成 C 行，注入的却是 action 行的激活，破坏了同问题行的机制对照定义；identity 不可能被此 capture 逻辑可靠签收。必须把 donor C 和 host C 的同一层状态都从 `row=1` 捕获，并以动态 meta 映射验证，而不是硬编码行序。同步核验 off-target 头没有被直接 patch。

### P0-C：V4 其余静态阻断未解，尤其预算无法按当前源成立

独立 A471/A472 已确认并可从当前 V4 blob 复读：
- `render()`（约 124）使用未定义的 `q_tw`；donor 与 host 旧状态恢复（约 239、285）使用未定义的 `state_by`；这两者会在启动 GPU 后导致 NameError。
- `host_final` 宽度循环（约 219–222）使用上一个 `for k in by_pair` 遗留的 `k`：`old_rid=k+":old"`，不是 `h["pair_key"]+":old"`；A472 已单独报告。
- 运行时没有冻结 `host_final[:2]` 等最小试点名单/样本上限。A471 按 G5 原始日志计算出 **32** 个候选（11 个 +34，21 个 +33），远多于宣称的 10 个，当前动态 97 上限没有在调用前被执行图核算；禁止继续执行到终态才发现超额。
- `spans[tag]["suffix_intact"]` 的当前布尔表达式 `Ls_t-(z+w)==Ls_o-(z+w)` 等价于 `Ls_t==Ls_o`，对追加事件永远为 false，而且没有独立 token 后缀比较或 `ck(suffix_intact)`，不构成真正的 token-span 合法性门。
- 已有 `rows` 在每组 forward 后 flush 到文件是进步，但 `produced` 在最后仅包含 `execution_receipt.json`，`SHA256SUMS` 没有为 `patching_rows.jsonl` 写 hash；必须同时在失败和完成回据中记录真实物理 forward 数，并校验原始数据清单。

A471 列出的 `G0D_CONS/G1S_V2` 运行路径与 GitHub 存档的 `G0D_CONS_V2/G1S_V2_REAL` 路径不同；在未验证实际服务器目录映射之前不能断言服务器读取一定失败，但应在 CPU dry-run 中明确冻结路径/源 SHA。

## 三、最短验收路径（不再重复泛化评审）

1. **把 V4 当前错误收敛为一个 CPU 合同修复**：在纯 CPU 中真实打开 frozen G5 V2 输入，修正 `q_tw/state_by`、old IDs、长度 schema、`h["pair_key"]`、按 actual G1S logits 选择 **两个** strict C=false host（候选 run114/run182）、和确切 +34 tokenizer span。
2. **修正且实跑同问题行的模型无关 mock**：使用分层 capture 的真实中间激活验证 identity、C-only perturbation、off-row noninterference、hook 层键唯一性和源—宿主 exact span 对齐；失败就继续修 CPU，不动 GPU。
3. **计算、冻结最小试点调用图**：预注册两个层、两方向、identity、SA sham 与 random；基于实际 forward trace 自动核算（原 28 次只是候选预算，必须核对它是否覆盖所有 capture/baseline）。
4. **一次 independent PASS 绑定 commit/blob 和日志**之后才启动真正 GPU，第一步小试验，不先扩 10×6。完整实验和新 P2 方向不能与这个关键路径争抢 GPU。
5. **创新约束**：若小试验产生恢复/抑制，应判为 single-donor DEV 探索性因果信号；需语义对照特异性、独立来源和文献竞争比较才能写“机制贡献”，不能仅以 Key-side 会计或某次 patch 翻转发表核心结论。

**总裁决：已有真实行为阳性/G4 代数读出/G5 供体，仍无有效双向 patching；现在需要的是一次真实 CPU 全链路 PASS，而不是另一轮写协议或漫无目标的新方向。**
