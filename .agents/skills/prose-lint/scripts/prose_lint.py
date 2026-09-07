"""prose_lint.py — 数学建模论文 Markdown 章节的文风 / 结构 lint。

用法：
    python prose_lint.py <paper/sections 目录 或 单个 .md> [--out reports/PROSE_LINT.md] [--json polish/prose_lint.json]
                         [--thresholds <corpus_stats.json>] [--strict]

只读输入，不改任何文件。阈值默认取同仓库 `_references/corpus_stats.json` 里优秀论文语料的 P75（WARN）与 max（FAIL）。
统计前会剥掉公式、代码块、表格、图片引用与 pandoc 属性块，只对正文汉字计数。
退出码：--strict 下有 FAIL 返回 1，否则 0。
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_THRESHOLDS = HERE.parent.parent / "_references" / "corpus_stats.json"

# 语料里几乎不出现、LLM 高频的措辞（校验见 _references/anti_ai_patterns.md）
AI_PHRASES = ["赋能", "需要指出的是", "全方位", "有力支撑", "不难发现", "多维度", "值得一提的是", "众所周知",
              "不言而喻", "无疑", "毫无疑问", "极大地", "极具", "深远影响"]
# 论证展开的连接词（语料中位 2.8/千字；偏低提示叙述不展开）
CONNECTIVES = ["首先", "其次", "再次", "然后", "随后", "最后", "从而", "因此", "此外", "进而", "由此", "可以看出",
               "由此可见", "换言之", "一方面", "另一方面", "考虑到", "为此", "于是"]
PROBLEM_HEAD = re.compile(r"问题\s*[一二三四五六七八九十0-9]+")
SKELETON = {
    "分析": re.compile(r"问题分析|的分析|分析与"),
    "建立": re.compile(r"模型建立|建模|模型的建立|方法|模型构建"),
    "求解": re.compile(r"求解|计算|算法|训练"),
    "验证": re.compile(r"结果|验证|检验|分析结果|评价|误差|对比"),
    "小结": re.compile(r"小结|总结|结论"),
}


@dataclass
class Finding:
    level: str  # FAIL / WARN / INFO
    rule: str
    file: str
    line: int
    msg: str
    excerpt: str = ""


@dataclass
class Section:
    file: str
    level: int
    title: str
    line: int
    body_lines: list[tuple[int, str]] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(t for _, t in self.body_lines)


def zh(s: str) -> int:
    return sum(1 for c in s if "\u4e00" <= c <= "\u9fff")


def strip_markup(md: str) -> str:
    """去掉公式/代码/表格/图片/属性块，保留正文。行数保持不变，便于定位。"""
    out = []
    in_code = in_math = False
    for line in md.split("\n"):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            out.append("")
            continue
        if in_code:
            out.append("")
            continue
        if s.startswith("$$") and s.count("$$") == 1:
            in_math = not in_math
            out.append("")
            continue
        if in_math or s.startswith("|") or s.startswith("![") or s.startswith("<!--"):
            out.append("")
            continue
        line = re.sub(r"\$\$.*?\$\$", " 公式 ", line)
        line = re.sub(r"\$[^$]+\$", " 公式 ", line)
        line = re.sub(r"\{#[^}]*\}", "", line)  # pandoc 属性 {#eq:x}
        line = re.sub(r"@(fig|tbl|eq|sec):[\w\-]+", "图表", line)
        line = re.sub(r"`[^`]*`", "", line)
        out.append(line)
    return "\n".join(out)


def parse_sections(path: Path, md: str) -> list[Section]:
    secs: list[Section] = []
    cur: Section | None = None
    for i, line in enumerate(md.split("\n"), 1):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            cur = Section(path.name, len(m.group(1)), m.group(2).strip(), i)
            secs.append(cur)
        elif cur is not None:
            cur.body_lines.append((i, line))
    return secs


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"[。！？；]", text) if zh(s) >= 4]


def load_thresholds(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    s = d["summary"]
    return {
        "paren_full_per_k": (s["paren_full_per_k"]["p75"], s["paren_full_per_k"]["max"]),
        "quote_per_k": (s["quote_per_k"]["p75"], s["quote_per_k"]["max"]),
        "dash_per_k": (s["dash_per_k"]["p75"], s["dash_per_k"]["max"]),
        "en_abbr_per_k": (s["en_abbr_per_k"]["p75"], s["en_abbr_per_k"]["max"]),
        "connective_low": s["connective_per_k"]["p25"],
        "h2_max": s["h2"]["p75"],
        "problem_chapter_zh_p25": round(s["problem_chapter_zh"]["p25"]),
        "problem_chapter_q": s["problem_chapter_zh"],
        "thin_section_zh": 300,
        "long_sentence_zh": 80,
        "n_corpus": len(d["rows"]),
    }


class Linter:
    def __init__(self, th: dict) -> None:
        self.th = th
        self.findings: list[Finding] = []
        self.metrics: dict = {}

    def add(self, level: str, rule: str, file: str, line: int, msg: str, excerpt: str = "") -> None:
        self.findings.append(Finding(level, rule, file, line, msg, excerpt[:80]))

    # ---------- 全文级 ----------
    def lint_global(self, files: dict[str, str], secs: list[Section]) -> None:
        body = "\n".join(strip_markup(t) for t in files.values())
        n = zh(body)
        k = max(n, 1) / 1000
        m = self.metrics
        m["zh_chars"] = n
        m["paren_full_per_k"] = round(body.count("（") / k, 2)
        m["quote_per_k"] = round(body.count("“") / k, 2)
        m["dash_per_k"] = round(len(re.findall(r"—+", body)) / k, 2)
        m["en_abbr_per_k"] = round(len(re.findall(r"\b[A-Z][A-Za-z]*[A-Z]\b|\b[A-Z]{2,}\b", body)) / k, 2)
        m["connective_per_k"] = round(sum(body.count(c) for c in CONNECTIVES) / k, 2)
        m["ai_phrase_count"] = sum(body.count(p) for p in AI_PHRASES)
        sl = [zh(s) for s in sentences(body)]
        m["sent_median"] = st.median(sl) if sl else 0
        m["h1"], m["h2"], m["h3"] = (sum(1 for s in secs if s.level == L) for L in (1, 2, 3))
        m["h4plus"] = sum(1 for s in secs if s.level >= 4)
        for key, label in [("paren_full_per_k", "全角括号"), ("quote_per_k", "中文引号"), ("dash_per_k", "破折号"),
                           ("en_abbr_per_k", "英文缩写")]:
            p75, mx = self.th[key]
            v = m[key]
            if v > mx:
                self.add("FAIL", key, "*", 0, f"{label}密度 {v}/千字，超过优秀论文语料最大值 {mx}")
            elif v > p75:
                self.add("WARN", key, "*", 0, f"{label}密度 {v}/千字，超过优秀论文 P75 {p75}")
        if m["connective_per_k"] < self.th["connective_low"]:
            self.add("INFO", "connective_low", "*", 0,
                     f"连接词密度 {m['connective_per_k']}/千字低于语料 P25 {self.th['connective_low']}，提示论证展开不足（不是要堆连接词，而是要把因果链写成句子）")
        if m["h2"] > self.th["h2_max"]:
            self.add("WARN", "too_many_h2", "*", 0, f"二级标题 {m['h2']} 个，超过语料 P75 {self.th['h2_max']}；结合 thin_section 结果合并")
        if m["h4plus"]:
            self.add("WARN", "h4_exists", "*", 0, f"存在 {m['h4plus']} 个四级及以下标题，优秀论文极少使用")

    # ---------- 章节级 ----------
    def lint_sections(self, secs: list[Section], raw: dict[str, str]) -> None:
        # 问题章节字数 + 骨架
        for i, s in enumerate(secs):
            if s.level == 1 and PROBLEM_HEAD.search(s.title) and not re.search(r"重述|分析$", s.title):
                is_check_chapter = bool(re.search(r"灵敏度|稳健|检验|评价|误差", s.title))
                j = i + 1
                chunk = [s]
                while j < len(secs) and secs[j].level > 1:
                    chunk.append(secs[j])
                    j += 1
                n = sum(zh(strip_markup(c.text)) for c in chunk)
                self.metrics.setdefault("problem_chapters", {})[s.title] = n
                if n < self.th["problem_chapter_zh_p25"]:
                    self.add("WARN", "problem_chapter_thin", s.file, s.line,
                             f"「{s.title}」正文 {n} 字，低于优秀论文问题章节 P25（{self.th['problem_chapter_zh_p25']} 字）；按处理链检查缺哪一环")
                titles = " / ".join(c.title for c in chunk[1:])
                missing = [k for k, rx in SKELETON.items() if not rx.search(titles)]
                if is_check_chapter:
                    missing = [k for k in missing if k == "小结"]
                if missing:
                    lvl = "FAIL" if ("验证" in missing or "小结" in missing) else "WARN"
                    self.add(lvl, "problem_skeleton", s.file, s.line, f"「{s.title}」缺少环节：{'、'.join(missing)}（子标题：{titles or '无'}）")
        # 薄节 / 标题连排 / 标题带括号
        for i, s in enumerate(secs):
            body = strip_markup(s.text)
            n = zh(body)
            paras = [p for p in s.text.split("\n") if p.strip()]
            nxt = secs[i + 1] if i + 1 < len(secs) else None
            if s.level >= 3 and n < self.th["thin_section_zh"]:
                self.add("WARN", "thin_section", s.file, s.line, f"三级节「{s.title}」正文仅 {n} 字（<{self.th['thin_section_zh']}），建议并入上级节改为段落")
            if nxt and nxt.level > s.level and n == 0:
                self.add("WARN", "heading_run", s.file, s.line, f"「{s.title}」之后直接是子标题，缺过渡句")
            if re.search(r"[（(].*[）)]", s.title):
                self.add("WARN", "paren_in_title", s.file, s.line, f"标题带括号补充：「{s.title}」，把补充信息放进正文")
            if len(paras) and s.level >= 2 and st.median([zh(p) for p in paras if not p.startswith("$$")] or [0]) < 60 and n > 300:
                self.add("INFO", "short_paragraphs", s.file, s.line, f"「{s.title}」段落中位长度 <60 字，条目化写法，检查是否应合并成论证段")
        # 行级
        for fname, text in raw.items():
            self.lint_lines(fname, text)

    def lint_lines(self, fname: str, text: str) -> None:
        lines = text.split("\n")
        clean = strip_markup(text).split("\n")
        for i, (line, cl) in enumerate(zip(lines, clean), 1):
            if not cl.strip() or cl.lstrip().startswith("#"):
                # 公式后是否有解释
                if line.strip().startswith("$$") and "{#eq" in line:
                    follow = " ".join(clean[i:i + 3])
                    if zh(follow) < 20 or not re.search(r"其中|式中|表示|为|含义|意味", follow):
                        self.add("WARN", "formula_followup", fname, i, "编号公式后 3 行内没有符号解释/直观说明")
                is_table_start = re.match(r"^\s*\|", line) and i > 1 and not lines[i - 2].strip().startswith("|")
                if (line.strip().startswith("![") or is_table_start) and not re.search(r"symbols|符号", fname):
                    window = [l for l in clean[max(0, i - 5):i - 1] if not re.match(r"^\s*(Table|Figure|图|表)\s*[:：]", l)]
                    if not re.search(r"图|表", " ".join(window)):
                        self.add("WARN", "figure_lead", fname, i, "图/表之前 4 行内没有引导句（要看什么）")
                continue
            if re.search(r"“[^”“]{1,60}“", cl) or re.search(r"”[^”“]{1,60}”", cl):
                self.add("FAIL", "quote_mismatch", fname, i, "引号闭合错误（“…“ 或 ”…”）", cl.strip())
            q = len(re.findall(r"“[^”]{1,40}”", cl))
            d = len(re.findall(r"—+", cl))
            ab = len(set(re.findall(r"\b[A-Z]{2,}\b", cl)))
            if q >= 2 or d >= 2 or ab >= 4:
                self.add("WARN", "compressed_sentence", fname, i,
                         f"名词串式表达：引号术语 {q}、破折号 {d}、缩写 {ab}；拆成因果句", cl.strip())
            if re.search(r"(?:[^—\n，。]{1,25}—){2,}[^—\n，。]{1,25}", cl):
                self.add("FAIL", "dash_chain", fname, i, "A—B—C 三段以上名词串（优秀论文语料中为 0）", cl.strip())
            pc = cl.count("（")
            if pc >= 3:
                self.add("WARN", "paren_dense", fname, i, f"一段内 {pc} 对括号", cl.strip())
            for m in re.finditer(r"（([^（）]{12,})）", cl):
                inner = m.group(1)
                if re.search(r"[，；]", inner) and zh(inner) >= 12:
                    self.add("INFO", "paren_sentence", fname, i, "括号内是完整句/多个子句，改为正文句或表格", inner)
            for p in AI_PHRASES:
                if p in cl:
                    self.add("INFO", "ai_phrase", fname, i, f"措辞「{p}」在优秀论文语料中几乎不出现", cl.strip())
            for s in sentences(cl):
                if zh(s) > self.th["long_sentence_zh"] + 40:
                    self.add("INFO", "long_sentence", fname, i, f"句长 {zh(s)} 字", s.strip())


def render_md(lint: Linter, src: str) -> str:
    m = lint.metrics
    th = lint.th
    lv = {"FAIL": 0, "WARN": 0, "INFO": 0}
    for f in lint.findings:
        lv[f.level] += 1
    L = [f"# PROSE_LINT — {src}", "",
         f"FAIL {lv['FAIL']}，WARN {lv['WARN']}，INFO {lv['INFO']}（阈值来自 {th['n_corpus']} 篇优秀论文语料，见 _references/corpus_stats.md）", "",
         "## 全文指标", "", "| 指标 | 本稿 | 语料 P75 | 语料 max |", "| --- | ---: | ---: | ---: |"]
    for key, label in [("paren_full_per_k", "全角括号/千字"), ("quote_per_k", "中文引号/千字"), ("dash_per_k", "破折号/千字"),
                       ("en_abbr_per_k", "英文缩写/千字")]:
        L.append(f"| {label} | {m[key]} | {th[key][0]} | {th[key][1]} |")
    L += [f"| 连接词/千字 | {m['connective_per_k']} | （语料 P25 {th['connective_low']}，低于则 INFO） | |",
          f"| 正文汉字 | {m['zh_chars']} | | |",
          f"| 标题 H1/H2/H3/H4+ | {m['h1']}/{m['h2']}/{m['h3']}/{m['h4plus']} | H2 ≤ {th['h2_max']} | |", ""]
    if m.get("problem_chapters"):
        q = th["problem_chapter_q"]
        L += [f"## 问题章节字数（语料 P25/P50/P75 = {q['p25']}/{q['p50']}/{q['p75']}）", ""]
        L += [f"- {t}：{n} 字" for t, n in m["problem_chapters"].items()]
        L.append("")
    for level in ("FAIL", "WARN", "INFO"):
        items = [f for f in lint.findings if f.level == level]
        if not items:
            continue
        L += [f"## {level}（{len(items)}）", ""]
        by_rule: dict[str, list[Finding]] = {}
        for f in items:
            by_rule.setdefault(f.rule, []).append(f)
        for rule, fs in by_rule.items():
            L.append(f"### {rule}（{len(fs)}）")
            L.append("")
            for f in fs[:60]:
                loc = f"`{f.file}:{f.line}`" if f.line else "全文"
                ex = f" — {f.excerpt}" if f.excerpt else ""
                L.append(f"- {loc} {f.msg}{ex}")
            if len(fs) > 60:
                L.append(f"- …另 {len(fs) - 60} 条见 JSON")
            L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--thresholds", default=str(DEFAULT_THRESHOLDS))
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    src = Path(a.src)
    files = sorted(src.glob("*.md")) if src.is_dir() else [src]
    files = [f for f in files if not re.search(r"references|参考文献", f.stem, re.I)]
    raw = {f.name: f.read_text(encoding="utf-8") for f in files}
    secs: list[Section] = []
    for f in files:
        secs += parse_sections(f, raw[f.name])
    lint = Linter(load_thresholds(Path(a.thresholds)))
    lint.lint_global(raw, secs)
    lint.lint_sections(secs, raw)
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    lint.findings.sort(key=lambda f: (order[f.level], f.rule, f.file, f.line))
    report = render_md(lint, str(src))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(report, encoding="utf-8")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({"metrics": lint.metrics, "findings": [asdict(f) for f in lint.findings]},
                                           ensure_ascii=False, indent=1), encoding="utf-8")
    nf = sum(1 for f in lint.findings if f.level == "FAIL")
    nw = sum(1 for f in lint.findings if f.level == "WARN")
    print(report if not a.out else f"[prose_lint] FAIL {nf}，WARN {nw}，INFO {len(lint.findings) - nf - nw} → {a.out}")
    return 1 if (a.strict and nf) else 0


if __name__ == "__main__":
    raise SystemExit(main())
