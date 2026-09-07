---
name: rewrite-style
description: polish 第 4 阶段。按 _references/writing_style_card.md 对 polish/sections/*.md 逐段改文风：括号补充改独立句、引号术语只定义一次、破折号名词串拆成因果句、缩写首次给中文全称、公式后补符号解释、图表前后补引导与解读、每问结尾回到题意。公式、数字、编号、引用锁定不改。每段改完记 REWRITE_LOG.md，全部改完跑 fact_diff 与 prose_lint。
---

# rewrite-style

## 输入

`polish/sections/*.md`（deepen 之后的版本）、`polish/PROSE_LINT.md`（按 `file:line` 定位）、`_references/writing_style_card.md`、`_references/anti_ai_patterns.md`。

## 顺序

先处理 FAIL 定位到的行（`dash_chain`、`quote_mismatch`），再按文件顺序逐段过一遍 WARN（`compressed_sentence`、`paren_dense`、`paren_in_title`、`formula_followup`、`figure_lead`），最后全文通读处理 INFO。

## 每段的改写流程

1. 读原段，列出其中的事实：数字、公式、引用、术语。这些是不可动的。
2. 判断段落要说的因果链是什么（为什么 → 怎么做 → 得到什么 → 意味着什么）；缺哪一环就从本节其他句子或上下文补，不新造事实。
3. 重写。对照风格卡 §3 的模板：
   - 括号里的完整句 → 独立句；括号里的数值参数 → 写进句子；括号里的英文缩写 → 只保留首次出现。
   - 引号术语：本文首次出现处保留引号并给定义；其后全部去引号。
   - `A—B—C` → 每个环节一句，说明它解决什么。
   - 缩写：正文用中文名，缩写在首次出现处以"中文全称（英文缩写）"给出；一句里不超过 3 个缩写。
   - 公式后："其中 …… 为 ……"逐个解释新符号，再一句直观含义。
   - 图表前一句说看什么，后两句说看到什么、意味着什么。
4. 自查：`anti_ai_patterns.md` §1 措辞是否出现；是否删掉了限定条件；数字是否原样。
5. 记 `REWRITE_LOG.md`：`文件:行 | 类型（paren/quote/dash/abbr/formula/figure/bridge） | 改前（≤60字） | 改后（≤60字）`。

## 不改的东西

- `$...$`、`$$...$$`、`{#eq:x}`、`@fig:/@tbl:/@eq:` 、`![](...)`、表格里的数值。
- 标题层级与编号（structure-audit 已经决定的合并除外）。
- 参考文献文件。

## 完成标准

- `fact_diff --strict` 0 FAIL（deepen 阶段带 `evidence:` 标记的新增数字除外）。
- `prose_lint` FAIL 0；四项密度进入语料 P75 以内；WARN 剩余项在 `POLISH_REPORT.md` 里逐条说明保留理由。
