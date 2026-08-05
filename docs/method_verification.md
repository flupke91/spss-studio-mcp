# P3 ??????????

> ?????2026-08-05 ? ???IBM SPSS Statistics 32.0.0 ? ???`examples/data/*.sav`???/??/??/??/???

## ????

- **26 ???????**?26/26?
- ??????? / ?? / ?? / ?? / ??? / ??? / ?? / ???? / ???+????? / ??+???? / ?? / MANOVA / t ???3 ??/ ????M-W/Wilcoxon?/ ???? ANOVA / KM / Cox / Logistic / ???? / ???? / ???? / ????????

## ??

| ?? | ?? | ?? | ?????? | ??(s) |
|---|---|---|---|---|
| descriptives | `spss_descriptives` | ? | ??? | 4.7 |
| frequencies | `spss_frequencies` | ? | ??? | 1.5 |
| correlations | `spss_correlations` | ? | ??? | 1.9 |
| crosstabs | `spss_crosstabs` | ? | ??? | 1.6 |
| normality_outliers | `spss_normality_outliers` | ? | ??? | 3.6 |
| reliability_alpha | `spss_reliability_alpha` | ? | ??? | 2.1 |
| factor | `spss_factor` | ? | ??? | 2.1 |
| compute_scale_score | `spss_compute_scale_score` | ? | ??? | 2.1 |
| glm_univariate | `spss_glm_univariate` | ? | ??? | 1.5 |
| cluster_hierarchical | `spss_cluster_hierarchical` | ? | ??? | 6.0 |
| twostep_cluster | `spss_twostep_cluster` | ? | ??? | 2.0 |
| discriminant | `spss_discriminant` | ? | ??? | 2.9 |
| manova | `spss_manova` | ? | ??? | 1.9 |
| ttest_independent | `spss_t_test` | ? | ??? | 2.1 |
| ttest_paired | `spss_t_test` | ? | ??? | 1.6 |
| ttest_one_sample | `spss_t_test` | ? | ??? | 1.4 |
| nonparam_mann_whitney | `spss_nonparametric_tests` | ? | ??? | 1.5 |
| nonparam_wilcoxon | `spss_nonparametric_tests` | ? | ??? | 1.3 |
| repeated_measures_anova | `spss_repeated_measures_anova` | ? | ??? | 2.0 |
| kaplan_meier | `spss_kaplan_meier` | ? | ??? | 3.1 |
| cox_regression | `spss_cox_regression` | ? | ??? | 1.6 |
| logistic_regression | `spss_logistic_regression` | ? | ??? | 1.9 |
| regression | `spss_regression` | ? | ??? | 1.5 |
| ordinal_regression | `spss_ordinal_regression` | ? | ??? | 1.9 |
| mixed | `spss_mixed` | ? | ??? | 1.8 |
| genlinmixed | `spss_genlinmixed` | ? | ??? | 15.3 |

## ?????? SPSS ??????????

| ?? | ?? | ?? |
|---|---|---|
| `spss_correlations` | `/PRINT=TAILS(2)` ?? | ?? `TWOTAIL` / `ONETAIL` |
| `spss_compute_scale_score` | `MEAN(q1 q2 ...)` ??? | ????????? |
| `spss_twostep_cluster` | `DISTANCE=EUCLID` ????? `=`?`EUCLID` ????????`OUTLIERS`/`PRINT` ?????? | ??????????? `LIKELIHOOD`???????? |
| `spss_discriminant` | `/GROUPS=var` ???? | ? `group_values` ????? 1 2? |
| `spss_manova` | ??? `(min max)`?`/METHOD=SSTYPE3` ????? | ??????????? METHOD ? |
| `spss_ordinal_regression` | `/TEST=PARALLEL` ?? | ???? |
| `spss_genlinmixed` | `/PRINT SOLUTION` ???subject ?????? | ??????????? `VARIABLE LEVEL`?????? nominal ???? |

## ??

```powershell
python scripts/make_sample_data.py
python scripts/method_verification.py
```


## 新增中介 / 调节工具（2026-08-05）

| 工具 | 实现 | 输出 |
|------|------|------|
| `spss_mediation` | Baron & Kenny 三步回归（M~X; Y~X; Y~X+M） | 路径 a/b/c/c'、间接效应 a×b、Sobel z/p |
| `spss_moderation` | 均值中心化回归（Y ~ X + W + X×W） | 各系数 + 交互项 t/p（调节检验） |

- 未捆绑 PROCESS 宏（版权），输出附 Bootstrap 复核建议。
- 真机验证（`mediation_study.sav`）：中介间接效应 a×b=0.245, Sobel z=6.75, p<.001；
  调节交互项 p=.639（模拟数据无调节，符合预期）。
- 解析处理：SPSS 输出行标签为中文变量标签时，通过读取 .sav 元数据建立
  变量名↔标签映射后匹配系数。

## 补充验收：其余工具（2026-08-05，11/11 通过）

| 用例 | 工具 | 说明 |
|------|------|------|
| read_data / file_summary / list_variables / read_metadata / list_files | 文件类 5 件 | 真实 `.sav` 读取/元数据/目录列表 |
| import_csv | `spss_import_csv` | CSV→.sav 导入（20 行×18 变量） |
| check_status | `spss_check_status` | 能力/路径/引擎状态 |
| validate_syntax | `spss_validate_syntax` | 语法校验（FINISH 提前终止） |
| structured_result | `spss_structured_result` | 统一 `{markdown, json, files, warnings}` |
| run_syntax_full | `spss_run_syntax` | 默认完整路径（含 .spv/.sps 落盘） |
| genlin | `spss_genlin` | 补齐注册方法（修复 DISTRIBUTION 语法） |

## 图表工具格式矩阵（P1 起累计验证）

- **11 类 × PNG / EMF / TIFF** 全部真机验证通过（1950×1500 @300dpi）；
- 例外：boxplot 的 **EMF** 为 SPSS 32 自身 0 字节 bug（PNG/TIFF 正常，已加降级提示）；
- qqplot 一次产出 2 张（Q-Q + 去趋势 Q-Q），工具返回全部路径。

## 补充修复

| 方法 | 问题 | 修复 |
|------|------|------|
| `spss_genlin` | `/PRINT=...` 等号无效；`DISTRIBUTION` 非独立子命令 | `DISTRIBUTION/LINK` 并入 `/MODEL` 子命令；`/PRINT SOLUTION` 无等号 |

## 复现

```powershell
python scripts/method_verification.py   # 26 个分析方法用例
python scripts/tool_verification.py     # 11 个补充工具用例
python -m spss_mcp.poc_chart --format TIFF   # 11 类图 × TIFF
```
