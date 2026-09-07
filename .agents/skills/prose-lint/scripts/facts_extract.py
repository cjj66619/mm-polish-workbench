"""facts_extract.py — 从论文 Markdown 章节提取"事实账本"（数字、公式、图表引用、标题）。

用法：
    python facts_extract.py <paper/sections 目录 或 单个 .md> [--out polish/FACTS.json]

只读输入。账本是 rewrite 阶段的"不可改动清单"，也是 fact_diff.py 比对的基准。
被视为事实的对象：
- 带上下文的数字（含小数、百分数、区间、科学计数），排除标题编号、列表编号、pandoc 标签、图片路径；
- 展示公式（$$...$$，按标签或归一化文本记录）；
- 行内公式的归一化文本；
- 交叉引用 @fig:/@tbl:/@eq:/@sec: 与图片路径；
- 标题（只作 INFO 对比，结构审计允许改标题）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

NUM = re.compile(r"(?<![\w.\-])[-−]?\d+(?:[.,]\d+)*(?:\s*[×x]\s*10\^?\{?-?\d+\}?|e-?\d+)?")
UNIT = re.compile(r"^\s*(%|％|‰|°C|℃|°|[A-Za-zμΩ]{1,5}(?:/[A-Za-zμ]{1,4})?(?:\^?\d)?|[阶维个次倍组条点转段层类种台次名人张份台年月日天时分秒块]|h\b|min\b|s\b)")


def norm_math(s: str) -> str:
    return re.sub(r"\s+", "", s.replace("\\,", "").replace("\\;", "").replace("\\!", ""))


def extract_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    numbers, inline_math, display, refs, images, headings = [], [], [], [], [], []
    lines = text.split("\n")
    in_code = in_math = False
    math_buf: list[str] = []
    math_start = 0
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if in_math:
            math_buf.append(line)
            if "$$" in line:
                in_math = False
                block = "\n".join(math_buf)
                m = re.search(r"\{#(eq:[\w\-]+)\}", block)
                body = norm_math(re.sub(r"\{#eq:[\w\-]+\}", "", block).replace("$$", ""))
                display.append({"label": m.group(1) if m else None, "line": math_start, "hash": hashlib.md5(body.encode()).hexdigest()[:10], "text": body[:200]})
            continue
        if s.startswith("$$"):
            if s.count("$$") >= 2:
                m = re.search(r"\{#(eq:[\w\-]+)\}", s)
                body = norm_math(re.sub(r"\{#eq:[\w\-]+\}", "", s).replace("$$", ""))
                display.append({"label": m.group(1) if m else None, "line": i, "hash": hashlib.md5(body.encode()).hexdigest()[:10], "text": body[:200]})
            else:
                in_math, math_buf, math_start = True, [line], i
            continue
        hm = re.match(r"^(#{1,6})\s+(.*)$", line)
        if hm:
            headings.append({"level": len(hm.group(1)), "title": hm.group(2).strip(), "line": i})
            continue
        for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", line):
            images.append({"path": m.group(1).split()[0], "line": i})
        for m in re.finditer(r"@((?:fig|tbl|eq|sec):[\w\-]+)", line):
            refs.append({"ref": m.group(1), "line": i})
        # 行内公式记录后替换掉，避免公式里的数字重复计入；但公式里的数字仍是事实，单独记
        def _im(m: re.Match) -> str:
            inline_math.append({"line": i, "text": norm_math(m.group(1))})
            return " " + m.group(1) + " "
        work = re.sub(r"\$([^$\n]+)\$", _im, line)
        work = re.sub(r"\{#[^}]*\}", "", work)
        work = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", work)
        work = re.sub(r"^\s*(\d+)\.\s+", "", work)  # 列表编号
        work = re.sub(r"^\s*(Table|Figure)\s*[:：]", "", work)
        for m in NUM.finditer(work):
            raw = m.group(0)
            after = work[m.end():m.end() + 12]
            um = UNIT.match(after)
            unit = um.group(1) if um else ""
            val = raw.replace(",", "").replace("−", "-").replace(" ", "")
            ctx = work[max(0, m.start() - 14):m.end() + 10].strip()
            numbers.append({"value": val, "unit": unit, "line": i, "ctx": ctx})
    return {"file": path.name, "numbers": numbers, "inline_math": inline_math, "display_math": display,
            "refs": refs, "images": images, "headings": headings}


def extract(src: Path) -> dict:
    files = sorted(src.glob("*.md")) if src.is_dir() else [src]
    return {"source": str(src), "files": [extract_file(f) for f in files]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    facts = extract(Path(a.src))
    tot = {k: sum(len(f[k]) for f in facts["files"]) for k in ("numbers", "inline_math", "display_math", "refs", "images", "headings")}
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(facts, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[facts_extract] {len(facts['files'])} 个文件：" + "，".join(f"{k} {v}" for k, v in tot.items()) + f" → {a.out}")
    else:
        print(json.dumps(facts, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
