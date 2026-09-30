# 字段写法

```text
cases/<id>/
  meta.md
  prompt.md
  ideal-steps.md
  golden.md
  rubrics.md
  doubao-output.md
  rating.md
  attachments/
```

`meta.md` 必填：

```text
slot: p1-fengzhang
scene: 变电运维班组核对监管通报中的送电事件
primary_gap: 结果质量
capability: 待按页面下拉填写
difficulty: 中
author_role: 变电运维人员，依据附件做班组核对
author_on_scene: 否
source_kind: public_notice
source_url: https://...
source_fetched: 2026-09-30
status: SOURCE_VERIFIED_DRAFT
```

`status` 允许：`BLOCKED_NO_SOURCE`、`SOURCE_VERIFIED_DRAFT`、`READY_FOR_DOUBAO`、`RATED`、`LOCAL_PASS`。不要写 `APPROVED`。

`SOURCE_VERIFIED_DRAFT` 表示 Golden 的 `原文：「」` 已在附件中找到，豆包还没跑。这个状态不能交。

Golden 里要被核验的句子必须写成：

```text
原文：「6月24日，国网河南省电力公司500千伏丰彰Ⅱ线送电过程中」
```

引号内是附件连续子串，不改标点。附件没有的内容单独写「材料未提供，不能判断」，不要放进「」。

提示词四件套：谁用、交付列、禁止补数和下执行结论、附件编号。不写事件里的过错结论。

Rubrics 4 到 7 条，权重和 100。每条有 `fail:`，并写「本条 0 分」。
