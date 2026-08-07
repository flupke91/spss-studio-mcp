# SPSS Studio MCP：给 Agent 的傻瓜式使用教程

> 把 SPSS 变成 Agent 可以调用的统计引擎和制图工厂。
>
> 适用版本：v0.3+ ｜ 推荐环境：Windows 10/11、Python 3.10+、IBM SPSS Statistics 20–32

这篇教程专门写给第一次接触 MCP、SPSS-MCP 或 Agent 工作流的用户。你不需要先学会 MCP，也不需要记住工具名称。完成安装后，直接用自然语言告诉 Agent：数据在哪里、你想回答什么问题、希望得到什么结果。

## 1. 先理解它能做什么

传统流程通常是：打开 SPSS → 导入数据 → 找菜单 → 设置参数 → 运行 → 整理表格 → 导出图片 → 写结果。

SPSS Studio MCP 把其中大量重复操作交给 Agent：

- Agent 读取 `.sav` / `.zsav` 数据，检查变量、标签、缺失值和样本量；
- Agent 根据研究问题选择描述统计、t 检验、方差分析、回归、中介、调节、生存分析等方法；
- MCP 调用真实 IBM SPSS Statistics 引擎执行分析，而不是只凭语言模型猜结果；
- 返回 Markdown 表格、结构化 JSON、统计摘要、`.sps` 语法和 `.spv` Viewer 文件；
- 根据需要导出 PNG、TIFF 或 EMF 格式的 300 dpi 图表；
- 对危险语法、数据目录和执行过程进行安全检查并写入审计日志。

它适合论文分析、问卷研究、实验数据、医学随访、课程作业、研究助理和需要重复执行的统计流程。

## 2. 最快方式：把这段话发给你的 Agent

下面这段可以直接复制给 Codex、Claude Code 或其他支持 MCP 的 Agent。建议把项目目录、数据目录和当前使用的客户端说清楚。

```text
请帮我安装并配置 SPSS Studio MCP，让你可以直接调用 IBM SPSS Statistics 做统计分析和论文级出图。

项目地址：
https://github.com/flupke91/spss-studio-mcp

请按以下顺序执行，不要跳过检查：

1. 检查当前系统是否安装 Python 3.10 或更高版本、pip，以及 IBM SPSS Statistics。
2. 如果当前目录没有项目，请克隆项目；如果项目已经存在，请进入项目目录并检查是否为最新可用代码。
3. 安装项目依赖：pip install -e ".[dev]"。
4. 运行 spss-studio-mcp status，并告诉我 pyreadstat、pandas 和 SPSS batch 的状态。
5. 根据我当前使用的 Agent 自动配置 MCP：
   - 如果是 Codex，运行 spss-studio-mcp configure-codex；
   - 如果是 Claude Code，运行 spss-studio-mcp configure-claude；
   - 如果客户端不支持自动配置，运行 spss-studio-mcp setup-info，并给出手动配置片段。
6. 检查配置文件是否成功写入；如果修改了配置，请提示我重启 Agent。
7. 安装项目自带的 skills（如果当前项目包含 skills 目录），并说明安装位置。
8. 重启后，用 examples/data/survey_study.sav 做一次最小测试：读取变量、做描述统计和 Cronbach's alpha 可靠性分析。
9. 最后告诉我：安装是否成功、可调用哪些工具、示例结果文件在哪里，以及我下一步可以怎样用自然语言提出分析需求。

遇到错误时，请先判断是 Python、依赖、SPSS 路径、授权、MCP 配置还是数据路径问题，再给出最小修复方案。不要删除我的数据，不要修改原始数据文件。
```

如果 Agent 没有权限执行命令，就让它逐条解释命令，你在终端执行后把输出粘贴回来。Agent 可以根据输出继续完成配置和排错。

## 3. 手动安装：一步一步照做

### 3.1 检查环境

在 PowerShell 中执行：

```powershell
python --version
pip --version
```

Python 应为 3.10 或更高版本。然后确认 IBM SPSS Statistics 已经安装并且授权可用。SPSS Studio MCP 的文件读取工具可以在没有 SPSS 引擎时工作，但真正的统计分析和图表导出需要 SPSS。

### 3.2 获取项目并安装

```powershell
git clone https://github.com/flupke91/spss-studio-mcp.git
cd spss-studio-mcp
pip install -e ".[dev]"
```

如果项目已经在本机，直接进入项目目录再执行安装命令即可。开发依赖包含测试和格式化工具；只想运行服务时，也可以使用 `pip install -e .`。

### 3.3 检查 SPSS 状态

```powershell
spss-studio-mcp status
```

正常情况下会看到类似结果：

```text
=== SPSS MCP Capability Status ===
pyreadstat : OK v...
pandas     : OK v...
SPSS batch : OK - C:\Program Files\IBM\SPSS Statistics\32\stats.exe
```

如果显示 `SPSS batch : NOT FOUND`，先不要急着重装依赖。按照第 8 节设置 `SPSS_INSTALL_PATH`，再重新运行 `status`。

### 3.4 自动配置 Codex

如果你使用 Codex：

```powershell
spss-studio-mcp configure-codex
```

命令会更新 Codex 的 `~/.codex/config.toml`，并在修改已有文件前创建备份。执行完成后重启 Codex，让它重新加载 MCP 服务器。

### 3.5 自动配置 Claude Code

如果你使用 Claude Code：

```powershell
spss-studio-mcp configure-claude
```

命令会更新 Claude Code 的用户配置，并在需要时生成备份。执行完成后重启 Claude Code。

### 3.6 手动配置其他客户端

先生成配置提示：

```powershell
spss-studio-mcp setup-info
```

常见的 MCP 配置形式如下：

```json
{
  "mcpServers": {
    "spss": {
      "command": "spss-studio-mcp",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

不同客户端的配置文件位置和字段名称可能不同，以客户端文档和 `setup-info` 输出为准。配置完成后必须重启客户端，否则它可能仍然看不到新的工具。

## 4. 第一次验证：让 Agent 做一个最小任务

重启客户端后，先不要直接拿自己的论文数据测试。把下面这段发给 Agent：

```text
请先调用 spss_check_status，告诉我当前有哪些能力可用。
然后检查 examples/data/survey_study.sav：
1. 列出变量名、变量标签、变量类型和缺失值信息；
2. 预览前 10 行数据；
3. 对 engagement_total 做均值、标准差、最小值、最大值和样本量；
4. 对 q1 到 q12 做 Cronbach's alpha 可靠性分析；
5. 不要修改原始数据，只返回分析结果和生成文件的路径。
```

你应该得到：

- 数据文件和变量信息；
- 描述统计表；
- 可靠性统计结果；
- 自动生成的统计摘要；
- 需要时附带 `.sps` 和 `.spv` 文件路径。

如果这一步成功，说明 Agent 已经能发现 MCP 工具并调用 SPSS Studio MCP。

## 5. 给 Agent 下指令的正确姿势

不要只说“帮我分析一下”。高质量的请求至少包含五项：

1. **数据文件**：明确 `.sav` 文件路径；
2. **研究问题**：你想比较、预测、解释或描述什么；
3. **变量角色**：因变量、自变量、分组变量、中介变量、调节变量；
4. **分析要求**：是否需要前提检验、效应量、事后比较和可视化；
5. **交付格式**：论文结果段、Markdown 表格、语法文件、图片或结构化 JSON。

可以复用这个通用模板：

```text
请分析 [数据文件路径]。

研究问题：[用一句话说明想回答的问题]
因变量：[变量名和含义]
自变量或分组变量：[变量名和含义]
其他变量：[协变量 / 中介 / 调节 / 时间 / 个体 ID]

请按以下流程执行：
1. 先检查样本量、变量类型、缺失值、异常值和必要的前提条件；
2. 如果我的统计方法不合适，请解释原因并选择更合适的方法；
3. 执行分析并报告关键统计量、p 值、置信区间和效应量；
4. 给出适合论文结果部分的中文解释，但不要把相关关系写成因果关系；
5. 保存可复现的 SPSS syntax，并保留原始数据不变；
6. 如果适合，请生成论文级图片，并告诉我图片路径和格式。
```

## 6. 常见研究场景

### 6.1 问卷：描述统计、信度和组间差异

```text
请分析 examples/data/survey_study.sav。
先检查样本量、变量标签、缺失值和 q1-q12 的取值范围。
然后完成：
1. 对 q1-q12 做 Cronbach's alpha 可靠性分析；
2. 对 engagement_total 做描述统计和正态性检查；
3. 按 gender 比较 engagement_total，先判断使用独立样本 t 检验是否合适；
4. 按 major 比较 engagement_total，使用单因素方差分析并在需要时做事后比较；
5. 绘制 engagement_total 的直方图和 Q-Q 图；
6. 输出表格、统计摘要、论文结果段、SPSS syntax 和图像路径。
```

### 6.2 实验：前后测和组间比较

```text
请分析 examples/data/experiment_study.sav。
变量为 group、pretest、posttest 和 gain。
请先检查 group 的编码和每组样本量，然后：
1. 报告两组 pretest 和 posttest 的描述统计；
2. 比较两组 posttest 是否存在差异；
3. 比较两组 gain 是否存在差异；
4. 对同一被试的 pretest 与 posttest 做配对样本 t 检验；
5. 报告均值差、95% CI、t、df、p 和效应量；
6. 生成按 group 分组的 posttest 箱线图；
7. 写出谨慎、适合论文的结果解释。
```

### 6.3 相关和回归：避免把相关写成因果

```text
请对 examples/data/mediation_study.sav 做相关和回归分析。
研究问题是 autonomy、satisfaction 与 performance 的关系。
请先检查变量分布和异常值，再完成：
1. Pearson 相关矩阵；
2. 以 performance 为因变量、autonomy 和 satisfaction 为预测变量的多元线性回归；
3. 报告 R²、调整 R²、模型检验、标准化系数、置信区间和共线性诊断；
4. 绘制 satisfaction 与 performance 的散点图；
5. 用“相关”和“预测”表述结果，不要直接声称存在因果关系。
```

### 6.4 中介分析

```text
请对 examples/data/mediation_study.sav 做中介分析：
X = autonomy，M = satisfaction，Y = performance。

请先检查三个变量的样本量、缺失值和基本分布，再调用合适的中介分析工具。
报告总效应、直接效应、间接效应 a×b、Sobel 检验和每一步回归结果。
请明确说明这个分析能支持的统计结论和不能支持的因果结论，
并保存完整的 SPSS syntax 与结果文件。
```

### 6.5 调节分析

```text
请对 examples/data/mediation_study.sav 做调节分析：
X = autonomy，W = satisfaction，Y = performance。

请对 X 和 W 做中心化，建立包含主效应和 X×W 交互项的回归模型。
报告交互项系数、标准误、t、p、置信区间和模型解释度变化。
如果交互项显著，请解释它表示的调节方向；如果不显著，请明确说不支持调节效应。
不要只根据主效应判断调节成立。
```

### 6.6 生存分析

```text
请分析 examples/data/survival_study.sav。
变量为 treatment、time 和 status，其中 status=1 表示事件发生。
请完成：
1. 检查 time 和 status 的编码；
2. 按 treatment 绘制 Kaplan-Meier 生存曲线；
3. 进行组间生存比较；
4. 报告中位生存时间、置信区间和 log-rank 结果；
5. 说明删失数据如何被处理；
6. 输出论文级 PNG 图片和可复现语法。
```

## 7. 论文级出图

SPSS Studio MCP 提供多类 `spss_chart_*` 工具。常用选择如下：

| 工具 | 适用场景 |
|------|----------|
| `spss_chart_histogram_density` | 连续变量分布和正态性展示 |
| `spss_chart_qqplot` | 正态 Q-Q 检查 |
| `spss_chart_scatter` | 两个连续变量的关系 |
| `spss_chart_bar_error` | 分组均值和 95% CI |
| `spss_chart_boxplot` | 组间分布、异常值和中位数 |
| `spss_chart_errorbar` | 均值与置信区间 |
| `spss_chart_line` / `spss_chart_area` | 时间序列或重复测量趋势 |
| `spss_chart_km_curve` | Kaplan-Meier 生存曲线 |

直接给 Agent 的出图请求：

```text
请使用 examples/data/survey_study.sav。
以 engagement_total 为变量，绘制论文级直方图并叠加正态密度曲线。
要求：PNG、300 dpi、1950×1500 像素，中文标题为“学习投入总分分布”。
检查图片是否成功生成，返回绝对路径，并说明该图适合放在论文哪个部分。
```

图片工具默认返回可用的文件路径。投稿前仍应检查字体、坐标轴标题、图例、分辨率和期刊格式要求。

## 8. 输出文件和复现

一次分析可能产生以下结果：

| 文件或字段 | 用途 |
|------------|------|
| Markdown | 直接阅读和复制到笔记或报告 |
| JSON | 供脚本、网页或后续 Agent 消费 |
| `.sps` | 保存实际执行的 SPSS 语法，便于复现 |
| `.spv` | 在 SPSS Viewer 中查看完整输出 |
| PNG / TIFF / EMF | 论文、汇报或进一步排版 |
| `logs/audit.jsonl` | 记录执行过程和安全审计信息 |

涉及数据变换时，明确要求 Agent 另存为新文件：

```text
可以生成派生变量，但不要覆盖原始 data.sav。
请把变换后的数据保存为 data_derived.sav，并在结果中列出每个新变量的计算规则。
后续分析只使用 data_derived.sav。
```

注意：每次提交通常会重新载入数据文件，上一轮 `COMPUTE` 生成的临时变量不会自动保留。需要保留时，使用 `SAVE OUTFILE=...` 保存为新的数据集。

## 9. 安全使用建议

- 先让 Agent 读取元数据，再允许它执行复杂分析；
- 不要把含有身份证号、银行卡号、密码或其他不必要的敏感信息的数据上传给不可信的客户端；
- 要求 Agent 不覆盖原始数据，并把派生数据保存到新文件；
- 对陌生语法先使用 `dry_run=True` 校验，不要直接执行；
- 保留 `.sps` 语法和审计日志，方便复核；
- 将允许访问的数据目录限制在项目目录或专门的分析目录。

项目默认会拦截 `HOST`、`ERASE`、`DELETE FILE` 等危险命令，并限制数据文件路径。详细规则见 [安全层说明](security.md)。

## 10. SPSS 路径和环境变量

### 10.1 设置 SPSS 安装路径

如果自动检测失败，在项目目录创建 `.env` 文件：

```ini
SPSS_INSTALL_PATH=C:\Program Files\IBM\SPSS Statistics\32
```

也可以在当前 PowerShell 会话中临时设置：

```powershell
$env:SPSS_INSTALL_PATH = "C:\Program Files\IBM\SPSS Statistics\32"
spss-studio-mcp status
```

### 10.2 调整超时

首次启动 SPSS 引擎通常比后续调用慢。如果首次启动超时，在 `.env` 中增加：

```ini
SPSS_STARTUP_TIMEOUT=300
SPSS_TIMEOUT=120
```

`SPSS_STARTUP_TIMEOUT` 控制引擎首次启动，`SPSS_TIMEOUT` 控制单次分析任务。复杂模型可以适当提高后者。

### 10.3 设置数据白名单

如果数据放在项目目录之外，可以设置允许访问的目录。具体格式以项目当前版本的配置说明为准；推荐只加入专门的研究数据目录，不要直接放开整个磁盘。

## 11. 常见问题

### `SPSS batch : NOT FOUND`

先确认 `stats.exe` 的真实位置，再设置 `SPSS_INSTALL_PATH`。设置后重新打开终端或重新运行 `status`。

### Agent 看不到 SPSS 工具

依次检查：

1. 是否运行了正确的 `configure-codex` 或 `configure-claude`；
2. 客户端是否已重启；
3. `spss-studio-mcp status` 是否能成功运行；
4. 客户端配置中的命令是否能在当前终端找到；
5. 是否有多个旧的 SPSS MCP 配置互相冲突。

### 首次分析很慢或超时

第一次启动引擎约需 15–20 秒，之后通常会保持常驻。不要同时打开多个 SPSS 会话；必要时提高 `SPSS_STARTUP_TIMEOUT` 或 `SPSS_TIMEOUT`。

### 提示未授权或图片导出失败

确认 IBM SPSS Statistics 授权有效，并检查是否有残留的 `stats.exe`、`spssengine` 或 `spsswers.dll` 进程占用试用席位。结束残留进程后重新尝试，并避免同时启动多个 SPSS 会话。

### 数据文件被拒绝

将数据放入 `examples/data/`、系统临时目录或配置的允许目录。不要通过改名绕过安全限制；应该正确设置数据白名单。

### 中文变量标签显示异常

优先在 Prompt 中使用变量名，并让 Agent 先读取变量标签。工具内部会尽量建立变量名与标签的映射，但统计语法仍应使用 SPSS 中真实存在的变量名。

## 12. 一键完成完整分析的最终模板

当你已经熟悉基本操作，可以直接把下面的模板发给 Agent：

```text
请作为我的 SPSS 统计分析助手，分析 [数据文件路径]，不要修改原始文件。

研究背景：[研究对象、研究目的和假设]
数据说明：[样本量、变量含义、分组方式、时间结构]
核心问题：[希望回答的统计问题]

请严格按以下顺序完成：
1. 读取元数据，检查变量类型、标签、取值范围、缺失值和样本量；
2. 说明每一个研究问题适合使用什么统计方法，以及选择理由；
3. 执行必要的前提检验和异常值检查；
4. 执行正式分析，报告估计值、标准误、置信区间、检验统计量、自由度、p 值和效应量；
5. 生成与研究问题对应的论文级图表，要求 PNG 300 dpi；
6. 给出中文结果解释和可直接修改的论文结果段；
7. 保存完整 SPSS syntax、Viewer 输出和图像文件；
8. 返回 Markdown 结果、结构化摘要、所有输出路径和警告；
9. 最后列出结果的局限性，不把横断面相关关系表述为因果关系。

如果变量编码、研究设计或统计假设不清楚，请先指出问题并向我提问，不要擅自假设。
```

## 13. 开发者和高级用户

在项目根目录运行：

```powershell
python scripts/make_sample_data.py
python scripts/method_verification.py
python scripts/tool_verification.py
python scripts/archive_sample_charts.py
pytest
```

实现、结果解析、方法验证和安全边界分别见：

- [技术报告](technical_report.md)
- [出图管线](poc_chart_pipeline.md)
- [结果解析](result_parsing.md)
- [方法验证](method_verification.md)
- [安全层](security.md)

如果你要把固定的研究流程交给团队反复使用，可以把“数据检查 → 方法选择 → 分析 → 出图 → 论文解释”的 Prompt 固化为团队 skill，并要求每次输出 `.sps` 语法和审计记录。
