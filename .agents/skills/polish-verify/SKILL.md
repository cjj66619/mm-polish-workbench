---
name: polish-verify
description: polish 最后阶段。对 polish/sections 跑 fact_diff（零漂移）、prose_lint（复核）、内部名称与限定词丢失检查，生成 polish/POLISH_REPORT.md（前后指标对照、剩余 WARN 及理由、回 draft 清单、逐文件搬运指引）。任何 FAIL 未清零不得交付。
---

# polish-verify

## 命令

```bash
S=.agents/skills/prose-lint/scripts
python $S/fact_diff.py  <proj>/paper/sections <proj>/polish/sections --out <proj>/polish/FACT_DIFF.md --strict
python $S/prose_lint.py <proj>/polish/sections --out <proj>/polish/PROSE_LINT_after.md --json <proj>/polish/prose_lint_after.json --strict
```

## 人工核对项（脚本查不了的）

1. **限定条件没丢**：对照 `REWRITE_LOG.md`，抽查每处 `paren`/`dash` 类改动，原句中的"在源域上""假设 3 下""仅对 …"是否仍在。
2. **结论强度没涨**：改稿中新出现的"显著 / 明显优于 / 充分证明 / 最优"逐个回到证据核对；原稿与报告没有的删掉。
3. **公式周边**：每个 `{#eq:}` 后有"其中"句；符号说明表与正文首次定义一致。
4. **图表周边**：每个 `@fig:`/`@tbl:`/表格前有引导、后有解读。
5. **内部名称**：`grep -nE "reports/|figures/|results/|polish/|run_all|AGENTS.md|plan.md|todo.md" polish/sections/*.md` 必须为空。
6. **`evidence:` 新增数字**：`FACT_DIFF.md` 中 `numbers_added` FAIL 逐条对照 LOG 的 `evidence:` 来源文件，数字一致则在 REPORT 里放行并列出；否则改回。

## `polish/POLISH_REPORT.md` 结构

```markdown
# POLISH_REPORT — <项目名>

## 前后对照
| 指标 | 原稿 | 改稿 | 语料 P75 |
| 全角括号/千字 | 14.9 | 4.8 | 5.6 |
| ...（引号、破折号、缩写、正文汉字、H2/H3 数、各问字数） |

## FAIL 清零情况
- fact_diff：0 FAIL；放行的 evidence 新增数字 N 条（列表）
- prose_lint：0 FAIL

## 保留的 WARN 及理由
- `05_problem1.md:61` compressed_sentence：RMSE/R²/AIC 同句是指标并列，保留。

## 回 draft 清单（polish 不能解决）
- 问题二缺基线比较 …

## 搬进 Word 的指引
- 逐文件：polish/sections/05_problem1.md ↔ Word 第五章；改动集中在 §5.2、§5.3（见 REWRITE_LOG）。
- 公式、图、表在 Word 中原样保留，只替换文字段落。
```

## 交付条件

`FACT_DIFF.md` 与 `PROSE_LINT_after.md` 均 0 FAIL；人工核对 6 项完成并在 REPORT 中打勾；`paper/` 目录 `git status` 无改动。
