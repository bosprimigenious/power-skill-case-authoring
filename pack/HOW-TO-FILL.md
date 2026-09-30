# 电力题怎么填到能交

当前可继续的只有 `p1-fengzhang` 和 `p2-js-202412`。两题来源已核验，还不能交。

1. 打开豆包，选工作任务模式，模型 2.1 Pro。
2. 只上传该题 `attachments/` 里的文件，提示词用 `prompt.md` 去掉说明后的正文。这两题的 `prompt.md` 已经是正文。
3. 全文贴进 `doubao-output.md`。第一行写 `model: 豆包工作任务模式 2.1Pro`。
4. 对照 `rubrics.md` 打分。引用必须是输出里的原句。`skill_rule` 写成一条电力核对规则，例如「通报未写出的变电站名称不得补全」。
5. 你确认评级是自己打的之后，把 `would_submit` 改成 `是`，`status` 改成 `RATED`。
6. 再跑：

在仓库根目录执行：

```bash
python3 scripts/audit_pack.py pack --strict
python3 scripts/privacy_scan.py .
```

strict 仍会看未改状态的另一题。只提交已评级的题时，把未跑的题移出 `cases/` 再跑，或等两题都评级。不要改脚本让占位题通过。

下一道电力题不要再写绩效。有票面、缺陷单或验收清单，放到新槽 p3、p4、p5。没有原件就保持不建目录。
