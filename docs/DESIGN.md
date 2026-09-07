# mm-polish-workbench 设计方案（v0）

> 定位：mm-draft-workbench 的下游。输入是任意一个 draft 输出项目文件夹（`projects/<年>-<题号>/`），输出是同一文件夹里"文笔与结构达到优秀论文水准"的论文。与题目、学科无关，只依赖 draft 项目的文件契约。

## 0. 先说清楚问题是什么（用你给的 14 篇国一论文实测）

对 14 篇优秀论文（2023 E 题 10 篇 + 2024 E 题 4 篇）与本次 E 题 Word 初稿跑同一套脚本 `corpus_stats.py`，统计范围都是正文（摘要起、参考文献止，排除附录代码）。每千汉字归一化：

| 指标 | 优秀论文 P25 / P50 / P75 | 本稿 | 倍数（对 P50） |
| --- | --- | ---: | ---: |
| 全角括号 `（` / 千字 | 2.0 / 4.3 / 5.6 | **14.9** | 3.5× |
| 中文引号 `“` / 千字 | 0.1 / 0.3 / 2.2 | **10.7** | 31× |
| 破折号 `—` / 千字 | 0 / 0.03 / 0.28 | **2.69** | 90× |
| `A—B—C` 三段以上名词串 / 千字 | 0 / 0 / 0（14 篇里一处都没有） | **0.26** | — |
| 英文大写缩写 / 千字 | 1.4 / 2.5 / 3.3 | **14.8** | 6× |
| 引号闭合错误 `“…“` | 全部 0 | **79 处** | 构建 bug |
| 正文汉字数 | 22.6k / 29.4k / 32.9k | **15.6k** | 0.53× |
| 单个"问题 N"章节汉字数（n=32 章） | 3.3k / 5.4k / 9.3k | 问题一 2.3k、问题二 1.5k、问题三 3.1k、问题四 2.0k | 全部低于 P25 |
| 二级标题数 | 16 / 17 / 23.5 | **36** | 1.5× P75 |
| 三级标题数 | 14.5 / 21 / 26.5 | 30 | 高于 P75 |
| 三级节正文 < 300 字 | — | **13 / 30** | — |
| 句长中位 / P90（字） | 41 / 121 | 47 / 97 | 正常 |
| 行内枚举 `(1)(2)` / 千字 | 0.7 / 1.3 / 2.0 | 1.15 | 正常 |
| 连接词（首先/其次/从而/此外…）/ 千字 | 2.5 / 2.8 / 3.7 | 0.58 | **偏低** |

三个反直觉的发现，直接影响 lint 规则怎么定：

1. **"AI 味"不来自连接词。** 优秀论文"首先/从而/最后/此外/可以看出"用得比我们多 5 倍——它们是论证展开的标志。我们的问题恰恰是**连接词少、名词串多**：把本该用三句话讲的因果链压成一个带引号带破折号的名词。所以 lint 不该封杀连接词，而要抓"一句话里 ≥2 个引号术语或 ≥2 个破折号"这类压缩表达。
2. **篇幅差距是结构性的，不是字数问题。** 我们的正文只有优秀论文的一半，但二级标题数是它们的 1.5 倍以上：标题多、每节短。优秀论文每个"问题 N"章节中位 5.4k 字、三级标题与二级标题之比约 1.2，而我们每个问题章节都不到 P25。也就是说要做的不是"多写点"，而是"合并小节 + 把每一问按处理链讲透"。
3. **英文缩写密度 6 倍**（RF、CNN、DANN、MMD、SHAP、BPFO…）叠加括号与引号，是"生硬机械"的直接原因；优秀论文倾向首次给中文全称并在后文用中文。

所以 polish 要解决四类**可度量**的问题：括号/引号/破折号/缩写造成的堆砌感、名词串代替因果叙述、节碎段短、问题处理链不完整。四类都能先由脚本量化、再由 LLM 改写、再由脚本复核——这就是 draft 工作台"lint → 改 → 复核"的套路，可以直接复用。

## 0.5 已定决策（覆盖下文与之冲突的内容）

| 决策 | 结论 | 对下文的影响 |
| --- | --- | --- |
| 仓库 | 独立仓库 `mm-polish-workbench` | §3 按此实现 |
| Word 冻结点 | **保持在 draft 末尾不动**，polish 不生成、不覆盖 `paper/main.docx` | §1 决策 1 中"冻结点后移"作废；第 6 步 `docx-build --freeze` 删除 |
| 输出形态 | polish 只读写 Markdown 句子：改写稿在 `<proj>/polish/sections/*.md`，`paper/sections/` 原样保留；用户自己把句子搬进 Word | §1 决策 4 中"`paper/sections/` 原地更新、归档 `sections_v<N>`"作废 |
| 公式 | 锁定不改（LaTeX、编号、引用标签），只打磨公式前后的文字；对公式本身的意见只能进"回 draft 清单" | `fact_diff` 把公式任何变化判 FAIL；`formula_followup` 规则查周边 |
| 中间产物位置 | 全部在 `<proj>/polish/`，不写 `<proj>/reports/` | 下文 `reports/PROSE_LINT.md` 等一律读作 `polish/…` |

实现状态见 README"状态"节；skills 的最终规则以各 `SKILL.md` 与 `AGENTS.md` 为准，本文档保留设计推导与语料分析。

## 1. 总体架构

```text
draft 项目 (paper/sections/*.md + reports/ + results/ + figures/)
   │
   ├─ 0 polish-intake      读项目 → 事实账本 polish/FACTS.json（所有数字/符号/图表/结论，只读约束）
   ├─ 1 prose-lint         脚本：文风与结构度量 → reports/PROSE_LINT.md（FAIL/WARN，逐节逐条）
   ├─ 2 structure-audit    LLM+脚本：每问处理链完整性 → polish/STRUCTURE_PLAN.md（合并/扩写/重排清单）
   ├─ 3 deepen             LLM：按 PLAN 扩写薄弱节，只能用 FACTS/reports/code 里已有证据
   ├─ 4 rewrite-style      LLM：按 style card 逐节改写文笔，数字零改动
   ├─ 5 polish-verify      脚本：prose-lint 再跑必须改善 + fact_diff 数字零漂移 + 6verity/consistency-auditor
   └─ 6 docx-build --freeze（复用 draft 的 skill）
```

关键决策：

1. **在 Markdown 上打磨，不在 Word 上打磨。** LLM 改 docx 不可控、不可 diff。因此 polish 插在 draft 流程的 `draft-writing` 与 `docx-build` 之间；"Word 冻结"从 draft 的终点后移到 polish 的终点。对已冻结的老项目，用 `build_docx.py --force`（自动备份）重生成一次即可，这是 draft 规则明确允许的路径。
2. **事实账本是硬约束。** 步骤 0 把 `RESULTS_REPORT.md`、`results/*.csv|json`、符号表、图表清单、每问结论抽成 `FACTS.json`；步骤 3/4 的任何输出都要通过 `fact_diff.py`：账本里的每个数字在新旧文本中出现次数一致、不新增账本外的数字。这条把"改文笔"与"改结论"彻底隔开，也是防编造的唯一可靠手段。
3. **度量先于改写。** 所有"AI 味"的判断都落成 `prose_lint.py` 的规则和阈值，阈值来自优秀论文语料统计（见 §4），而不是拍脑袋。改写完必须再 lint，指标不改善就不算完成。
4. **阶段间只靠文件交接**，与 draft 一致：`polish/` 目录放中间产物，`paper/sections/` 原地更新，旧版归档到 `paper/sections_v<N>/`。

## 2. 各阶段细化

### 0 polish-intake

- 输入：项目根。读 `project.yaml`、`paper/paper.yaml`、`paper/sections/*.md`、`reports/*.md`、`results/`、`figures/*/README.md`（图的五要素 docstring 是扩写的好素材）、`code/*.py` 的模块 docstring。
- 输出 `polish/FACTS.json`：
  - `numbers[]`：值、单位、出处文件、在正文出现的章节；
  - `symbols[]`：符号说明表；
  - `figures[]/tables[]/equations[]`：id、题注、被引用位置；
  - `chain[]`：每问的"输入 ← 前问输出 / 输出 → 后问输入"关系（从 02_analysis 与各问小结抽取）。
- 输出 `polish/BASELINE.md`：本项目 lint 初值，作为 polish 完成的对照。

### 1 prose-lint（纯脚本，可移植，随项目 vendored 进 `tools/`）

规则分三组，每条给 FAIL/WARN/INFO 与逐处定位（文件:行）：

**文风**
- `paren_density`：括号对 / 千字 > 阈值（WARN），单段 ≥ 3 对（WARN）；括号内含完整句（含谓语）的（WARN，建议改成正文句）。
- `quote_coinage`：引号内为自造术语（非引用原文、非题面用语）超过 N 次；同一术语反复加引号（应"首次定义，后文裸用"）。
- `quote_mismatch`：`“…“` / `”…”`（FAIL，这是构建 bug）。
- `dash_chain`：一句内 ≥ 3 个破折号/连字符串起的名词链（WARN，建议改成分步句或流程图引用）。
- `enum_inline`：`(1)…(2)…(3)…` 行内枚举密度（WARN）。
- `sentence_len`：> 80 字长句、< 12 字碎句占比。
- `compressed_sentence`：一句内 ≥ 2 个引号术语、或 ≥ 2 个破折号、或 ≥ 3 个英文缩写（WARN，这是"名词串代替叙述"的直接特征）。
- `connective_low`：连接词密度低于语料 P25（INFO，提示论证展开不足；**不**反向封杀连接词）。
- `ai_phrases`：仅保留语料里几乎不出现而 LLM 高频的词（"赋能""旨在""值得注意的是""综上所述"等，需再用语料校验），词表放 `_references/anti_ai_patterns.md`。
- `abbrev_density`：英文缩写 / 千字 > 语料 P75（WARN）；首次出现无中文全称（WARN）。

**结构**
- `thin_section`：三级节正文 < 300 字或 < 2 段（WARN）；四级标题存在（WARN）。
- `heading_run`：标题后紧跟标题、无过渡句（WARN）。
- `para_len_dist`：中位段长 < 100 字（WARN，条目化写法）。
- `formula_followup`：编号公式后 2 段内无符号解释/直观说明（WARN）。
- `figure_lead`：图表前无引导句、后无解读句（WARN）。
- `problem_skeleton`：每问是否具备 N.1 分析 / N.2 建立 / N.3 求解 / N.4 结果与验证 / N.5 小结（缺 N.4/N.5 → FAIL；这条已在 `huaweibei_excellent_paper_patterns.md` §6 有雏形）。
- `chain_link`：每问小结是否点明"交给下一问什么"、下一问分析是否承接（WARN）。

**篇幅与配比**
- 每问正文字数、图数、表数、公式数与全篇占比；与语料分布比较给出 INFO/WARN（例如某问 < 全篇 10% 且非附属问）。

输出 `reports/PROSE_LINT.md`（汇总表 + 逐条定位）与 `polish/prose_lint.json`（给后续 LLM 步骤消费）。

### 2 structure-audit

- 输入：`PROSE_LINT`、`FACTS.chain`、`02_analysis.md`、各问小结、`ANALYSIS_MODELING_REPORT.md`。
- 用一条通用的"问题处理链"模板对每问打分（每环节：有/薄/无 + 证据出处）：

```text
题意拆解 → 数据/机理观察（为什么这样建模）→ 模型建立（公式 + 每个设计选择的理由）
→ 求解（算法/参数/规模）→ 中间结果（不只有最终指标）→ 检验（基线/扰动/误差）
→ 结果解读（回到题目语言）→ 与下一问的衔接
```

- 输出 `polish/STRUCTURE_PLAN.md`：逐节操作清单，只有四种动作——`merge`（碎节并入上级，改为段落+主题句）、`expand`（扩写，注明可用证据来自哪个 report/CSV/图 README）、`reorder`、`add_bridge`（加过渡/衔接段）。每条注明预期字数区间。
- 若发现某问"检验"环节无任何证据可用（结果里根本没有），**不在 polish 里补做实验**，而是写进 `todo.md` 交回 draft 侧（`robustness-checker`）。这是 polish 的边界。

### 3 deepen（扩写）

- 逐条执行 PLAN 的 `expand`：素材只允许来自 FACTS、reports、code docstring、图 README 五要素；扩写方向是"为什么这样做、机理/直觉、中间量、和备选方案的取舍、结果意味着什么"，而不是堆更多数字。
- 单节单次调用，prompt 里带：该节现文 + 允许使用的证据片段 + 目标字数 + 该问的处理链缺口。
- 每节写完立刻 `fact_diff.py` 校验，不过就回滚该节。

### 4 rewrite-style（改文笔）

- 逐节改写，prompt 里带 `_references/writing_style_card.md`（规则）+ `exemplar_paragraphs.md`（优秀论文段落范式，按"问题分析段 / 模型建立段 / 结果解读段 / 小结段"分类的短样例，只学句法不学内容）+ 本节 lint 命中清单。
- style card 核心条目（初版）：
  1. 括号：只留单位、缩写、公式编号引用；解释性内容改为正文句或表格。
  2. 引号：术语首次出现"定义句"，之后裸用；不给方法起绰号。
  3. 方法链：破折号串改为"首先…；其次…；最后…"的分步句，或引用流程图后逐步解释。
  4. 节 → 段：三级节正文不足时并入上级，用主题句开头、用过渡句收尾。
  5. 公式后必跟：符号含义 + 一句直观意义 + （如有）取值来源。
  6. 图表：前有引导句（要看什么），后有解读句（看到了什么、意味着什么）。
  7. 结论回到题目语言，不停留在指标名。
  8. 数字、单位、符号、图表编号一律不动。
- 输出到 `paper/sections/`，旧版归档 `paper/sections_v1/`，并写 `polish/REWRITE_LOG.md`（每节改了什么类型的问题、字数前后）。

### 5 polish-verify

- `prose_lint.py` 复跑：与 BASELINE 比，FAIL 归零，WARN 至少下降 X%（阈值可配）。
- `fact_diff.py`：数字零漂移、图表引用集合不变、符号表一致。
- 复用 draft 的 `consistency-auditor` / `6verity`（Markdown 源 vs `RESULTS_REPORT.md`）。
- 输出 `reports/POLISH_REPORT.md`：前后指标对照表 + 未解决项 + 交回 draft 侧的 todo。
- 通过后 `docx-build --pdf --strict` → `--freeze`，`HANDOFF.md` 追加 polish 阶段行。

## 3. 仓库结构（建议）

```text
mm-polish-workbench/
  .agents/skills/
    polish-kickoff/            入口：检查 draft 契约、建 polish/、跑 intake+lint、给出 PLAN 草稿
    prose-lint/scripts/        prose_lint.py, fact_diff.py, facts_extract.py（纯 Python，vendored 到项目 tools/）
    structure-audit/
    deepen/
    rewrite-style/
    polish-verify/
    _references/
      writing_style_card.md        改写规则（上面 §2.4）
      anti_ai_patterns.md          词表 + 句式模式（可持续增补）
      exemplar_paragraphs.md       优秀论文段落范式（按段落功能分类；短引用+来源，或改写为范式模板）
      problem_chain_template.md    处理链模板与打分口径
      corpus_stats.md              语料统计结果（阈值来源）
  scripts/
    corpus_stats.py            对一批优秀论文 PDF 跑同一套 prose_lint 指标 → 生成阈值
    smoke_test.py              用 examples/demo-drug-decay 跑完整 polish 流程
  AGENTS.md / README.md
```

与 draft 的关系：不复制 draft 的 skills，只依赖其项目文件契约；`prose_lint.py` 同时可以反向贡献给 draft（写作阶段就 lint），把问题消灭在初稿。

## 4. 阈值怎么来（"参照开源资料"落地）

- `corpus_stats.py` 已写出并在你给的 14 篇上跑通（§0 的表就是它的输出），后续直接放进新仓库 `scripts/`。`prose_lint.py` 的默认阈值取语料 **P75**（WARN）与 **max**（FAIL）；14 篇样本量小，阈值以后随语料增补自动更新，仓库只存统计结果 `corpus_stats.md`，不存 PDF。
- 初版阈值（P75）：括号 ≤ 5.6/千字、引号 ≤ 2.2/千字、破折号 ≤ 0.3/千字、名词串 = 0、缩写 ≤ 3.3/千字、二级标题 ≤ 24、问题章节 ≥ 3.3k 字（低于则 WARN "单薄"）、三级节 ≥ 300 字。
- `_references/huaweibei_excellent_paper_patterns.md` 已有 75 篇的**结构**统计（页数、图表、公式），与这里的**文风**统计互补，两者合并成 `corpus_stats.md`。
- 本次 E 题稿是第一个校准样本（"改前"），改后再跑一遍就是第一组"前后对照"。

## 5. 边界与风险

- **polish 不改模型、不补实验、不加数字。** 缺证据的环节写回 `todo.md` 交 draft 侧。这条守不住，"文笔优化"就会变成"编造"。
- **Word 冻结规则要改一处**：冻结点从 draft 末尾移到 polish 末尾；draft 的 `docx-build` 保留，但 `HANDOFF.md` 状态表加一行"文笔打磨"。
- **LLM 改写不稳定**：靠"单节小步 + 每步 fact_diff + 归档可回滚"控制，而不是靠 prompt 祈祷。
- **先修 draft 侧的引号 bug**（`“…“`），否则 lint 的 `quote_mismatch` 永远是 FAIL。

## 6. 建议的推进顺序（按我的会话粒度）

1. 一个会话：建仓库骨架，放入已完成的 `corpus_stats.py` 与 `corpus_stats.md`；写 `prose_lint.py`（阈值读 corpus_stats）+ `fact_diff.py` + `facts_extract.py`，对 `examples/demo-drug-decay` 与本次 E 题稿跑出 `PROSE_LINT.md`；顺手修 draft 的引号 bug。
2. 一个会话：从 14 篇语料中抽取范式段落写 style card、anti_ai_patterns、problem_chain_template、exemplar 初版（只存短引用与句法模板，不存全文）。
3. 一个会话：structure-audit / deepen / rewrite-style / polish-verify 四个 skill，用 E 题稿走一遍完整流程，产出前后对照报告，据此修规则。
4. 之后：把 `prose_lint` 回灌到 draft 的写作阶段。

需要你决定的两件事：
- (a) 新仓库建在哪：独立 `mm-polish-workbench` 仓库（需要给 Devin 写权限，否则仍走 patch），还是放进 `mm-draft-workbench` 里作为 `polish/` 子目录？
- (b) 是否同意"冻结点后移到 polish 末尾"这条规则变更。
