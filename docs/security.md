# 安全层（P4）

> 实现日期：2026-08-05 ｜ 真机验证：SPSS 32.0.0（dry_run / 危险拦截 / 审计全通过）

## 模块

`src/spss_mcp/security.py`

| 能力 | 实现 |
|------|------|
| 危险语句拦截 | `check_syntax_safety(syntax)`：行首匹配 `HOST / ERASE / DELETE FILE / FILE HANDLE / INSERT FILE / SCRIPT / CD / SYSTEM`，避免变量名误报 |
| 路径白名单 | `validate_data_file(path)`：允许 `SPSS_ALLOWED_DIRS`（分号分隔）、项目 `examples/`、系统临时目录；拒绝不存在或白名单外路径 |
| 审计日志 | `audit(entry)`：JSONL 追加写入 `logs/audit.jsonl`（`SPSS_AUDIT_LOG` 可改路径），失败不阻断分析 |
| dry_run | `spss_run_syntax(..., dry_run=True)`：只校验语法安全与路径，不启动执行 |

## 集成点

- `spss_runner.run_syntax`：统一安全闸（所有工具共用）——先拦截危险命令，
  再校验 `data_file` 参数与语法中的 `GET FILE='...'` 路径；每次成功执行写审计。
- `server.spss_run_syntax`：新增 `dry_run` 参数；`spss_structured_result` 同走
  `run_syntax` 安全闸。

## 审计事件

| event | 含义 |
|-------|------|
| `blocked / dangerous_syntax` | 语法含危险命令，未执行 |
| `blocked / path` | 数据文件不存在或不在白名单，未执行 |
| `dry_run` | dry_run 校验请求（含被拦命令列表） |
| `syntax_run` | 正常执行（含语法首行摘要、data_file、success、error） |

## 真机验证记录

```
dry_run:      Dry run: syntax is safe to execute ...
HOST 语法:    Error: Syntax blocked: dangerous commands HOST.
正常分析:     通过（FREQUENCIES 正常返回）
外部路径:     Error: Data file does not exist: D:/outside/x.sav
审计日志:     dry_run / blocked / syntax_run 事件均落盘
```

## 配置

```powershell
$env:SPSS_ALLOWED_DIRS = "C:\data;D:\research\data"   # 额外允许的数据目录
$env:SPSS_AUDIT_LOG    = "D:\logs\spss-audit.jsonl"   # 审计日志位置
```