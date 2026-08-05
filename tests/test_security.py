import json
from pathlib import Path

import pytest

from spss_mcp import security

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_check_syntax_safety_allows_normal_syntax():
    syntax = "FREQUENCIES VARIABLES=gender.\nDESCRIPTIVES VARIABLES=score.\n"
    assert security.check_syntax_safety(syntax) == []


def test_check_syntax_safety_blocks_host():
    assert "HOST" in security.check_syntax_safety("HOST COMMAND 'dir'.\n")


def test_check_syntax_safety_blocks_erase_and_delete_file():
    assert "ERASE" in security.check_syntax_safety("ERASE FILE='x.sav'.\n")
    assert "DELETE FILE" in security.check_syntax_safety("DELETE FILE='x.sav'.\n")


def test_check_syntax_safety_blocks_file_handle_and_script():
    assert "FILE HANDLE" in security.check_syntax_safety("FILE HANDLE h NAME='x'.\n")
    assert "SCRIPT" in security.check_syntax_safety("SCRIPT 'x.py'.\n")


def test_check_syntax_safety_does_not_flag_variable_cd_in_expression():
    # "CD" only matched at the start of a line, not as a variable name
    syntax = "COMPUTE cd = 1.\n"
    assert security.check_syntax_safety(syntax) == []


def test_validate_data_file_allows_examples():
    example = PROJECT_ROOT / "examples" / "data" / "survey_study.sav"
    assert example.exists()
    assert security.validate_data_file(str(example)) is None


def test_validate_data_file_rejects_external_path():
    outside = Path.home() / "spss_studio_mcp_outside_test.sav"
    outside.write_bytes(b"")
    try:
        error = security.validate_data_file(str(outside))
        assert error is not None
        assert "outside the allowed directories" in error
    finally:
        outside.unlink(missing_ok=True)


def test_validate_data_file_rejects_missing_file():
    error = security.validate_data_file("C:/nope/missing.sav")
    assert error is not None
    assert "does not exist" in error


def test_audit_appends_json_lines(tmp_path, monkeypatch):
    log = tmp_path / "audit.jsonl"
    monkeypatch.setenv("SPSS_AUDIT_LOG", str(log))
    security.audit({"event": "test", "value": 1})
    security.audit({"event": "test", "value": 2})
    lines = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [line["value"] for line in lines] == [1, 2]
    assert "ts" in lines[0]


def test_summarize_syntax_takes_first_command():
    assert (
        security.summarize_syntax("FREQUENCIES VARIABLES=x.\nDESCRIPTIVES.")
        == "FREQUENCIES VARIABLES=x."
    )
    assert security.summarize_syntax("x" * 300) == "x" * 200 + "..."
