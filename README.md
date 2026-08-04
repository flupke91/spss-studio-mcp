# spss-studio-mcp

A Model Context Protocol (MCP) server for IBM SPSS Statistics: paper-ready chart
export, deep result parsing, and safe syntax execution for Codex / Claude / Cursor.

> Status: P0 skeleton — reuses the MIT-licensed engine/runner/CLI from
> `Exekiel179/SPSS-MCP` (37 tools), adds Codex configuration, CI, and lays the
> groundwork for the chart pipeline (G1), deep output parsing (G2), method
> verification (G3) and the security layer (G4). See `D:\opencode\SPSS-MCP-项目规划.md`.

## Requirements

- Windows 10/11 (analysis tools require SPSS; file tools work elsewhere)
- IBM SPSS Statistics 20–31
- Python 3.10+

## Install (dev)

```powershell
cd spss-studio-mcp
pip install -e ".[dev]"
spss-studio-mcp status
```

## Configure MCP client

```powershell
spss-studio-mcp configure-claude   # Claude Code (~/.claude.json)
spss-studio-mcp configure-codex    # Codex (~/.codex/config.toml)
spss-studio-mcp setup-info         # print config snippet
```

## CLI

```powershell
spss-studio-mcp serve --transport stdio
spss-studio-mcp status
spss-studio-mcp version
```

## Roadmap

- P0: skeleton + Codex config + CI (this branch)
- P1: paper-ready chart pipeline (GGRAPH + OMS IMAGE export, PNG/TIFF/EMF)
- P2: deep result parsing (Markdown + JSON + chart extraction)
- P3: verify all 37 tools on real SPSS + mediation/moderation tools
- P4: security layer (allowlists, dry-run, audit) + release

## License

MIT
