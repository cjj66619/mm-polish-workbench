# AGENTS.md — mm-polish-workbench 规则

本仓库是一套给 Devin 用的 skills（`.agents/skills/`），输入是 **任意** `mm-draft-workbench` 输出项目，输出是该项目 `polish/` 目录下的改写稿与报告。它是 draft 的下游，不重做模型、不重跑数据、不生成 Word。

## 工作流

```text
polish-kickoff → prose-lint → structure-audit → deepen → rewrite-style → polish-verify
```

各阶段的输入输出只通过 `<proj>/polish/` 下的文件交接：`FACTS.json`、`PROSE_LINT.md`、`STRUCTURE_PLAN.md`、`sections/`、`REWRITE_LOG.md`、`FACT_DIFF.md`、`POLISH_REPORT.md`。

## 硬规则

1. **只改 `polish/sections/*.md`**。`paper/`（含 `main.docx`、`sections/`）、`data/`、`results/`、`reports/`、`figures/`、`code/` 一律只读。
2. **公式锁定**。`$...$`、`$$...$$`、`{#eq:}` 及所有引用标签、图片路径、表格数值不改；只改公式与图表周围的中文句子。
3. **事实零漂移**。`fact_diff --strict` 必须 0 FAIL 才能出报告；扩写只用 `reports/`、`results/`、`figures/*/README.md`、代码 docstring、原稿中已有的事实，新增数字要在 `REWRITE_LOG.md` 标 `evidence:<文件>`。
4. **缺证据回 draft**。没有基线、没有检验、没有图的环节写进 `POLISH_REPORT.md` 的"回 draft 清单"，不在 polish 阶段编造。
5. **通用性**。不假设题型、问题数量、章节文件名、模型名；问题章节靠一级标题匹配 `问题 N`，证据靠文件契约（`reports/*.md`、`results/`、`figures/*/README.md`）。
6. **正文干净**。改写稿中不得出现 `reports/`、`figures/`、`results/`、`polish/`、`run_all`、`AGENTS.md`、`plan.md`、`todo.md`。
7. **脚本约束**。Python 3.10+ 标准库；`pathlib`；文本 I/O 显式 `encoding="utf-8"`；stdout `reconfigure(encoding="utf-8")`；不写绝对路径；不调用 bash。语料脚本 `scripts/corpus_stats.py` 例外地依赖 pymupdf/python-docx，仅维护阈值时运行。
8. **阈值有出处**。lint 阈值只来自 `_references/corpus_stats.json`（脚本生成，勿手改）；改规则先改 `corpus_stats.py` 再重跑。仓库不存 PDF 语料。

## 常见任务

| 任务 | 做法 |
| --- | --- |
| 打磨一个 draft 项目 | 读 `polish-kickoff/SKILL.md`，按六阶段走 |
| 只想看问题不改稿 | `python .agents/skills/prose-lint/scripts/prose_lint.py <proj>/paper/sections` |
| 增加语料 / 调阈值 | `python scripts/corpus_stats.py <pdf 目录> --out-json ... --out-md ...` |
| 加 lint 规则 | 先在语料上验证该模式在优秀论文中确实少见（`anti_ai_patterns.md` 记录计数），再加进 `prose_lint.py` |
| 自检仓库 | `python scripts/smoke_test.py` |
