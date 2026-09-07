---
name: prose-lint
description: 数学建模论文 Markdown 章节的文风/结构量化检查与事实账本工具：prose_lint.py（括号/引号/破折号/缩写密度、名词串、碎节、处理链缺环、公式与图表周边）、facts_extract.py（数字/公式/引用账本）、fact_diff.py（改写前后零漂移比对）。阈值来自 14 篇国一论文语料。polish 各阶段前后都要跑。
---

# prose-lint

三个脚本，纯标准库，Python 3.10+，只读输入。

## prose_lint.py

```bash
python .agents/skills/prose-lint/scripts/prose_lint.py <sections 目录|单个 md> \
    --out polish/PROSE_LINT.md --json polish/prose_lint.json [--strict]
```

| 级别 | 规则 | 含义 |
| --- | --- | --- |
| FAIL | `paren_full_per_k` `quote_per_k` `dash_per_k` `en_abbr_per_k` | 密度超过语料 **max**（超过 P75 为 WARN） |
| FAIL | `dash_chain` | `A—B—C` 三段以上名词串（语料 0） |
| FAIL | `quote_mismatch` | `“…“` 引号闭合错误（多为构建 bug） |
| FAIL/WARN | `problem_skeleton` | 问题章节子标题里找不到 分析/建立/求解/验证/小结；缺验证或小结为 FAIL |
| WARN | `problem_chapter_thin` | 问题章节汉字 < 语料 P25（≈3.3k） |
| WARN | `thin_section` | 三级节正文 < 300 字 |
| WARN | `heading_run` | 标题后直接子标题 |
| WARN | `paren_in_title` | 标题带括号补充 |
| WARN | `too_many_h2` / `h4_exists` | 二级标题 > 语料 P75；存在四级标题 |
| WARN | `compressed_sentence` | 一句里 ≥2 个引号术语、≥2 个破折号或 ≥4 个不同缩写 |
| WARN | `paren_dense` | 一段 ≥3 对括号 |
| WARN | `formula_followup` | 编号公式后 3 行内没有"其中/式中/表示" |
| WARN | `figure_lead` | 图/表前 4 行内没有引导句（符号说明表除外） |
| INFO | `paren_sentence` `ai_phrase` `long_sentence` `short_paragraphs` `connective_low` | 提示性 |

`--strict` 时有 FAIL 返回码 1。阈值文件默认 `_references/corpus_stats.json`，可用 `--thresholds` 换。

## facts_extract.py / fact_diff.py

```bash
python .agents/skills/prose-lint/scripts/facts_extract.py <proj>/paper/sections --out <proj>/polish/FACTS.json
python .agents/skills/prose-lint/scripts/fact_diff.py <proj>/paper/sections <proj>/polish/sections --out <proj>/polish/FACT_DIFF.md --strict
```

`fact_diff` 判定：数字（值+单位）丢失/新增、展示公式与行内公式任何变化、引用或图片丢失 → FAIL；新增无单位 ≤20 的整数、新增引用 → WARN；标题变化 → INFO。全文多重集比对，允许章节合并与段落移动。

## 解读要点

- 连接词密度低是"论证没展开"的信号，不是要堆连接词。
- 语料只有 14 篇，P75 阈值是初版；WARN 允许人工判断保留，FAIL 必须处理。
- 灵敏度/稳健性单独成章时，其 `problem_skeleton` 只检查小结。
