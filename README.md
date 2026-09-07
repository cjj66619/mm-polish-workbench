# mm-polish-workbench

`mm-draft-workbench` 的下游：把初稿项目里的论文 Markdown 章节打磨成接近优秀数学建模论文的文风与结构，**不碰模型、数据、公式和 Word**。

## 解决什么问题

draft 输出的论文技术上完整，但对照 14 篇华为杯国一论文有四类差距（实测，每千汉字）：

| | draft 稿 | 国一论文中位 |
| --- | ---: | ---: |
| 全角括号 | 14.9 | 4.3 |
| 中文引号 | 10.7 | 0.3 |
| 破折号（`A—B—C` 名词串） | 1.7 | 0.03 |
| 英文缩写 | 15.1 | 2.5 |
| 正文汉字 | 15.6k | 29.4k |
| 二级标题 | 36 | 17 |
| 单个"问题 N"章节 | 1.5k–3k | 5.4k |

字数一半、标题两倍、括号引号缩写三到三十倍——问题不是"写得少"，而是把因果叙述压成了名词串、把段落拆成了小节、每一问缺少完整的处理链（题意 → 数据 → 模型 → 求解 → 检验 → 解释 → 结论 → 交接）。

## 它做什么 / 不做什么

做：文风 lint（量化，阈值来自语料）、结构审计（每问 12 环节处理链）、基于已有证据的扩写、按风格卡改写、事实零漂移校验、前后对照报告。

不做：改数字、改公式、加实验、生成 Word、改 `paper/` 下任何文件。改写稿输出到 `<proj>/polish/sections/*.md`，由人逐段搬进 Word。

## 用法

```bash
# 只看问题
python .agents/skills/prose-lint/scripts/prose_lint.py <proj>/paper/sections --out <proj>/polish/PROSE_LINT.md

# 完整打磨：让 Devin 读 .agents/skills/polish-kickoff/SKILL.md，按六阶段执行
#   polish-kickoff → prose-lint → structure-audit → deepen → rewrite-style → polish-verify

# 改写后校验（任何数字/公式/引用漂移 → FAIL）
python .agents/skills/prose-lint/scripts/fact_diff.py <proj>/paper/sections <proj>/polish/sections --strict
```

## 仓库结构

```text
.agents/skills/
├── polish-kickoff/     入口与六阶段流程
├── prose-lint/         prose_lint.py · facts_extract.py · fact_diff.py（标准库，Py 3.10+）
├── structure-audit/    每问处理链审计 → STRUCTURE_PLAN.md
├── deepen/             按计划用已有证据扩写
├── rewrite-style/      按风格卡改文风
├── polish-verify/      零漂移 + 复核 + POLISH_REPORT.md
└── _references/        writing_style_card · anti_ai_patterns · problem_chain_template · corpus_stats（阈值）
scripts/
├── corpus_stats.py     从优秀论文 PDF 生成阈值（需 pymupdf）
└── smoke_test.py       在 examples/ 上跑 lint + 账本 + diff 自检
examples/demo-drug-decay/   draft 示例项目的 sections + RESULTS_REPORT（lint 的回归样本）
docs/DESIGN.md              设计文档与语料分析
```

## 状态

- `prose_lint` / `facts_extract` / `fact_diff` 可用，在示例项目与一篇真实 draft 稿上验证：真实稿 56 FAIL / 100 WARN，其中 `thin_section` 24 处、`quote_mismatch` 48 处、`dash_chain` 4 处，与人工判断一致。
- structure-audit / deepen / rewrite-style / polish-verify 为 skill 文档（由 Devin 执行），尚未在真实项目上完整跑过一轮。
- 语料 14 篇，阈值为初版；`scripts/corpus_stats.py` 可随时增补重算。仓库不保存 PDF。
