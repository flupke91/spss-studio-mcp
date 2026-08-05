import asyncio
import json
from pathlib import Path

import pytest

from spss_mcp import server
from spss_mcp.config import detect_capabilities
from spss_mcp.spss_runner import run_syntax

requires_spss = pytest.mark.skipif(
    not detect_capabilities().get("spss"),
    reason="IBM SPSS Statistics is not installed on this machine",
)


MANIFEST_PATH = Path(__file__).parent / "fixtures" / "reproduction_manifest.json"
DATA_DIR = Path(__file__).resolve().parents[1] / "examples" / "data"


def _resolve_data_file(name: str) -> str:
    """Resolve a manifest data file against the bundled example datasets."""
    return str(DATA_DIR / name)


def test_reproduction_manifest_structure():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert len(manifest) == 10
    for case in manifest:
        assert "id" in case
        assert "file_path" in case
        assert "params" in case
        assert "execution_context" in case
        assert "expected_success" in case
        assert "required_output_markers" in case
        assert case.get("tool") or case.get("syntax_kind")


@requires_spss
def test_reproduction_manifest_cases_execute_successfully():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    from spss_mcp.spss_engine import get_engine

    engine = get_engine()
    try:
        _run_cases(manifest)
    finally:
        # Release the engine so the trial license seat is not held after the test.
        try:
            import asyncio

            asyncio.run(engine.stop())
        except Exception:
            pass


def _run_cases(manifest: list) -> None:
    import asyncio as _asyncio

    for case in manifest:
        if case.get("syntax_kind") == "raw":
            result = _asyncio.run(
                run_syntax(
                    case["params"]["syntax"],
                    data_file=_resolve_data_file(case["file_path"]),
                    filter_variable=case["execution_context"].get("filter_variable"),
                    select_if=case["execution_context"].get("select_if"),
                )
            )
            rendered = result.get("output_markdown") or ""
            if result.get("error"):
                rendered = f"Error: {result['error']}\n\n{rendered}"
        else:
            tool = getattr(server, case["tool"])
            rendered = _asyncio.run(
                tool(file_path=_resolve_data_file(case["file_path"]), **case["params"])
            )

        assert rendered.startswith("Error:") is False, (
            case["id"] + " failed with output:\n" + rendered[:4000]
        )
        for marker in case["required_output_markers"]:
            assert (
                marker in rendered
            ), f"{case['id']} missing marker: {marker}\n{rendered[:4000]}"
