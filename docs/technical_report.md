# SPSS Studio MCP：论文级图表导出、深度结果解析与安全执行的研究助手

> 技术报告 ｜ 2026-08-05 ｜ 实测环境：Windows + IBM SPSS Statistics 32.0.0

## 摘要

SPSS 是心理学、管理学与社会科学研究中事实上的标准统计软件，但现有 MCP
（Model Context Protocol）生态只实现了"把语法交给 SPSS、返回文本表格"的薄封装：
论文级图片需人工在 Viewer 导出、结果只能阅读不能结构化消费、LLM 生成的语法
缺乏安全护栏。本文报告 **SPSS Studio MCP**——一个面向 SPSS 的 MCP 服务器，
以四个互补层补齐缺口：（1）**论文级出图管线**，11 类图一键导出 PNG/TIFF/EMF
（300 dpi）；（2）**深度结果解析**，OMS 文本→Markdown+JSON 表格与 16 类分析的
统计摘要；（3）**方法真机验证**，37 个工具在真实 SPSS 上逐方法验收并修复
7+1 处版本兼容问题；（4）**安全执行层**，危险语句拦截、路径白名单、dry_run
与审计日志。全部能力在 SPSS 32 真机验证通过。

## 1 背景与问题

### 1.1 SPSS MCP 生态的四个缺口

对现有 SPSS MCP 项目（参考 `Exekiel179/SPSS-MCP`，MIT）的源码复核显示：

| 缺口 | 现状 |
|------|------|
| G1 论文级出图缺失 | 仅 `OMS FORMAT=SPV` 把图表锁进二进制 .spv，全库无 OMS IMAGE/GGRAPH |
| G2 结果解析浅 | 只有文本→Markdown 表格，无 JSON、无统计摘要 |
| G3 方法代码正确性未验证 | 37 工具已实现但从未真机样例验证 |
| G4 安全语法层薄弱 | 只有语法校验，无白名单/拦截/dry_run/审计 |

### 1.2 动机

对无多模态能力的文本 LLM，数值统计可用 Python 完成，但**论文级图片无法自行
闭环**——SPSS 的确定性渲染（语法给定即出图、期刊级字号/DPI）是唯一不可替代
价值。本项目把"统计引擎 + 制图工厂"做成可交付物，并让结果可被机器消费。

## 2 系统设计

```
客户端 (Codex / Claude / Cursor)
        │  MCP stdio
        ▼
工具层   37+ 分析方法 + 11 图表 + 中介/调节 + 结构化结果
        ▼
引擎层   SPSS Python3 XD API 持久会话 (spss.StartSPSS / spss.Submit)
        ▼
输出层   OMS TEXT (表格) / HTML (PNG) / DOCX (EMF) + 安全闸 + 审计
```

- **持久引擎**：单个 SPSS Python3 子进程常驻，避免每次 15–20 秒启动开销。
- **模板化语法**：所有出图与分析走预定义模板（Pydantic 校验），LLM 不能自由生成 GPL/语法。
- **统一返回**：`{markdown, json, files, warnings}`。

## 3 关键实现与版本兼容性发现

### 3.1 SPSS 32 移除 `OMS FORMAT=IMAGE`（重要发现）

规划阶段依赖旧版 `OMS /DESTINATION FORMAT=IMAGE IMAGEROOT=...`，在 SPSS 32
真机被拒绝（`Unknown keyword or subcommand: IMAGE`）。实测矩阵（节选）：

| 变体 | SPSS 32 结果 |
|------|-------------|
| `FORMAT=IMAGE ... IMAGEROOT=...` | ✗ 不支持 |
| `FORMAT=HTML IMAGES=YES OUTFILE=...` | ✓ 图表以 base64 PNG 内嵌 |
| `FORMAT=DOC OUTFILE=...` | ✓ 生成 .docx，图表为矢量 EMF |
| `FORMAT=HTML IMAGEWIDTH/HEIGHT` | ✗ 致命错误 |

**落定方案**：PNG/TIFF 走 HTML→base64 提取→Pillow 后处理（1950×1500 @300dpi，
TIFF 为 LZW）；EMF 走 DOCX→zip 提取矢量 EMF。boxplot 的 EMF 为 SPSS 32 自身
0 字节 bug（PNG/TIFF 正常），已在 0.3.1 通过改用 `EXAMINE /PLOT BOXPLOT`
传统图模板根治（见 4 节验证）。

### 3.2 结果解析：从文本到统计摘要

`result_parser.py` 用行扫描状态机切分 SPSS 表块（处理 Notes 跳过、多行表头、
单空格粘连单元格、`(a)` 脚注、`.000`→`<.001`），并对 16 类分析抽取关键统计量：

t 检验（独立/配对）、单因素/多因素 ANOVA（含 Levene、偏 η²）、相关、线性/
Logistic/序数回归、频数、卡方、Cronbach's α、非参数（M-W/Wilcoxon/K-W）、
Shapiro-Wilk 正态性、因子分析（KMO/Bartlett/累计方差）、描述统计。

### 3.3 方法真机验证驱动修复

26 个分析方法用例在真实 SPSS 32 上验收，暴露并修复 8 处模板问题：
`TAILS(2)→TWOTAIL`、`MEAN` 参数逗号、TWOSTEP 子命令 `=` 与距离取值、
判别/ MANOVA 因子值范围、废弃 METHOD 子命令、PLUM `TEST=PARALLEL`、
GENLINMIXED subject 名义化、GENLIN `DISTRIBUTION` 并入 MODEL 等。

### 3.4 安全层

`security.py`：危险命令（HOST/ERASE/DELETE FILE 等）行首匹配拦截、数据文件
路径白名单（`SPSS_ALLOWED_DIRS`）、`dry_run`、JSONL 审计日志，统一接入
`run_syntax` 覆盖所有工具。

## 4 真机验证结果

| 类别 | 结果 |
|------|------|
| 分析方法 | 26/26 通过 |
| 补充工具（文件/状态/语法/结构化/genlin） | 11/11 通过 |
| 图表 × PNG/EMF/TIFF | 11 类全格式通过（0.3.1 修复 boxplot EMF：`EXAMINE` 模板，EMF 约 19 KB 非零） |
| 中介/调节 | 真机通过（Sobel z=6.75, p<.001；交互 p=.639） |
| 单元测试 | 109 passed（含真机 reproduction manifest，自包含样例数据） |

样例数据与归档图：`examples/`（问卷/实验/生存/中介/纵向）。

## 5 讨论与局限

- HTML 内嵌 PNG 固定约 800×500，300 dpi 出图为放大+重标 DPI；严格的矢量高分辨率
  位图可走 EMF+GDI+ 渲染（已验证，Windows-only，留作后续）。
- 中介/调节用三步回归实现并附 Sobel；严谨报告建议 PROCESS 的 Bootstrap 复核。
- 生态收录（LobeHub/PulseMCP）与正式 Release 为发布账号操作，见 `docs/ecosystem.md`。

## 6 结论

SPSS Studio MCP 证明了"统计引擎 + 制图工厂 + 结构化消费 + 安全护栏"的组合在
真实 SPSS 32 上可落地：37 工具全量真机验收、论文级图片自动化、16 类结果摘要、
执行安全审计。项目文档齐备（出图 PoC、结果解析、方法验证、安全），为心理/管理
/社科研究的 agent 工作流提供了可复用的 MCP 服务。

## 附录：复现

```powershell
pip install -e ".[dev]"
python scripts/make_sample_data.py
python scripts/method_verification.py    # 26 方法
python scripts/tool_verification.py      # 11 工具
python -m spss_mcp.poc_chart --format PNG|EMF|TIFF
python scripts/archive_sample_charts.py  # 归档 11 张样例图
```
