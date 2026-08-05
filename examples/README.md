# 真机样例图归档（P1）

> 生成日期：2026-08-04 ｜ 引擎：IBM SPSS Statistics 32.0.0 ｜ 图片：PNG 1950×1500 @300dpi

四组贴近论文场景的样例数据与代表性出图，用于演示与回归验证 `spss_chart_*` 工具。

## 目录

- `data/` — 四个场景的 SPSS 数据文件（.sav，含变量/值标签）
- `charts/` — 用真实 SPSS 引擎导出的 11 张 PNG 图

## 数据集

| 文件 | 场景 | 样本量 | 关键变量 |
|------|------|--------|----------|
| `data/survey_study.sav` | 问卷：大学生学习投入 | 200 | `gender`/`major`/`q1`-`q12`/`cognitive`/`affective`/`behavioral`/`engagement_total` |
| `data/experiment_study.sav` | 实验：记忆训练前后测 | 120 | `group`（训练/对照）/`pretest`/`posttest`/`gain` |
| `data/survival_study.sav` | 生存：治疗方案随访 | 150 | `treatment`/`time`/`status`（1=死亡，0=删失） |
| `data/mediation_study.sav` | 中介：工作自主性→满意度→绩效 | 300 | `autonomy`/`satisfaction`/`performance` |

## 图表清单（examples/charts）

| 图 | 场景 | 工具 |
|----|------|------|
| `survey_engagement_histogram_density.png` | 问卷 | `spss_chart_histogram_density` |
| `survey_engagement_by_major.png` | 问卷 | `spss_chart_bar_error` |
| `survey_engagement_by_gender.png` | 问卷 | `spss_chart_errorbar` |
| `experiment_posttest_boxplot.png` | 实验 | `spss_chart_boxplot` |
| `experiment_gain_errorbar.png` | 实验 | `spss_chart_errorbar` |
| `experiment_posttest_bar.png` | 实验 | `spss_chart_bar` |
| `survival_km_curve.png` | 生存 | `spss_chart_km_curve` |
| `survival_time_histogram.png` | 生存 | `spss_chart_histogram` |
| `mediation_autonomy_performance_scatter.png` | 中介 | `spss_chart_scatter` |
| `mediation_satisfaction_performance_scatter.png` | 中介 | `spss_chart_scatter` |
| `mediation_performance_histogram_density.png` | 中介 | `spss_chart_histogram_density` |

## 复现

```powershell
# 1) 重新生成样例数据（固定随机种子，可复现）
python scripts/make_sample_data.py

# 2) 真机导出归档图（需 SPSS + 授权）
python scripts/archive_sample_charts.py
```

## 在 MCP 工具中使用

任选一个 `.sav` 作为 `data_file` 传给图表工具即可，例如：

- 生存曲线：`spss_chart_km_curve(time="time", status="status", group="treatment", data_file="examples/data/survival_study.sav")`
- 问卷分布：`spss_chart_histogram_density(variable="engagement_total", data_file="examples/data/survey_study.sav")`
- 实验箱线：`spss_chart_boxplot(variable="posttest", category="group", data_file="examples/data/experiment_study.sav")`