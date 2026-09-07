---
name: _references
description: mm-polish-workbench 共享知识库：写作风格卡、AI 痕迹清单、问题处理链模板、优秀论文语料统计与阈值。其他 skills 按需读取，无需单独触发。
---

| 文件 | 用途 | 谁读 |
| --- | --- | --- |
| `writing_style_card.md` | 硬指标 + 句法改写模板 + 允许/禁止 | rewrite-style、deepen |
| `anti_ai_patterns.md` | 经语料校验的 AI 痕迹措辞与结构 | prose-lint 规则来源、rewrite-style |
| `problem_chain_template.md` | 每问 12 环节检查表、STRUCTURE_PLAN 格式 | structure-audit、deepen |
| `corpus_stats.md` / `corpus_stats.json` | 14 篇国一论文实测分布；json 是 prose_lint 的阈值文件 | prose_lint.py 自动读取 |

更新语料阈值：把新 PDF 放到任意目录，运行 `python scripts/corpus_stats.py <目录> --out-json .agents/skills/_references/corpus_stats.json --out-md .agents/skills/_references/corpus_stats.md`。不要把 PDF 提交进仓库。
