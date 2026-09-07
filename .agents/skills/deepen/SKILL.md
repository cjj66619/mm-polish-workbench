---
name: deepen
description: polish 第 3 阶段。按 STRUCTURE_PLAN 中的 expand / merge / add_bridge 动作，在 polish/sections/*.md 上补写"问题分析、模型动机、参数理由、结果解释、回到题意、向下一问交接"等缺环，只能使用 reports/、results/、figures README、代码 docstring、原稿中已有的事实。每处改动记入 REWRITE_LOG.md，改完跑 fact_diff。
---

# deepen

## 输入

`polish/STRUCTURE_PLAN.md`、`polish/sections/*.md`（工作副本）、证据源（`reports/*.md`、`results/*.json|csv`、`figures/*/README.md`、`code/*.py` 顶部 docstring）、`_references/problem_chain_template.md`、`_references/writing_style_card.md`。

## 逐动作做法

| 动作 | 做法 |
| --- | --- |
| `expand` | 先把证据原文（报告小节、README 段）摘到工作区，再据此写段落。段落结构：为什么 → 怎么做 → 得到什么 → 意味着什么。数字必须与证据一字不差，且原稿已有的数字不得改写形式（0.50 不写成 0.5）。 |
| `merge` | 把平行小节标题去掉，各节首句改成段落主题句，补一句说明它们之间的关系（互补/递进/并列）。合并后一节 ≥ 300 字。 |
| `add_bridge` | 问题 N 末尾加"本问输出 X，作为问题 N+1 的输入；局限 Y 将在 N+1 中处理"；问题 N+1 开头承接。内容来自 `02_analysis.md` 与 `plan.md` 的决策记录。 |
| `reorder` | 只移动段落，不改句子；移动后检查图表引用顺序仍然合理。 |
| `back_to_draft` | 不写正文。只在 `POLISH_REPORT.md`"回 draft 清单"列出。 |

## 扩写时的证据规则

- 每个 expand 段落末尾在 `REWRITE_LOG.md` 里记"依据：reports/RESULTS_REPORT.md §2.3"；正文里不出现文件名。
- 结果解释只能说数据已经显示的事，不加"显著""明显优于"等原稿和报告没有的判断词；比较必须有两边的数字。
- 报告里有而原稿没有的数字可以写进正文（fact_diff 会报 `numbers_added` FAIL），此时在 LOG 里标 `evidence:<文件>`，verify 阶段人工放行；宁可少写不写没依据的数。

## 完成标准

- STRUCTURE_PLAN 里每条 expand/merge/add_bridge 都有对应 LOG 条目。
- `python .agents/skills/prose-lint/scripts/fact_diff.py <proj>/paper/sections <proj>/polish/sections` 的 FAIL 只剩带 `evidence:` 标记的新增数字。
- 各问字数进入 PLAN 给的区间；没证据的环节仍为空，不硬填。
