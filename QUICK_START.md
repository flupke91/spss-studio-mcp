# spss-studio-mcp 快速开始

> 3 步完成部署，5 分钟开始使用（已在 IBM SPSS Statistics 32 真机验证）

---

## 第 1 步：安装

```powershell
cd D:\opencode\spss-studio-mcp
pip install -e ".[dev]"
spss-studio-mcp status   # 应显示 SPSS batch: OK
```

## 第 2 步：配置 MCP 客户端

```powershell
spss-studio-mcp configure-codex     # Codex（~/.codex/config.toml）
spss-studio-mcp configure-claude    # Claude Code（~/.claude.json）
spss-studio-mcp setup-info          # 手动配置片段
```

## 第 3 步：使用

### 统计分析

直接向客户端描述需求，例如：

- `对 examples/data/survey_study.sav 做描述统计和可靠性分析`
- `用 examples/data/experiment_study.sav 做独立样本 t 检验（group 分组，posttest）`
- `对 examples/data/mediation_study.sav 做中介分析：autonomy → satisfaction → performance`

### 论文级出图

- `画 examples/data/survey_study.sav 学习投入总分的直方图（带正态密度），PNG 300dpi`
- `用 examples/data/survival_study.sav 画按 treatment 分组的 KM 生存曲线`
- `用 examples/data/experiment_study.sav 画后测成绩按组别的箱线图`

所有图表工具都会返回 1950×1500 @300dpi 的文件路径，可直接用于投稿。

### 结构化结果

- 调用 `spss_structured_result` 获得 `{markdown, json, files, warnings}` 统一结构；
  统计摘要（t/F/r/B/p 等）会自动出现在各分析工具的返回末尾（`### 统计摘要`）。

## 安全

- 危险命令（HOST / ERASE / DELETE FILE 等）会被拦截；
- 数据文件需位于 `examples/`、系统临时目录或 `SPSS_ALLOWED_DIRS` 指定目录；
- `spss_run_syntax(..., dry_run=True)` 可先校验不执行；
- 审计日志默认写入 `logs/audit.jsonl`（可用 `SPSS_AUDIT_LOG` 改路径）。

## 样例与文档

- 样例数据与归档图：`examples/`
- 文档：`docs/`（出图管线 PoC、结果解析、方法验证记录）
- Agent 完整教程：[`docs/tutorial.md`](docs/tutorial.md)（可直接复制安装和分析 Prompt）

## 常见问题

- **启动慢**：首次引擎启动约 15–20 秒，之后为常驻会话。
- **提示未授权**：确保 SPSS 试用/正式授权可用，勿同时开多个 SPSS 会话。
- **数据文件被拒**：把文件放入 `examples/data/`，或用 `SPSS_ALLOWED_DIRS` 声明目录。
