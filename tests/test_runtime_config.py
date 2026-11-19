import importlib

from spss_mcp import config


def test_get_timeout_rejects_invalid_values(monkeypatch):
    monkeypatch.setenv("SPSS_TIMEOUT", "abc")
    assert config.get_timeout() == 120

    monkeypatch.setenv("SPSS_TIMEOUT", "0")
    assert config.get_timeout() == 120

    monkeypatch.setenv("SPSS_TIMEOUT", "600")
    assert config.get_timeout() == 600


def test_get_startup_timeout_rejects_invalid_values(monkeypatch):
    monkeypatch.setenv("SPSS_STARTUP_TIMEOUT", "abc")
    assert config.get_startup_timeout() == 300

    monkeypatch.setenv("SPSS_STARTUP_TIMEOUT", "0")
    assert config.get_startup_timeout() == 300

    monkeypatch.setenv("SPSS_STARTUP_TIMEOUT", "900")
    assert config.get_startup_timeout() == 900


def test_get_runtime_config_includes_effective_timeout(monkeypatch):
    monkeypatch.setenv("SPSS_TIMEOUT", "321")
    monkeypatch.setenv("SPSS_STARTUP_TIMEOUT", "654")
    runtime = config.get_runtime_config()
    assert runtime["timeout"] == 321
    assert runtime["startup_timeout"] == 654
    assert "temp_dir" in runtime
    assert "results_dir" in runtime


def test_find_spss_via_filesystem_includes_spss_32(tmp_path, monkeypatch):
    spss_32 = tmp_path / "32"
    spss_32.mkdir()
    exe = spss_32 / "stats.exe"
    exe.write_bytes(b"")

    orig_path = config.Path

    def patched_path(raw):
        if raw == r"C:\Program Files\IBM\SPSS Statistics":
            return tmp_path
        return orig_path(raw)

    monkeypatch.setattr(config, "Path", patched_path)
    assert config._find_spss_via_filesystem() == str(exe)
