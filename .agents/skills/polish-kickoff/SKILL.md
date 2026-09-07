---
name: polish-kickoff
description: mm-polish-workbench 入口。对任意 mm-draft-workbench 输出项目（含 paper/sections/*.md、reports/、results/、figures/）执行论文打磨：建立 polish/ 工作区 → prose-lint → structure-audit → deepen → rewrite-style → polish-verify，产出 polish/sections/*.md 改写稿与前后对照报告。原始 sections 与 Word 一律不改。用户说"打磨/润色这个项目的论文、跑 polish、开始 polish"时使用。
---

# polish-kickoff

## 输入与前提

- 输入：一个 draft 项目目录 `<proj>`，至少含 `paper/sections/*.md`。有 `reports/`、`results/`、`figures/*/README.md` 则作为扩写证据；没有则只做文风与结构层。
- 不需要 Word、pandoc、LibreOffice。polish 只处理 Markdown 句子；用户自己把改后的句子搬进 Word。
- 公式锁定：`$...$`、`$$...$$ {#eq:x}` 及编号一律不改（用户决定）。

## 工作区（在 `<proj>/polish/` 下，不触碰 `<proj>/paper/`）

```text
<proj>/polish/
├── FACTS.json           # facts_extract 的事实账本（基准）
├── PROSE_LINT.md        # 原稿 lint
├── STRUCTURE_PLAN.md    # structure-audit 输出：每问处理链表 + merge/expand/reorder/add_bridge/back_to_draft
├── sections/            # 改写稿（从 paper/sections 复制后逐文件改写）
├── REWRITE_LOG.md       # 每处改动：文件:行、类型、改前→改后（截断）、依据
├── FACT_DIFF.md         # 原稿 vs 改写稿事实零漂移检查
├── PROSE_LINT_after.md  # 改写稿 lint
└── POLISH_REPORT.md     # 前后指标对照 + 遗留问题 + 需回 draft 的清单
```

## 流程

```text
0 复制 paper/sections → polish/sections；facts_extract → FACTS.json
1 prose-lint       python .agents/skills/prose-lint/scripts/prose_lint.py <proj>/paper/sections --out <proj>/polish/PROSE_LINT.md --json <proj>/polish/prose_lint.json
2 structure-audit  读 PROSE_LINT + sections + reports → 写 STRUCTURE_PLAN.md（人可先审）
3 deepen           按 PLAN 里的 expand/add_bridge，仅用 reports/results/figures README 中已有事实扩写
4 rewrite-style    按 writing_style_card 逐段改文风；每段改完自查禁止项
5 polish-verify    fact_diff（--strict 必须 0 FAIL）→ prose_lint 复核 → POLISH_REPORT.md
```

每个阶段完成后先跑对应脚本再进入下一阶段；`fact_diff` 有 FAIL 时不得进入 verify 的报告环节，回到 3/4 修。

## 输出给用户的东西

- `polish/sections/*.md`：改写稿，逐文件对应原稿，便于逐段搬进 Word。
- `polish/POLISH_REPORT.md`：前后指标表（括号/引号/破折号/缩写密度、各问字数、标题数）、剩余 WARN、`back_to_draft` 清单。
- 不生成 docx，不改 `paper/`。

## 禁止

- 修改 `paper/sections/`、`paper/main.docx`、`data/`、`results/`、`reports/`、`figures/`。
- 新增原稿与 draft 报告中不存在的数字、实验、结论。
- 改公式、编号、引用标签。
- 在改写稿正文里出现内部文件名（`reports/`、`figures/`、`polish/`、`AGENTS.md`）。
