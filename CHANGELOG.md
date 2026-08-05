# Changelog

## [0.3.1] - 2026-08-05

### Fixed
- `spss_chart_boxplot`：GGRAPH `ELEMENT: schema` 在 SPSS 32 对真实数据报
  `outlier was found inside fences`（个案值恰落在箱须线上），且 DOCX/EMF 导出为
  0 字节；改为 `EXAMINE /PLOT BOXPLOT` 传统图模板，PNG/TIFF/EMF 均真机验证通过
  （EMF 18996 字节非零）。修复由实战作业验证触发，见项目规划 5.3。

## [0.3.0] - 2026-08-05

### Added
- P3 方法验证：26 个分析方法真机验收 + `scripts/method_verification.py`
- 中介/调节工具：`spss_mediation`（三步回归 + Sobel）、`spss_moderation`（中心化交互）
- P4 安全层：`security.py`（危险拦截/路径白名单/dry_run/审计 JSONL）
- 补充工具验收：文件类 6 件 + 状态/语法/结构化 + `spss_genlin`（`scripts/tool_verification.py`）
- 11 类图 × TIFF 全格式验证
- 文档：教程、技术报告、生态收录/发布准备

### Fixed
- `spss_correlations`：`TAILS(2)` → `TWOTAIL`
- `spss_compute_scale_score`：`MEAN`/`NVALID` 参数逗号分隔
- `spss_twostep_cluster`：子命令去 `=`、距离默认 LIKELIHOOD、删无效 OUTLIERS/PRINT
- `spss_discriminant` / `spss_manova`：因子/组值范围；MANOVA 删废弃 METHOD
- `spss_ordinal_regression`：删无效 `TEST=PARALLEL`
- `spss_genlinmixed`：subject 名义化、删无效 PRINT
- `spss_genlin`：`DISTRIBUTION` 并入 MODEL、`PRINT` 无等号

## [0.2.0] - 2026-08-04

### Added
- P1 出图管线：11 类图 spec + GGRAPH 模板 + `spss_chart_*` 工具
- OMS 导出双链路：HTML→base64 PNG 提取、DOCX→EMF 提取（SPSS 32 兼容）
- 图片后处理：Pillow 缩放 1950×1500 + 300 dpi 元数据
- P2 结果解析：`result_parser.py`（表格 JSON + 16 类统计摘要）
- `spss_structured_result` 统一返回结构
- 样例数据与归档：`examples/`（问卷/实验/生存/中介/纵向）

### Fixed
- GGRAPH 模板：末尾换行、`VARIABLES=x y`、bar 预计算 MEAN/MEANCI、line `color.interior`
- `poc_chart` 样例数据补 DESCRIPTIVES（INPUT PROGRAM 无输出问题）

## [0.1.0] - 2026-08-04

### Added
- P0 基座：复用 MIT 引擎/runner/CLI、37 工具基线
- 项目改名 `spss-studio-mcp`、`configure-codex`、CI（black/isort/pytest）
