# A461 V8 M23 独立原始数据计数复核

状态：PASS（限于 CPU 统计复核，不是独立模型重复实验）。直接从每个模型 248 行原始 JSONL 的三个动作 logits 重新取 argmax，不调用作者分析脚本。

| 指标 | kev-4B | SecJev-0.8B |
|---|---:|---:|
| 新冲突被拒绝 | 40/124 | 14/124 |
| 合法 twin 错误拒绝 | 45/124 | 15/124 |
| 错误拒绝涉及来源组 | 14/17 | 9/17 |
| 在 new 已被拒绝时仍误拒 twin | 37/40 | 14/14 |

两模型覆盖相同的 124 个场景；twin Gold 为 accept 102、wait 22。全部三动作 Gold × prediction 混淆计数与 V8 numbers_mech_v5.json 一致；M margin 复算零差异。

本项不证明独立实验重复、自然内部机制或跨任务泛化。不启动新 GPU，不修改冻结数据。完整哈希和混淆矩阵见 INDEPENDENT_M23_RECOUNT.json。
