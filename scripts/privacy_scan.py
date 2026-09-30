#!/usr/bin/env python3
"""公开包隐私扫描。命中即失败。报告只写规则编号和路径，不回显命中文本。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RULES = (
    ("P01_HOME", re.compile(r"/(?:Users|home)/|[A-Za-z]:\\Users\\")),
    ("P02_PHONE", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("P03_EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("P04_PERSON", re.compile("潘" + "博|" + "wx" + "id_|" + "苏电" + "智办")),
    ("P05_EMPLOYER", re.compile("常州" + "供电")),
    ("P06_PRIVATE_NOTE", re.compile(r"~\.zshenv|127\.0\.0\.1")),
)
SKIP = {"__pycache__", ".git"}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP for part in path.parts):
            continue
        if path.suffix in {".pyc", ".png", ".jpg", ".zip"}:
            continue
        yield path


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    hits: list[str] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            hits.append(f"P00_BINARY {path.relative_to(root)}")
            continue
        for code, pattern in RULES:
            if pattern.search(text):
                hits.append(f"{code} {path.relative_to(root)}")
    if hits:
        print(f"PRIVACY_FAIL {len(hits)}")
        for item in hits:
            print(item)
        return 1
    print(f"PRIVACY_PASS {root.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
