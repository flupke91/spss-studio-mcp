"""Security layer for the SPSS MCP server (P4).

Provides:
* dangerous-syntax blocking (OS / file-system commands must not reach SPSS)
* a data-file path allowlist (env ``SPSS_ALLOWED_DIRS``, project ``examples``,
  and the system temp dir)
* an append-only JSONL audit log (env ``SPSS_AUDIT_LOG``)
* ``dry_run`` helpers so callers can validate without executing

The allowlist is intentionally permissive for the bundled example datasets and
temp outputs; production deployments should set ``SPSS_ALLOWED_DIRS``.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Commands that can touch the OS, other files, or the SPSS process itself.
# Matched at the start of a line to avoid false positives on variable names.
DANGEROUS_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"(?m)^\s*HOST\b", re.IGNORECASE),
    re.compile(r"(?m)^\s*ERASE\b", re.IGNORECASE),
    re.compile(r"(?m)^\s*DELETE\b.*\bFILE\b", re.IGNORECASE),
    re.compile(r"(?m)^\s*FILE\s+HANDLE\b", re.IGNORECASE),
    re.compile(r"(?m)^\s*INSERT\s+FILE\b", re.IGNORECASE),
    re.compile(r"(?m)^\s*SCRIPT\b", re.IGNORECASE),
    re.compile(r"(?m)^\s*CD\b", re.IGNORECASE),
    re.compile(r"(?m)^\s*SYSTEM\b", re.IGNORECASE),
)

DANGEROUS_LABELS: tuple[str, ...] = (
    "HOST",
    "ERASE",
    "DELETE FILE",
    "FILE HANDLE",
    "INSERT FILE",
    "SCRIPT",
    "CD",
    "SYSTEM",
)


def check_syntax_safety(syntax: str) -> list[str]:
    """Return the dangerous commands detected in ``syntax`` (empty = safe)."""
    hits = []
    for pattern, label in zip(DANGEROUS_PATTERNS, DANGEROUS_LABELS):
        if pattern.search(syntax):
            hits.append(label)
    return hits


def get_allowed_dirs() -> list[Path]:
    """Allowed locations for data files (env overrides + examples + temp)."""
    dirs: list[Path] = []
    env = os.environ.get("SPSS_ALLOWED_DIRS", "").strip()
    if env:
        for raw in env.split(";"):
            if raw.strip():
                dirs.append(Path(raw.strip()).resolve())
    dirs.append((_PROJECT_ROOT / "examples").resolve())
    dirs.append(Path(tempfile.gettempdir()).resolve())
    return dirs


def validate_data_file(path: str) -> Optional[str]:
    """Return an error message when ``path`` is unusable, else ``None``."""
    if not path:
        return None
    try:
        resolved = Path(path).resolve()
    except OSError as exc:
        return f"Invalid data file path {path!r}: {exc}"
    if not resolved.exists():
        return f"Data file does not exist: {path}"
    for allowed in get_allowed_dirs():
        try:
            resolved.relative_to(allowed)
            return None
        except ValueError:
            continue
    return (
        f"Data file is outside the allowed directories: {path}. "
        "Set SPSS_ALLOWED_DIRS to grant access."
    )


def get_audit_path() -> Path:
    """Path of the JSONL audit log (env override, default project logs/audit.jsonl)."""
    env = os.environ.get("SPSS_AUDIT_LOG", "").strip()
    if env:
        return Path(env)
    return _PROJECT_ROOT / "logs" / "audit.jsonl"


def audit(entry: dict) -> None:
    """Append one JSON line to the audit log (best-effort, never raises)."""
    try:
        path = get_audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            **entry,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Auditing must never break an analysis.
        pass


def summarize_syntax(syntax: str, limit: int = 200) -> str:
    """First command line of the syntax (for audit logs)."""
    first_line = next((ln.strip() for ln in syntax.splitlines() if ln.strip()), "")
    if len(first_line) > limit:
        return first_line[:limit] + "..."
    return first_line
