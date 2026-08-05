# P1 PoC：GGRAPH → 图表 → PNG 全链路真机验证

> 验证日期：2026-08-04
> 环境：Windows + IBM SPSS Statistics **32.0.0**（`C:\Program Files\IBM\SPSS Statistics\stats.exe`）
> 结论：**SPSS 32 已移除 `OMS FORMAT=IMAGE` / `IMAGEROOT`**，出图方案改为「HTML 内嵌 base64 PNG 提取」+「DOCX 内嵌矢量 EMF 提取」

---

## 1. 背景

P1 的第一里程碑是跑通「GGRAPH → OMS IMAGE → PNG」全链路，并记录当前 SPSS 版本的真实行为。
原设计依赖 `OMS /DESTINATION FORMAT=IMAGE IMAGEROOT=...`（参考上游代码与旧版 IBM 文档），
在 SPSS 32 上被拒绝。

## 2. 真机验证矩阵（SPSS 32.0.0）

| # | 变体 | 结果 |
|---|------|------|
| 1 | `FORMAT=IMAGE IMAGEFORMAT=PNG IMAGEROOT=...` | ✗ `Unknown keyword or subcommand: IMAGE` |
| 2 | `FORMAT=HTML IMAGES=YES IMAGEFORMAT=PNG IMAGEROOT=...` | ✗ `IMAGEROOT` 不被识别 |
| 3 | `FORMAT=HTML IMAGES=YES IMAGEFORMAT=PNG OUTFILE=...` | ✓ 生成 HTML，图表以 base64 PNG 内嵌 |
| 4 | `FORMAT=HTML OUTFILE=...`（最小变体） | ✓ 同上（仍内嵌 PNG） |
| 5 | `FORMAT=HTML IMAGES=YES IMAGEFORMAT=TIFF/EMF` | ✓ 语法接受，但**仍输出 PNG**（HTML 忽略 IMAGEFORMAT） |
| 6 | `FORMAT=HTML ... IMAGEWIDTH=1950 IMAGEHEIGHT=1500` | ✗ 致命错误（HTML 不接受尺寸关键字） |
| 7 | `FORMAT=DOC OUTFILE=...`（无扩展名） | ✓ 生成 `xxx.docx`（zip），图表为 `word/media/imageN.emf`（矢量） |
| 8 | `FORMAT=DOC OUTFILE=xxx.doc` | ✓ 生成 RTF `.doc`，图表为 `\pict\pngblip` 内嵌 PNG |
| 9 | 同一 OMS 块内多个 GGRAPH | ✓ 每个图表一个 data URI / 一个 EMF 成员，顺序提取 |
| 10 | **boxplot EMF 导出** | ✗→✓ 原 GGRAPH `ELEMENT: schema` 方案 DOCX 中 `imageN.emf` 为 **0 字节**；0.3.1 起模板改用 `EXAMINE /PLOT BOXPLOT` 传统图，EMF 真机验证非零（约 19 KB），PNG/TIFF 亦正常 |

### 关键事实

- **命名规则**：`OUTFILE` 原样使用（不加序号、不自动加扩展名）；不存在 `IMAGEROOT` 概念。
- **尺寸**：HTML 内嵌 PNG 为 Viewer 默认尺寸 ~799×499 px，无 DPI 元数据；
  DOCX 内 EMF 为 800×500 视框的矢量图，可任意分辨率栅格化。
- **多图表**：HTML 中每个 `<img>` 一个 `data:image/png;base64,...`；
  DOCX 中每个图表一个 `word/media/imageN.emf`。
- **`INPUT PROGRAM` + `EXECUTE` 不产生任何 OMS 输出项**：单独提交时 OMS TEXT 为空、
  会被判定为失败；需在样例数据块后追加一个输出命令（如 `DESCRIPTIVES`）。
- **Q-Q（PPLOT）一次生成 2 张图**（Q-Q 图 + 去趋势 Q-Q 图），工具会返回全部路径。

## 3. 落定方案（SPSS 32）

| 目标格式 | 链路 |
|----------|------|
| PNG / TIFF | `OMS FORMAT=HTML IMAGES=YES IMAGEFORMAT=PNG OUTFILE='<root>.html'` → 正则提取 base64 → 解码 PNG → Pillow 缩放至目标尺寸（默认 1950×1500）并写入 300dpi 元数据（TIFF 由 PNG 转换，LZW） |
| EMF | `OMS FORMAT=DOC OUTFILE='<root>.docx'` → 解压 `word/media/imageN.emf` → 矢量 EMF 原样交付（期刊线稿可直接用；boxplot 除外，见上） |

### 高 DPI 说明

- HTML 内嵌 PNG 只有 ~800×500。已实测两种补救：
  1. **Pillow Lanczos 放大**（当前实现）：纯 Python，简单，文字边缘略软；
  2. **Windows GDI+ 矢量栅格化**（.NET `System.Drawing` 渲染 EMF，已实测可输出 1950×1500 锐利 PNG）：
     后续若需严格论文级位图，可对 EMF 走该路径（Windows-only，PowerShell 子进程）。

## 4. 真机验证中发现并修复的 GPL/语法问题

以下问题在 SPSS 32 真机上逐一暴露并已修复（`src/spss_mcp/chart_templates.py`）：

| 问题 | 现象 | 修复 |
|------|------|------|
| 生成语法末尾无换行 | `END GPL.OMSEND ...` 同行，OMS 块不关闭、HTML 不落盘、tag 级联冲突 | 每个命令生成后补 `\n`；拼接处归一化 |
| 多变量 GRAPHDATASET 重复关键字 | `VARIABLES=x VARIABLES=y` → `repeated keyword (VARIABLES)` | 改为 `VARIABLES=x y` |
| bar 内联 `summary.mean(val)` | `position(cat*summary.mean(val))` → GPL error | 在 GRAPHDATASET 预计算 `MEAN(var)[name="MEAN_var"]`，`position(cat*agg)` |
| line 用 `color.exterior` | 不被 line 元素接受 | 改为 `color.interior` |
| 饼图 `shape.pie` | SPSS 32 GPL 未定义 `shape.pie` | P1 不提供饼图工具，改用 `GRAPH /PIE` 可作为后续扩展 |

## 5. 图表库（11 个 `spss_chart_*` 工具，2026-08-04 真机全部出图验证）

| 工具 | 类型 | 实现 |
|------|------|------|
| `spss_chart_histogram` | 直方图 | GGRAPH `summary.count(bin.rect())` |
| `spss_chart_scatter` | 散点 | GGRAPH `point(position(x*y))` |
| `spss_chart_bar` | 条形（均值/求和） | GGRAPH 预计算 `MEAN/SUM(var)[name=...]` |
| `spss_chart_line` | 折线 | GGRAPH `line(position(x*y))` |
| `spss_chart_boxplot` | 箱线图 | GGRAPH `schema(position(cat*var))` |
| `spss_chart_errorbar` | 误差条（均值±CI） | GGRAPH 预计算 `MEANCI(var pct)[name=...]` |
| `spss_chart_qqplot` | 正态 Q-Q 图 | `PPLOT /TYPE=Q-Q /FRACTION=BLOM` |
| `spss_chart_km_curve` | KM 生存曲线 | `KM time BY group /STATUS=... /PLOT SURVIVAL` |
| `spss_chart_area` | 面积图 | GGRAPH `area(position(x*y))` |
| `spss_chart_histogram_density` | 直方图+正态密度 | GGRAPH `interval` + `line(density.normal())` |
| `spss_chart_bar_error` | 条形+误差条 | GGRAPH 预计算 `MEANCI` + 柱形 |

## 6. 复现

```powershell
cd D:\opencode\spss-studio-mcp
python scripts/poc_chart_pipeline.py    # 引擎启动约 15-20s + 两个变体
python -m spss_mcp.poc_chart --format PNG   # 11 种图表 × PNG
python -m spss_mcp.poc_chart --format EMF   # 11 种图表 × EMF（boxplot 预期报错提示降级）
```

产物（默认 `%TEMP%\spss-studio-mcp\results`）：
- `poc_histogram_001.png`（1950×1500 @300dpi，由 ~800×500 放大）
- `poc_histogram_emf_001.emf`（矢量）

## 7. 对代码的影响

- `src/spss_mcp/oms_image.py`：`build_oms_image_block` 改为生成 HTML OMS 块；
  新增 `build_oms_doc_block` / `extract_html_images` / `extract_docx_emf` / `validate_emf` / `oms_doc_end_block`。
- `src/spss_mcp/chart_service.py`：`export_chart` 按格式选择 HTML 或 DOC 链路，PNG/TIFF 走放大+DPI 后处理。
- `src/spss_mcp/chart_spec.py`：11 种 ChartSpec 模型。
- `src/spss_mcp/chart_templates.py`：11 个模板构建器（GGRAPH/PPLOT/KM）。
- `src/spss_mcp/server.py`：注册 11 个 `spss_chart_*` 工具。
