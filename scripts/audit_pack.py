#!/usr/bin/env python3
"""提交前自检。PASS 只表示本地包满足字段契约，不是平台质检通过。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED = (
    "meta.md",
    "prompt.md",
    "ideal-steps.md",
    "golden.md",
    "rubrics.md",
    "doubao-output.md",
    "rating.md",
)
GAPS = ("任务理解", "信息组织", "执行路径", "输出格式", "结果质量")
STATUSES = {
    "DRAFT",
    "BLOCKED_NO_SOURCE",
    "SOURCE_VERIFIED_DRAFT",
    "READY_FOR_DOUBAO",
    "RATED",
    "LOCAL_PASS",
}
SUBMITTABLE = {"RATED", "LOCAL_PASS"}
OFF_TOPIC = ("绩效经理人", "业绩考核指标", "薪酬兑现", "技能等级评价", "人才评价技术")
PHONE = re.compile(r"1[3-9]\d{9}")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PASS_CLAIM = ("平台质检通过", "验收通过")
PASS_NEG = ("不是", "并非", "不要", "不能", "不可", "未", "没有", "尚未")
VAGUE = ("逻辑清晰", "较为专业", "深入分析", "格式规范", "内容完整", "语言流畅")
ANSWER_LEAK = ("正确答案", "标准答案", "应得出", "冲突共有", "共有以下冲突")
EXEC_ORDER = ("可以操作", "同意停电", "定值改为", "按此令执行")


def claims_passed(text: str) -> bool:
    for line in text.splitlines():
        if not any(token in line for token in PASS_CLAIM):
            continue
        if any(neg in line for neg in PASS_NEG):
            continue
        return True
    return False


def read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def field(text: str, key: str) -> str:
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def quotes_in(text: str) -> list[str]:
    return re.findall(r"原文：「([^」]+)」", text)


def quotes_fail(golden: str, files: list[Path]) -> list[str]:
    quotes = quotes_in(golden)
    if not quotes:
        return ["Golden 没有原文：「」锚"]
    blob = "\n".join(p.read_text(encoding="utf-8") for p in files)
    missing = [q for q in quotes if q not in blob]
    return [f"原文锚不在附件中：{q[:40]}" for q in missing]


def attachments(case: Path) -> list[Path]:
    folder = case / "attachments"
    if not folder.is_dir():
        return []
    return [p for p in folder.rglob("*") if p.is_file() and not p.name.startswith(".")]


def audit_case(case: Path, strict: bool) -> list[str]:
    fails: list[str] = []
    name = case.name
    texts = {fn: read(case / fn) for fn in REQUIRED}
    missing = [fn for fn, body in texts.items() if not body.strip()]
    if missing:
        fails.append(f"{name}: 缺文件或为空 {', '.join(missing)}")
        if "meta.md" in missing:
            return fails

    meta = texts["meta.md"]
    status = field(meta, "status")
    gap = field(meta, "primary_gap")
    slot = field(meta, "slot") or name
    if status not in STATUSES:
        fails.append(f"{name}: status 非法 {status or '空'}")
    if gap not in GAPS:
        fails.append(f"{name}: primary_gap 必须是五缺口之一，当前为 {gap or '空'}")
    if slot != name:
        fails.append(f"{name}: 目录名与 meta.slot 不一致 ({slot})")

    scene = field(meta, "scene") + texts["prompt.md"]
    if any(token in scene for token in OFF_TOPIC):
        fails.append(f"{name}: 场景不是电力生产，命中退出范围")
    if field(meta, "author_on_scene") == "否":
        for token in ("我当时操作", "我在现场", "本人操作"):
            if token in texts["prompt.md"] or token in texts["golden.md"]:
                fails.append(f"{name}: 公开材料题写成了亲历「{token}」")

    if status == "BLOCKED_NO_SOURCE":
        return fails

    files = attachments(case)
    if not files:
        fails.append(f"{name}: attachments/ 没有原件，不能当真实输入")
    elif texts["golden.md"].strip():
        for item in quotes_fail(texts["golden.md"], files):
            fails.append(f"{name}: {item}")

    prompt = texts["prompt.md"]
    if "附件" not in prompt:
        fails.append(f"{name}: 提示词没有引用附件")
    for token in ANSWER_LEAK:
        if token in prompt:
            fails.append(f"{name}: 提示词泄露答案口径「{token}」")
    if not any(w in prompt for w in ("不要", "不得", "禁止")):
        fails.append(f"{name}: 提示词没有禁止事项")

    steps = texts["ideal-steps.md"]
    if "附件" not in steps:
        fails.append(f"{name}: Ideal Steps 没有指向附件")
    if len(re.findall(r"^##\s+", steps, re.M)) < 5 and len(re.findall(r"^\d+\.", steps, re.M)) < 5:
        fails.append(f"{name}: Ideal Steps 少于 5 步")

    golden = texts["golden.md"]
    if "不能判断" not in golden and "材料未提供" not in golden and "待核实" not in golden:
        fails.append(f"{name}: Golden 没有「不能判断/待核实」格，像是把缺数补完了")
    for token in EXEC_ORDER:
        if token in golden:
            fails.append(f"{name}: Golden 含执行口吻「{token}」")

    rubrics = texts["rubrics.md"]
    weights = [int(n) for n in re.findall(r"^  weight:\s*(\d+)\s*$", rubrics, re.M)]
    if not weights:
        weights = [int(n) for n in re.findall(r"weight:\s*(\d+)", rubrics)]
    if sum(weights) != 100:
        fails.append(f"{name}: rubrics 权重和为 {sum(weights)}，应为 100")
    if not any(g in rubrics for g in GAPS):
        fails.append(f"{name}: rubrics 没有点明缺口")
    if any(v in rubrics and "本条" not in rubrics.split(v, 1)[-1][:80] for v in VAGUE):
        fails.append(f"{name}: rubrics 含无法打分的空话")
    if gap and gap not in rubrics:
        fails.append(f"{name}: 主缺口 {gap} 没有写进 rubrics")

    output = texts["doubao-output.md"]
    if "2.1" not in output:
        fails.append(f"{name}: 豆包输出未标明 2.1 Pro")
    if "工作任务" not in output:
        fails.append(f"{name}: 豆包输出未标明工作任务模式")
    if strict and len(output) < 400:
        fails.append(f"{name}: 豆包输出过短，不像一次工作任务交付")
    if strict and golden and output and _same_body(golden, output):
        fails.append(f"{name}: 豆包输出与 Golden 正文相同，疑似回贴标准答案")

    rating = texts["rating.md"]
    if "primary_gap_hit" not in rating or "skill_rule" not in rating:
        fails.append(f"{name}: rating 缺 primary_gap_hit 或 skill_rule")
    quotes = re.findall(r'^  - "(.+)"\s*$', rating, re.M)
    if strict and not quotes:
        fails.append(f"{name}: rating 没有引用模型原句")
    elif quotes and output:
        for q in quotes:
            if q not in output:
                fails.append(f"{name}: 引用不在豆包原文中：{q[:24]}")

    blob = "\n".join(texts.values())
    if PHONE.search(blob) or EMAIL.search(blob):
        fails.append(f"{name}: 正文含电话或邮箱")
    if claims_passed(blob):
        fails.append(f"{name}: 把平台通过写进了案例包")
    return fails


def _same_body(golden: str, output: str) -> bool:
    def norm(s: str) -> str:
        s = re.sub(r"^model:.*$", "", s, flags=re.M)
        s = re.sub(r"〔附件[^〕]*〕", "", s)
        return re.sub(r"\s+", "", s)

    g, o = norm(golden), norm(output)
    return len(g) > 80 and g == o


def main() -> int:
    parser = argparse.ArgumentParser(description="审计电力 Skill 案例包")
    parser.add_argument("pack", type=Path)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="提交前使用：豆包输出和引用必须是实跑",
    )
    args = parser.parse_args()
    pack = args.pack
    cases = pack / "cases"
    if not cases.is_dir():
        print("FAIL 缺少 cases/")
        return 1

    fails: list[str] = []
    seen: dict[str, str] = {}
    n = 0
    submittable = 0
    blocked = 0
    sourced = 0
    for case in sorted(p for p in cases.iterdir() if p.is_dir()):
        n += 1
        fails.extend(audit_case(case, args.strict))
        status = field(read(case / "meta.md"), "status")
        if status == "BLOCKED_NO_SOURCE":
            blocked += 1
        elif status == "SOURCE_VERIFIED_DRAFT":
            sourced += 1
        elif status in SUBMITTABLE and attachments(case):
            if "待实跑" in read(case / "doubao-output.md") or "未评" in read(case / "rating.md"):
                fails.append(f"{case.name}: 状态是 {status}，但豆包输出或评级仍是占位")
            else:
                submittable += 1
        slot = field(read(case / "meta.md"), "slot")
        if slot:
            if slot in seen:
                fails.append(f"槽位重复 {slot}: {seen[slot]} 与 {case.name}")
            seen[slot] = case.name
    if n == 0:
        fails.append("cases/ 下没有题目")
    if n > 8:
        fails.append(f"当前上限 8 题，包内 {n} 题")
    if submittable == 0:
        fails.append(
            f"可提交 0 题，来源已核验未实跑 {sourced} 题，阻塞 {blocked} 题。不能当提交包。"
        )

    status = read(pack / "STATUS.md")
    if claims_passed(status):
        fails.append("STATUS.md 声称平台质检通过")

    if fails:
        print(f"NOT READY  {len(fails)} 项")
        for item in fails:
            print(f"- {item}")
        return 1
    print(f"LOCAL_STRUCTURE_PASS  {n} 题  strict={args.strict}")
    print("这不是平台质检通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
