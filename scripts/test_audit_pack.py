#!/usr/bin/env python3
"""自检脚本的反作弊：空包、泄露答案、权重不对必须 FAIL；一份最小合规格草稿在非 strict 下 PASS。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_pack.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(pack: Path, strict: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(AUDIT), str(pack)]
    if strict:
        cmd.append("--strict")
    return subprocess.run(cmd, capture_output=True, text=True)


def good_case(case: Path, output: str, rating_quote: str) -> None:
    write(case / "meta.md", "slot: s4-kpi\nprimary_gap: 信息组织\nstatus: RATED\n")
    write(
        case / "prompt.md",
        "请只根据附件1和附件2做口径冲突清单。不要补数，不得把建议写成已批准。\n",
    )
    write(
        case / "ideal-steps.md",
        "\n".join(
            [
                "1. 读附件1指标名称列。",
                "2. 读附件2统计口列。",
                "3. 以指标名称对齐。",
                "4. 对不上则写不能判断。",
                "5. 交付前核对每条都有附件锚。",
            ]
        ),
    )
    write(case / "golden.md", "原文：「指标A 统计口：公司口径」\n材料未提供计算公式，不能判断得分。\n")
    write(
        case / "rubrics.md",
        "\n".join(
            [
                "- id: R1",
                "  weight: 40",
                "  gap: 信息组织",
                "  fail: 合并未声明对应的指标，本条 0 分",
                "- id: R2",
                "  weight: 30",
                "  fail: 缺附件锚，本条 0 分",
                "- id: R3",
                "  weight: 20",
                "  fail: 写成散文，本条 0 分",
                "- id: R4",
                "  weight: 10",
                "  fail: 出现已批准，本条 0 分",
            ]
        ),
    )
    write(case / "attachments" / "01-指标.md", "指标A 统计口：公司口径\n")
    write(case / "doubao-output.md", output)
    write(
        case / "rating.md",
        "\n".join(
            [
                "score: 40/100",
                "primary_gap_hit: 是",
                f'quotes:\n  - "{rating_quote}"',
                "skill_rule: 指标名称不能唯一对齐时不得合并。",
                "would_submit: 否",
            ]
        ),
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp)
        write(pack / "STATUS.md", "本地结构检查用。不是平台质检通过。\n")
        write(pack / "cases" / ".keep", "")
        empty = run(pack)
        assert empty.returncode == 1, empty.stdout
        assert "没有题目" in empty.stdout

        case = pack / "cases" / "s4-kpi"
        good_case(
            case,
            "model: 豆包工作任务模式 2.1Pro\n日期: 2026-09-30\n"
            + ("已将指标A与指标A-1视为同一指标并给出得分。\n" * 8),
            "已将指标A与指标A-1视为同一指标并给出得分。",
        )
        loose = run(pack, strict=False)
        assert loose.returncode == 0, loose.stdout + loose.stderr

        write(case / "prompt.md", "正确答案是指标A冲突。不要补数。附件1见下。\n")
        leaked = run(pack)
        assert leaked.returncode == 1 and "泄露" in leaked.stdout, leaked.stdout

        good_case(
            case,
            "model: 豆包工作任务模式 2.1Pro\n太短\n",
            "不在原文",
        )
        strict = run(pack, strict=True)
        assert strict.returncode == 1, strict.stdout
        assert "过短" in strict.stdout
        assert "引用不在豆包原文" in strict.stdout

    print("audit_pack tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
