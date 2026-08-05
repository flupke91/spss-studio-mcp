# 生态收录与 Release v1.0 准备

> 2026-08-05 ｜ 提交类操作需发布账号，本文件给出可直接使用的条目与说明。

## 1. 项目速览（用于收录/发布）

- **名称**：spss-studio-mcp
- **一句话**：让 SPSS 成为 Agent 的"统计引擎 + 制图工厂"：论文级图片、深度结果解析、方法真机验证、安全执行。
- **类别**：data-analysis / statistics / mcp-server
- **标签**：`spss` `statistics` `mcp` `chart` `result-parsing` `psychology` `social-science`
- **核心能力（来自技术报告）**：
  - 11 类论文级图表（PNG/TIFF/EMF，300 dpi）
  - 16 类分析统计摘要（t/F/r/B/Wald/p/效应量）
  - 37+ 工具全量真机验收（SPSS 32）
  - 中介/调节工具（Baron & Kenny + Sobel）
  - 安全层（拦截/白名单/dry_run/审计）

## 2. LobeHub 收录条目

平台：LobeHub（Lobe Chat MCP/插件市场）。提交方式：通常为 GitHub 仓库提交
描述文件或 PR。可复制以下条目：

- 仓库：https://github.com/flupke91/spss-studio-mcp
- LobeHub 插件市场提交入口：https://github.com/lobehub/lobe-chat-plugins
  （创建 `plugins/<plugin-name>/` 目录，含 `plugin.json` + `README.md`）

```yaml
# lobehub 条目示例
name: spss-studio-mcp
description: >-
  SPSS Studio MCP：论文级图表导出（11 类图 PNG/TIFF/EMF @300dpi）、深度结果
  解析（Markdown+JSON+统计摘要）、37+ 方法真机验证、中介/调节分析与安全执行
  （危险拦截/白名单/dry_run/审计）。适用于心理学/管理学/社科研究。
category: data-analysis
tags: [spss, statistics, chart, mcp]
```

## 3. PulseMCP 收录条目

平台：PulseMCP（MCP 服务器目录）。提交方式：站点表单或 GitHub PR。
建议填写：

- 提交入口：https://www.pulsemcp.com/submit
- 仓库：https://github.com/flupke91/spss-studio-mcp

- **Name**: spss-studio-mcp
- **Short description**: Paper-ready charts, deep result parsing and safe execution for IBM SPSS Statistics via MCP.
- **Long description**: 引用 `README.md` 的功能清单与 `docs/technical_report.md` 摘要。
- **Transport**: stdio
- **Auth**: none（本地 SPSS 授权）
- **OS**: Windows

## 4. GitHub Release v1.0 草稿

见 `docs/release_notes_v1.0.md`（可直接粘贴到 Release 页面）。

## 5. 提交前检查清单

- [x] 功能与验证：37 工具真机验收（26 方法 + 11 工具）、11 类图 × PNG/EMF/TIFF
- [x] boxplot 全格式修复（0.3.1）：EMF 非零（约 19 KB），PNG/TIFF 正常
- [x] 文档：README / QUICK_START / docs（教程、技术报告、出图、解析、验证、安全）
- [x] 安全：拦截/白名单/dry_run/审计 + `docs/security.md`
- [x] CI：`.github/workflows/ci.yml`（lint + pytest）
- [x] 许可证：MIT（含上游说明）
- [x] 样例图：`examples/charts/*.png` 已用 0.3.1 模板重新归档（11 张，含修复后的 boxplot）
- [ ] 发布账号操作：创建 GitHub release、提交 LobeHub/PulseMCP 条目
- [ ] （建议）GitHub 仓库公开前检查：无敏感路径、无本地日志入库（`logs/` 已 gitignore）

## 7. GitHub 发布步骤（发布账号操作）

- [x] 创建公开仓库 `flupke91/spss-studio-mcp` 并推送 `master`（2026-08-05）；
- [x] 打 tag `v1.0.0` 并创建 Release（正文 = `docs/release_notes_v1.0.md`）；
- [ ] 提交 LobeHub 条目（lobe-chat-plugins PR）；
- [ ] 提交 PulseMCP 条目（pulsemcp.com/submit 表单）。

## 6. 对外材料（②的成果，可直接引用）

- 技术报告（论文稿）：`docs/technical_report.md`
- 使用教程：`docs/tutorial.md`
- 样例图：`examples/charts/*.png`（可作 README/收录页截图）
- 验证记录：`docs/method_verification.md`、`docs/tool_verification.json`
