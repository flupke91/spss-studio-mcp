"""
Helpers for generating and updating Codex MCP configuration (config.toml).

Codex stores MCP servers in ~/.codex/config.toml under an `mcp_servers`
table. This module merges the `[mcp_servers.spss]` entry without clobbering
the rest of the file, and creates a timestamped backup first.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from spss_mcp.claude_config import get_entrypoint_config
from spss_mcp.config import detect_capabilities, get_startup_timeout, get_timeout

_MCP_SECTION_RE = re.compile(r"(?ms)^\[mcp_servers\.spss\][^\n]*(?:\n(?!\[).*)*")


def get_codex_config_path() -> Path:
    """Return the default Codex config.toml path."""
    return Path.home() / ".codex" / "config.toml"


def _backup_config(path: Path) -> Path | None:
    """Create a timestamped backup of config.toml if it exists."""
    if not path.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.name}.backup.{timestamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def _toml_literal(value: str) -> str:
    """Quote a value as a TOML literal string (single quotes, no escaping)."""
    return "'" + value.replace("'", "''") + "'"


def build_codex_entry() -> dict:
    """Build the entry dict (command/args/env) for the Codex MCP server."""
    executable_command, executable_args = get_entrypoint_config()
    caps = detect_capabilities()
    spss_path = caps.get("spss_path")
    spss_install = (
        str(Path(spss_path).parent)
        if spss_path
        else "<replace-with-your-spss-install-dir>"
    )
    return {
        "command": executable_command,
        "args": executable_args,
        "env": {
            "SPSS_INSTALL_PATH": spss_install,
            "SPSS_TIMEOUT": str(get_timeout()),
            "SPSS_STARTUP_TIMEOUT": str(get_startup_timeout()),
        },
    }


def build_codex_server_block(entry: dict | None = None) -> str:
    """Render the `[mcp_servers.spss]` TOML block."""
    entry = entry or build_codex_entry()
    args_toml = ", ".join(f'"{a}"' for a in entry["args"])
    env_toml = (
        "{ "
        + ", ".join(
            f"{key} = {_toml_literal(value)}" for key, value in entry["env"].items()
        )
        + " }"
    )
    return (
        "[mcp_servers.spss]\n"
        f"command = {_toml_literal(entry['command'])}\n"
        f"args = [{args_toml}]\n"
        f"env = {env_toml}\n"
    )


def configure_codex_settings(config_path: Path | None = None) -> dict:
    """
    Merge the SPSS MCP entry into Codex config.toml and write the file.

    Returns a status payload describing what changed.
    """
    path = config_path or get_codex_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    existed = path.exists()
    content = path.read_text(encoding="utf-8") if existed else ""
    new_block = build_codex_server_block()

    match = _MCP_SECTION_RE.search(content)
    if match:
        previous = match.group(0).rstrip("\n")
        if previous == new_block.rstrip("\n"):
            status = "unchanged"
        else:
            content = _MCP_SECTION_RE.sub(new_block.rstrip("\n"), content, count=1)
            status = "updated"
    else:
        if content and not content.endswith("\n"):
            content += "\n"
        content += new_block
        status = "created"

    backup_path = _backup_config(path) if existed and status != "unchanged" else None

    if status != "unchanged":
        path.write_text(content, encoding="utf-8")

    return {
        "status": status,
        "config_path": str(path),
        "backup_path": str(backup_path) if backup_path else None,
        "entry": build_codex_entry(),
    }
