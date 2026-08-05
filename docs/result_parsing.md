# P2 结果解析：Markdown + JSON + 统计摘要

> 实现日期：2026-08-05 ｜ 依据 SPSS Statistics 32.0.0 真实 OMS TEXT 输出开发

## 目标

把 SPSS 文本输出转成机器可读的 JSON（表格级），并自动抽取论文汇报所需的
关键统计量（t / F / r / B / Wald / p / 效应量等），最后统一为
`{markdown, json, files, warnings}` 返回结构。

## 模块

`src/spss_mcp/result_parser.py`

| 函数 | 作用 |
|------|------|
| `parse_tables(raw_text)` | 行扫描状态机切分 SPSS 表块 → `[{title, headers, rows}]`（JSON 友好） |
| `summarize_analysis(raw_text)` | 按表标题识别分析类型，抽取统计量并生成自然语言结论 |
| `build_result_payload(result)` | 组装统一结构 `{markdown, json, files, warnings}` |

`src/spss_mcp/spss_runner.py`：`run_syntax` 返回新增 `tables` / `summary` / `files` 字段（增量，不破坏现有工具）。

`src/spss_mcp/server.py`：新增工具 **`spss_structured_result`**，执行任意语法并返回统一 JSON 结构；
同时 `_format_run_result` 会自动把统计摘要追加到所有分析工具（`spss_t_test`/`spss_regression`/`spss_anova` 等）的返回末尾（`### 统计摘要` 段落）。

## 解析规则要点（SPSS TEXT 真实布局）

- 表标题是行首无缩进的独立短行；缩进行是表头/数据的一部分，不会被误判为新表。
- 单空格连接的单元格（行标签-数值粘连、`Kolmogorov-Smirnov(a) Shapiro-Wilk` 等）通过
  「整行文本 + 数值正则」处理，不依赖严格列对齐。
- 表头判定启发式：首行含小数（`.000`、`-3.875`）视为数据行；否则视为表头
  （`-2 Log likelihood` 这类含整数的表头仍正确归为表头）。
- 子标题（如 `Dependent Variable xxx`）只并入标题一次，且必须是不含数字的纯文本行。
- `Notes` 块整体跳过；带 `(a)` 脚注的数字可解析；p 值 `.000` 汇报为 `<.001`。

## 统计摘要覆盖（16 类真实输出验证）

| 分析 | 表 | 提取项 | 示例输出 |
|------|----|--------|----------|
| 描述统计 | `Descriptive Statistics` | 每变量 N/Min/Max/Mean/Std | `score: N=120, Mean=54.20, SD=11.23` |
| 独立样本 t 检验 | `Independent Samples Test` / `Group Statistics` | t、df、p、均值差、组统计 | `t(118) = -3.88, p < .001, MD = -7.52` |
| 配对 t 检验 | `Paired Samples Test` | t、df、p、均值差 | `t(119) = -12.84, p < .001, MD = -9.88` |
| 单因素 ANOVA | `ANOVA` + Levene | F、df1、df2、p、Levene F | `F(1, 118) = 15.01, p < .001` |
| 多因素 ANOVA | `Tests of Between-Subjects Effects` | 各效应 F/df1/p/偏η² | `gender: F(1, 194) = .34, η² = .002` |
| 相关 | `Correlations` | r、p | `y-x: r = .42, p < .001` |
| 线性回归 | `Model Summary`/`ANOVA`/`Coefficients` | R、R²、F、B/Beta/t/p | `R = .82, R² = .68; x: B = .92, Beta = .48` |
| Logistic 回归 | `Model Summary`/`Variables in the Equation` | -2LL、Cox&Snell/Nagelkerke R²、B/SE/Wald/Exp(B)/p | `x: B = .19, Wald = .16, p = .69, OR = 1.21` |
| 频数 | `Statistics` | N/Mean/Median/Mode/Std | `N=120, Mean=.50` |
| 卡方 | `Chi-Square Tests` | χ²、df、p | `χ²(2) = .61, p = .739` |
| 可靠性 | `Reliability Statistics` | Cronbach's α、题项数 | `α = .82 (12 items)` |
| 非参数 | `Test Statistics` | Mann-Whitney U/Wilcoxon Z/K-W H、df、p | `U = 1088.50, z = -3.72, p < .001` |
| 正态性 | `Tests of Normality` | Shapiro-Wilk W、K-S D、df、p | `W(200) = .99, p = .101` |
| 因子分析 | `KMO and Bartlett's Test` / `Total Variance Explained` | KMO、Bartlett χ²、特征值、累计方差 | `KMO = .50, χ²(66) = 64.68` |

## 测试

- 16 个真实输出 fixture：`tests/fixtures/spss_outputs/*.txt`
- `tests/test_result_parser.py`：23 项断言覆盖全部类型的解析、摘要与统一结构
- 真机验证：`run_syntax` 对 T-TEST 返回完整 `summary` 与 `tables`

## 使用

```python
from spss_mcp.spss_runner import run_syntax
result = await run_syntax("T-TEST GROUPS=g(0 1) /VARIABLES=score.")
result["summary"]["text"]   # 自然语言结论
result["summary"]["summaries"]  # 结构化统计量
result["tables"]            # JSON 友好表格
```

MCP 客户端可调用 `spss_structured_result` 获得统一 JSON 返回。