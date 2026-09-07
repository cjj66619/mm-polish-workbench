"""fact_diff.py — 比对改写前后两套 Markdown 章节的事实账本，保证"数字/公式/图表引用零漂移"。

用法：
    python fact_diff.py <原始 sections 目录> <改写后 sections 目录> [--out reports/FACT_DIFF.md] [--strict]

判定：
- FAIL：原稿数字（值+单位）在改稿中消失或改稿新增带单位/小数的数字；展示公式或行内公式集合有任何变化；
        交叉引用/图片在改稿中消失。
- WARN：改稿新增无单位小整数（≤20，可能是"分三步"这类叙述用数）；改稿新增交叉引用。
- INFO：标题增删改（结构审计允许改标题）。
两侧都按全文多重集比对（允许章节合并、段落移动）；同名文件再给出逐文件差异供定位。
退出码：--strict 下有 FAIL 返回 1。
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from facts_extract import extract  # noqa: E402


def num_key(n: dict) -> str:
    v = n["value"]
    try:
        f = float(v.replace("×10^", "e").replace("×10", "e").replace("x10^", "e").replace("{", "").replace("}", ""))
        v = repr(f) if "." in v or "e" in v.lower() else str(int(f))
    except ValueError:
        pass
    return f"{v}{('␣' + n['unit']) if n['unit'] else ''}"


def bag(files: list[dict], kind: str) -> tuple[Counter, dict[str, list[str]]]:
    c: Counter = Counter()
    where: dict[str, list[str]] = {}
    for f in files:
        for item in f[kind]:
            if kind == "numbers":
                k = num_key(item)
                loc = f"{f['file']}:{item['line']} …{item['ctx']}…"
            elif kind == "display_math":
                k = f"{item['label'] or 'unlabeled'}|{item['hash']}"
                loc = f"{f['file']}:{item['line']} {item['text'][:60]}"
            elif kind == "inline_math":
                k = item["text"]
                loc = f"{f['file']}:{item['line']}"
            elif kind == "refs":
                k = item["ref"]
                loc = f"{f['file']}:{item['line']}"
            elif kind == "images":
                k = item["path"]
                loc = f"{f['file']}:{item['line']}"
            else:
                k = item["title"]
                loc = f"{f['file']}:{item['line']}"
            c[k] += 1
            where.setdefault(k, []).append(loc)
    return c, where


def is_soft_new_number(k: str) -> bool:
    if "␣" in k or "." in k or "e" in k.lower():
        return False
    try:
        return 0 <= int(k) <= 20
    except ValueError:
        return False


def diff(old: dict, new: dict) -> tuple[list[tuple[str, str, str]], dict]:
    out: list[tuple[str, str, str]] = []  # (level, rule, msg)
    stats = {}
    for kind, label in [("numbers", "数字"), ("display_math", "展示公式"), ("inline_math", "行内公式"),
                        ("refs", "交叉引用"), ("images", "图片"), ("headings", "标题")]:
        co, wo = bag(old["files"], kind)
        cn, wn = bag(new["files"], kind)
        lost = co - cn
        added = cn - co
        stats[kind] = {"old": sum(co.values()), "new": sum(cn.values()), "lost": sum(lost.values()), "added": sum(added.values())}
        for k, c in sorted(lost.items()):
            lvl = "INFO" if kind == "headings" else "FAIL"
            out.append((lvl, f"{kind}_lost", f"{label}丢失 ×{c}：`{k}` ← 原稿 {'; '.join(wo[k][:3])}"))
        for k, c in sorted(added.items()):
            if kind == "headings":
                lvl = "INFO"
            elif kind == "refs":
                lvl = "WARN"
            elif kind == "numbers" and is_soft_new_number(k):
                lvl = "WARN"
            else:
                lvl = "FAIL"
            out.append((lvl, f"{kind}_added", f"{label}新增 ×{c}：`{k}` → 改稿 {'; '.join(wn[k][:3])}"))
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    out.sort(key=lambda t: (order[t[0]], t[1], t[2]))
    return out, stats


def render(out: list[tuple[str, str, str]], stats: dict, a_old: str, a_new: str) -> str:
    n = Counter(t[0] for t in out)
    L = [f"# FACT_DIFF — {a_old} → {a_new}", "",
         f"FAIL {n['FAIL']}，WARN {n['WARN']}，INFO {n['INFO']}", "",
         "| 事实类型 | 原稿 | 改稿 | 丢失 | 新增 |", "| --- | ---: | ---: | ---: | ---: |"]
    for k, s in stats.items():
        L.append(f"| {k} | {s['old']} | {s['new']} | {s['lost']} | {s['added']} |")
    L.append("")
    for level in ("FAIL", "WARN", "INFO"):
        items = [t for t in out if t[0] == level]
        if not items:
            continue
        L += [f"## {level}（{len(items)}）", ""]
        L += [f"- [{rule}] {msg}" for _, rule, msg in items[:300]]
        if len(items) > 300:
            L.append(f"- …另 {len(items) - 300} 条")
        L.append("")
    if not n["FAIL"]:
        L.append("结论：数字、公式、图表引用零漂移。")
    else:
        L.append("结论：存在事实漂移，改稿不得交付；逐条回到原稿核对，数字/公式必须与原稿一致，若确需改数请回 draft 重跑代码。")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--out", default=None)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out, stats = diff(extract(Path(a.old)), extract(Path(a.new)))
    report = render(out, stats, a.old, a.new)
    nf = sum(1 for t in out if t[0] == "FAIL")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(report, encoding="utf-8")
        print(f"[fact_diff] FAIL {nf}，WARN {sum(1 for t in out if t[0] == 'WARN')} → {a.out}")
    else:
        print(report)
    return 1 if (a.strict and nf) else 0


if __name__ == "__main__":
    raise SystemExit(main())
