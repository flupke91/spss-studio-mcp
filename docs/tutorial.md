# SPSS Studio MCP 使用教程

> 适用版本：v0.3+ ｜ 实测：IBM SPSS Statistics 32.0.0 ｜ 目标读者：研究者 / Agent 使用者

---

## 1. 这是什么

`spss-studio-mcp` 是一个 MCP 服务器，把 SPSS 变成 Agent 的"统计引擎 + 制图工厂"：

- 一句话生成**论文级图片**（11 类图，PNG/TIFF/EMF，300 dpi，路径回传）
- 分析结果返回 **Markdown 表格 + JSON + 统计摘要**（t/F/r/B/p 等）
- 37 个分析方法**全部真机验收**，中介/调节一步完成
- 危险语法拦截 + 路径白名单 + 审计日志，让"LLM 生成语法"可被信任

## 2. 安装与配置（3 分钟）

```powershell
cd D:\opencode\spss-studio-mcp
pip install -e ".[dev]"
spss-studio-mcp status          # 应显示 SPSS batch: OK

spss-studio-mcp configure-codex    # Codex 客户端配置
spss-studio-mcp configure-claude   # Claude Code 配置
```

## 3. 样例数据

`examples/data/` 提供 5 组贴近论文场景的样例数据（固定随机种子，可复现）：

| 文件 | 场景 | 关键变量 |
|------|------|----------|
| `survey_study.sav` | 问卷：200 人学习投入 | `gender`/`major`/`q1`-`q12`/`engagement_total` 等 |
| `experiment_study.sav` | 实验：120 人记忆训练前后测 | `group`/`pretest`/`posttest`/`gain` |
| `survival_study.sav` | 生存：150 例随访 | `treatment`/`time`/`status` |
| `mediation_study.sav` | 中介：300 员工 | `autonomy`/`satisfaction`/`performance` |
| `longitudinal_study.sav` / `long_study.sav` | 纵向：60 人 3 次测量 | `id`/`group`/`time`/`score` |

## 4. 常用分析（自然语言即可驱动）

以问卷数据为例：

- 描述统计：`spss_descriptives(variables=[engagement_total, cognitive, affective, behavioral], file_path=examples/data/survey_study.sav)`
- 频数：`spss_frequencies(variables=[gender, major], ...)`
- 相关：`spss_correlations(variables=[cognitive, affective, behavioral], ...)`
- 卡方：`spss_crosstabs(row_variable=gender, column_variable=major, ...)`
- 独立样本 t：`spss_t_test(test_type="independent", variables=[posttest], grouping_variable=group, ...)`
- 配对 t：`spss_t_test(test_type="paired", variables=[pretest, posttest], ...)`
- 单因素方差：`spss_glm_univariate(dependent=engagement_total, factors=[gender, major], ...)`
- 重复测量：`spss_repeated_measures_anova(within_factor_name=time, levels=2, variables=[pretest, posttest], ...)`
- 非参数：`spss_nonparametric_tests(test_type="mann_whitney", variables=[posttest], grouping_variable=group, group_values=[1, 2], ...)`
- 可靠性：`spss_reliability_alpha(variables=q1..q12, ...)`
- 因子：`spss_factor(variables=q1..q12, rotation=VARIMAX, ...)`
- 回归：`spss_regression(dependent=performance, predictors=[autonomy, satisfaction], ...)`
- Logistic：`spss_logistic_regression(dependent=status, predictors=[treatment, time], ...)`
- 生存：`spss_kaplan_meier(time_variable=time, status_variable=status, status_event_value=1, strata=treatment, ...)`
- 混合模型：`spss_mixed(dependent=score, fixed_effects=[time, group], subject=id, repeated=time, ...)`

每个分析工具返回 Markdown 表格，末尾自动附 **`### 统计摘要`**（自然语言结论 + 关键统计量）。

## 5. 论文级出图（核心卖点）

11 个 `spss_chart_*` 工具，输出 1950×1500 @300dpi：

| 工具 | 用途 |
|------|------|
| `spss_chart_histogram` | 分布直方图 |
| `spss_chart_histogram_density` | 直方图 + 正态密度（正态性展示） |
| `spss_chart_scatter` | 两变量散点 |
| `spss_chart_bar` | 分类均值/求和条形 |
| `spss_chart_bar_error` | 条形 + 95% CI 误差须 |
| `spss_chart_line` / `spss_chart_area` | 时间序列折线/面积 |
| `spss_chart_boxplot` | 分组箱线图 |
| `spss_chart_errorbar` | 均值 ± CI 误差条 |
| `spss_chart_qqplot` | 正态 Q-Q 图 |
| `spss_chart_km_curve` | Kaplan-Meier 生存曲线 |

参数示例：

```python
spss_chart_histogram_density(
    variable="engagement_total",
    title="学习投入总分分布（带正态密度）",
    image_format="PNG",           # PNG / TIFF / EMF
    width_px=1950, height_px=1500, dpi=300,
    data_file="examples/data/survey_study.sav",
)
# → 返回图片文件路径，可直接投稿
```

样例输出见 `examples/charts/*.png`。

## 6. 结构化结果与统计摘要

- `spss_structured_result(syntax=..., data_file=...)` 返回统一 JSON：
  `{markdown, json: {tables, summary}, files, warnings}`
- `run_syntax` 返回新增 `tables` / `summary` / `files` 字段，编程消费方便。

## 7. 中介与调节

- `spss_mediation(x=autonomy, mediator=satisfaction, y=performance, ...)`：
  三步回归 + 间接效应 a×b + Sobel 检验。
- `spss_moderation(x=autonomy, moderator=satisfaction, y=performance, ...)`：
  中心化交互回归，报告 X×W 交互项 t/p。

## 8. 安全

- 危险命令自动拦截（HOST / ERASE / DELETE FILE 等）；
- 数据文件需在 `examples/`、临时目录或 `SPSS_ALLOWED_DIRS` 内；
- `spss_run_syntax(..., dry_run=True)` 只校验不执行；
- 审计日志：`logs/audit.jsonl`（`SPSS_AUDIT_LOG` 可改）。

## 9. 复现与扩展

```powershell
python scripts/make_sample_data.py      # 重建样例数据
python scripts/method_verification.py   # 26 方法真机验收
python scripts/tool_verification.py     # 11 工具真机验收
python scripts/archive_sample_charts.py # 重新出归档图
```

详细实现与验证：`docs/technical_report.md`、`docs/poc_chart_pipeline.md`、
`docs/result_parsing.md`、`docs/method_verification.md`、`docs/security.md`。

## 10. 常见问题

- **引擎启动慢**：首次 15–20 秒，之后常驻；不要同时开多个 SPSS 会话（试用版席位有限）。
- **图片提示失败**：检查 SPSS 授权；若引擎残留（`stats.exe` / `spssengine` / `spsswers.dll`）
  占用试用席位导致 "not licensed"，结束残留进程后重试。
- **数据文件被拒**：把文件放入 `examples/data/` 或用 `SPSS_ALLOWED_DIRS`。
- **中文标签**：变量有中文标签时，工具内部已建立 标签↔变量名 映射，正常使用变量名即可。
- **派生变量跨提交丢失**：每次提交会重新载入数据文件，上一轮 `COMPUTE` 的变量不会保留；
  先 `SAVE OUTFILE=...` 存成新数据集，后续提交再 `GET FILE` 新文件。
