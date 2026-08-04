from pathlib import Path

from spss_mcp import codex_config

ENTRY = {
    "command": "spss-studio-mcp",
    "args": ["serve", "--transport", "stdio"],
    "env": {
        "SPSS_INSTALL_PATH": r"E:\spss",
        "SPSS_TIMEOUT": "300",
        "SPSS_STARTUP_TIMEOUT": "600",
    },
}


def test_configure_codex_creates_new_config(monkeypatch, tmp_path):
    monkeypatch.setattr(codex_config, "build_codex_entry", lambda: ENTRY)

    config_path = tmp_path / "config.toml"
    result = codex_config.configure_codex_settings(config_path)

    assert result["status"] == "created"
    assert result["backup_path"] is None
    assert result["entry"] == ENTRY
    text = config_path.read_text(encoding="utf-8")
    assert "[mcp_servers.spss]" in text
    assert "spss-studio-mcp" in text
    assert "serve" in text


def test_configure_codex_merges_existing_config(monkeypatch, tmp_path):
    monkeypatch.setattr(codex_config, "build_codex_entry", lambda: ENTRY)

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'model = "gpt-5.2"\n[experimental]\nenabled = true\n',
        encoding="utf-8",
    )

    result = codex_config.configure_codex_settings(config_path)

    assert result["status"] == "created"
    assert Path(result["backup_path"]).exists()
    text = config_path.read_text(encoding="utf-8")
    assert 'model = "gpt-5.2"' in text
    assert "[experimental]" in text
    assert "[mcp_servers.spss]" in text
    assert "spss-studio-mcp" in text


def test_configure_codex_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setattr(codex_config, "build_codex_entry", lambda: ENTRY)

    config_path = tmp_path / "config.toml"
    first = codex_config.configure_codex_settings(config_path)
    assert first["status"] == "created"

    second = codex_config.configure_codex_settings(config_path)
    assert second["status"] == "unchanged"
    assert second["backup_path"] is None


def test_build_codex_server_block_renders_entry(monkeypatch):
    monkeypatch.setattr(codex_config, "build_codex_entry", lambda: ENTRY)
    block = codex_config.build_codex_server_block()
    assert block.startswith("[mcp_servers.spss]")
    assert "command = 'spss-studio-mcp'" in block
    assert "SPSS_INSTALL_PATH = 'E:\\spss'" in block
