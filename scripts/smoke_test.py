"""smoke_test.py — 仓库自检：在 examples/demo-drug-decay 上跑 prose_lint / facts_extract / fact_diff。

用法：python scripts/smoke_test.py
检查：三个脚本能运行并产出报告；同一目录 fact_diff 自比对 0 FAIL；注入一处数字改动后 fact_diff 必须 FAIL。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / ".agents" / "skills" / "prose-lint" / "scripts"
DEMO = ROOT / "examples" / "demo-drug-decay" / "paper" / "sections"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run(*args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, *args]
    r = subprocess.run(cmd, cwd=str(ROOT), env=_env(), text=True, encoding="utf-8", errors="replace", capture_output=True)
    print(f"$ {' '.join(Path(a).name if os.sep in a else a for a in args)}\n  -> exit {r.returncode}: {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-200:]}")
    return r


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ok = True
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        r = run(str(S / "prose_lint.py"), str(DEMO), "--out", str(tmp / "PROSE_LINT.md"), "--json", str(tmp / "lint.json"))
        ok &= r.returncode == 0 and (tmp / "PROSE_LINT.md").exists()
        r = run(str(S / "facts_extract.py"), str(DEMO), "--out", str(tmp / "FACTS.json"))
        ok &= r.returncode == 0 and (tmp / "FACTS.json").exists()
        r = run(str(S / "fact_diff.py"), str(DEMO), str(DEMO), "--strict")
        ok &= r.returncode == 0
        mutated = tmp / "sections"
        shutil.copytree(DEMO, mutated)
        p = mutated / "05_problem1.md"
        t = p.read_text(encoding="utf-8")
        assert "0.0469" in t
        p.write_text(t.replace("0.0469", "0.0468", 1), encoding="utf-8")
        r = run(str(S / "fact_diff.py"), str(DEMO), str(mutated), "--strict", "--out", str(tmp / "FACT_DIFF.md"))
        ok &= r.returncode == 1 and "numbers_lost" in (tmp / "FACT_DIFF.md").read_text(encoding="utf-8")
    print("[smoke] " + ("OK" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
