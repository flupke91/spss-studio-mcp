# Release Notes — v1.0.0

> 状态：发布准备就绪 ｜ 由 `docs/technical_report.md` 与验证记录汇总

## 概述

spss-studio-mcp 是面向 IBM SPSS Statistics 的 MCP 服务器，为 Codex / Claude /
Cursor 提供"统计引擎 + 制图工厂 + 结构化消费 + 安全护栏"四合一能力。全部功能
已在 SPSS Statistics 32.0.0 真机验收。

## 亮点

- **论文级出图**：11 类 `spss_chart_*` 工具，PNG/TIFF/EMF @300 dpi（1950×1500），路径回传可直接投稿。
- **深度结果解析**：OMS 文本 → Markdown + JSON 表格 + 16 类分析统计摘要（t/F/r/B/Wald/α/χ²/p/效应量）。
- **37+ 工具真机验收**：26 个分析方法 + 11 个补充工具全部通过；修复 8 处 SPSS 32 语法兼容问题。
- **boxplot 全格式修复**：0.3.1 起箱线图改用 `EXAMINE /PLOT BOXPLOT` 模板，解决
  GGRAPH schema 在 SPSS 32 的 `outlier was found inside fences` 报错与 EMF 0 字节问题。
- **中介/调节**：`spss_mediation`（Baron & Kenny + Sobel）、`spss_moderation`（中心化交互回归）。
- **安全执行**：危险命令拦截、数据路径白名单、`dry_run`、JSONL 审计日志。
- **统一返回**：`{markdown, json, files, warnings}`，Agent 可直接编程消费。

## 关键兼容性说明

- SPSS 32 已移除 `OMS FORMAT=IMAGE` / `IMAGEROOT`；项目改用 HTML 内嵌 PNG +
  DOCX 内嵌 EMF 双链路（详见 `docs/poc_chart_pipeline.md`）。
- 箱线图 0.3.1 起使用 `EXAMINE` 传统图模板，PNG / TIFF / EMF 三格式均真机验证通过。

## 资源

- 技术报告：`docs/technical_report.md`
- 使用教程：`docs/tutorial.md`
- 方法验证：`docs/method_verification.md`
- 生态收录：`docs/ecosystem.md`

## 安装

```powershell
pip install spss-studio-mcp
spss-studio-mcp status
```

## 版本

- 当前版本：`0.3.1`（0.3.0 完成 P3/P4 功能，0.3.1 修复 boxplot 全格式导出）

## 致谢

上游：`Exekiel179/SPSS-MCP`（MIT）。
