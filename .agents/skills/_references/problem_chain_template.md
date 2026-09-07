# 问题处理链模板（structure-audit 的检查表）

获奖论文的共同特征是每一问都有一条完整的处理链，而不是"方法 + 结果表"。本模板与题型无关：优化、评价、预测、分类、机理建模都适用，只是有些环节可以合并成一段。

## 1. 每一问的十二个环节

| # | 环节 | 至少要回答 | 证据来源（draft 项目内） | 缺失时 |
| --- | --- | --- | --- | --- |
| 1 | 题意拆解 | 这一问到底要输出什么、约束是什么、和上一问的关系 | `paper/sections/0x_restatement.md`、`02_analysis.md` | polish 可补（从题面） |
| 2 | 数据 / 机理观察 | 数据长什么样、有什么规律或问题、这决定了什么建模选择 | `reports/DATA_REPORT.md`、`results/data_quality*` | polish 可补（从报告） |
| 3 | 预处理 | 做了什么、为什么必须做、对后续有什么影响 | `reports/DATA_REPORT.md`、`code/00_*` docstring | polish 可补 |
| 4 | 模型建立 | 为什么选这个模型（对比了什么备选）、假设是什么、公式与符号 | `reports/ANALYSIS_MODELING_REPORT.md` | polish 可补动机；公式不改 |
| 5 | 参数与算法设置 | 关键参数取值及理由、算法流程、随机种子 | 代码 docstring、`RESULTS_REPORT.md` | polish 可补 |
| 6 | 求解过程 | 怎么算的、收敛/运行情况 | `RESULTS_REPORT.md`、`RUN_STATUS.md` | polish 可补 |
| 7 | 中间结果 | 不只给最终表，展示关键中间量（拟合曲线、特征分布、迭代曲线） | `figures/*/README.md` | 缺图 → 回 draft |
| 8 | 基线 / 备选比较 | 与至少一个更简单的方法比，好在哪 | `ROBUSTNESS_REPORT.md`、`results/` | 缺数据 → 回 draft |
| 9 | 检验 / 误差 / 灵敏度 | 结果稳不稳、误差多大、哪个参数最敏感 | `ROBUSTNESS_REPORT.md`、`results/*sens*` | 缺数据 → 回 draft |
| 10 | 结果解释 | 数字说明了什么现象、符合机理吗、意外之处 | 图表 README"人工审图"段、`RESULTS_REPORT.md` | polish 可补（不能新增结论） |
| 11 | 回到题意的结论 | 用题目的话回答这一问 | 原稿小结 | polish 可补 |
| 12 | 向下一问交接 | 本问输出什么给下一问、有什么局限被带过去 | `02_analysis.md`、`plan.md` | polish 可补 |

## 2. 环节到章节的映射（建议，不强制）

```text
N.1 问题分析          ← 1, 2, 12(上一问的输入)
N.2 数据准备 / 机理    ← 2, 3            （可并入 N.1 或 N.3）
N.3 模型建立          ← 4, 5
N.4 模型求解          ← 6, 7
N.5 结果分析与验证     ← 8, 9, 10
N.6 问题小结          ← 11, 12
```

灵敏度 / 稳健性单独成章的论文，问题章节里的 9 可以只留一句并指向该章。

## 3. 审计输出格式（`polish/STRUCTURE_PLAN.md`）

对每一问给一张表：

```markdown
### 问题二

| 环节 | 现状 | 动作 | 证据 | 目标字数 |
| --- | --- | --- | --- | --- |
| 1 题意拆解 | 6.1 有 2 句 | expand | 02_analysis.md §问题二 | 200–300 |
| 4 模型建立 | 6.2–6.4 拆成三节共 700 字 | merge + expand | ANALYSIS_MODELING_REPORT §3 | 900–1200 |
| 8 基线比较 | 无 | back_to_draft | 需要 RF 基线在 results/ 中 | — |
| 11 回到题意 | 无 | add | 原稿 6.5 表 + RESULTS_REPORT §2 | 150–250 |
```

动作只有五种：`merge`（合并小节）、`expand`（用已有证据扩写）、`reorder`（调整顺序）、`add_bridge`（加过渡/交接段）、`back_to_draft`（缺证据，不在 polish 阶段编造）。

## 4. 字数参考

语料 32 个"问题 N"章节：P25 3.3k、P50 5.4k、P75 9.3k 汉字。低于 P25 时先检查表 1 哪些环节为空，再决定扩写；不要在已有环节里加形容词凑字数。
