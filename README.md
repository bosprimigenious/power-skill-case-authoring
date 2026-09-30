# power-skill-case-authoring

为电力生产运行场景编写豆包工作任务模式评测案例：先保存可核验来源，再写提示词、理想步骤、参考答案和评分条。参考答案里的事实句必须是附件中的连续原文。

本仓库是出题方法，不是已经通过平台质检的专家提交包。`pack/` 里的两题来源已核对，模型尚未实跑，作者尚未评级，状态是 `SOURCE_VERIFIED_DRAFT`。

## 范围

只覆盖变电运维、两票、缺陷、验收、通报中已经写明的电气保护，以及电力安全监管通报的事实核对。

不覆盖绩效、薪酬、人才评价、新闻体例，也不把公开通报写成出题人亲历。

## 使用

```bash
python3 scripts/audit_pack.py pack
python3 scripts/privacy_scan.py .
python3 scripts/test_audit_pack.py
```

`audit_pack.py` 返回非 0 表示还不能当提交包。`PRIVACY_PASS` 只表示扫描规则没有命中，不代替人工确认内部单据是否可公开。

## 示例来源

两份附件摘自国家能源局及江苏监管办公开页面，抓取日 2026-09-30。页面链接和删除范围见 `references/source-ledger.md`。通报正文的著作权归原发布机关，本仓库只保存评测所需摘录。

## 许可证

方法、脚本和自写题面使用 MIT License，见 `LICENSE`。政府公开文本的权利不因本仓库许可证而改变，见 `NOTICE`。
