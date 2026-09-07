---
name: structure-audit
description: polish 第 2 阶段。读 PROSE_LINT 与原稿章节，对每个"问题 N"章节按 12 环节处理链逐项核对，并检查碎节/标题连排/问题间交接，输出 polish/STRUCTURE_PLAN.md（每问一张表：环节、现状、动作 merge/expand/reorder/add_bridge/back_to_draft、证据、目标字数）。只出计划，不改正文。
---

# structure-audit

## 输入

- `<proj>/polish/PROSE_LINT.md`（`problem_skeleton`、`problem_chapter_thin`、`thin_section`、`heading_run`、`too_many_h2` 条目）
- `<proj>/paper/sections/*.md`
- `<proj>/reports/*.md`、`<proj>/results/README.md`、`<proj>/figures/*/README.md`（用于判断"证据在不在"）
- `_references/problem_chain_template.md`

## 步骤

1. **识别问题章节**：一级标题匹配 `问题\s*[一二三…0-9]+` 且非"重述/分析"的章节；灵敏度/稳健性/评价章单独记。不要假设问题数量或题型。
2. **逐问填处理链表**：对模板 12 个环节，读章节正文，标记 现状 = `有/弱/无`。"弱"指只有一两句、只列了名词、或只有表格没有解释。
3. **找证据**：对 `弱/无` 的环节，在 reports/results/figures README 里找可以支撑扩写的已有事实，记录文件与小节。找不到 → 动作 `back_to_draft`，不允许后续阶段编造。
4. **合并碎节**：`thin_section` 连续出现的平行三级节（例如"特征组 A/B/C 各 60 字"）→ `merge` 成一节，给出合并后的标题与段落顺序。
5. **交接段**：每问结尾是否说明输出给下一问什么；下一问开头是否承接。缺 → `add_bridge`，写明桥接的两端。
6. **重排**：若章节顺序违反"分析 → 建立 → 求解 → 验证 → 小结"，给出 `reorder` 建议。
7. **目标字数**：以语料 P25 3.3k / P50 5.4k 为参考给区间，但每个 `expand` 必须对应具体证据；无证据不给字数。

## 输出 `polish/STRUCTURE_PLAN.md`

```markdown
# STRUCTURE_PLAN

## 全局
- 二级标题 36 → 目标 ≤ 24：合并清单 …
- 问题间交接：问题一→二 缺；问题二→三 有；…

## 问题一（现 2143 字 → 目标 3500–4500）
| 环节 | 现状 | 动作 | 证据 | 目标字数 |
| ... |

## 回 draft 清单
- 问题二缺基线比较：results/ 中无 RF 基线结果 → 需 draft 补 code/2x_baseline.py
```

## 禁止

- 改任何正文文件。
- 为凑字数给没有证据的环节安排 `expand`。
- 建议改公式、改数字、加实验（只能进"回 draft 清单"）。
