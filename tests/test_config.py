import pytest

from envspec import Config, Field, ValidationError


class AppConfig(Config):
    api_url = Field(str, required=True, doc="Base API URL")
    timeout_s = Field(int, default=30, min=1, max=300)
    verify_ssl = Field(bool, default=True)
    api_token = Field(str, secret=True, default="")


def test_fields_collected_in_order():
    assert list(AppConfig.__fields__) == ["api_url", "timeout_s", "verify_ssl", "api_token"]


def test_load_ok(monkeypatch):
    cfg = AppConfig.load(
        use_environ=False, overrides={"API_URL": "https://api.example.com", "TIMEOUT_S": "10"}
    )
    assert (
        cfg.api_url == "https://api.example.com" and cfg.timeout_s == 10 and cfg.verify_ssl is True
    )


def test_missing_required_raises_with_all_problems():
    with pytest.raises(ValidationError) as exc:
        AppConfig.load(use_environ=False, overrides={"TIMEOUT_S": "999"})
    r = exc.value.render()
    assert "API_URL" in r and "TIMEOUT_S" in r


def test_environ_overrides_dotenv(tmp_path, monkeypatch):
    ef = tmp_path / ".env"
    ef.write_text("API_URL=https://from-dotenv\n", encoding="utf-8")
    monkeypatch.setenv("API_URL", "https://from-environ")
    cfg = AppConfig.load(dotenv_path=str(ef))
    assert cfg.api_url == "https://from-environ"


def test_validate_returns_result_without_raising():
    r = AppConfig.validate(use_environ=False, overrides={})
    assert r.ok is False and any(p.name == "API_URL" for p in r.problems)


def test_empty_required_env_var_rejected():
    with pytest.raises(ValidationError) as exc:
        AppConfig.load(use_environ=False, overrides={"API_URL": ""})
    assert "API_URL" in exc.value.render()


class DeprecatedConfig(Config):
    api_url = Field(str, required=True)
    old_flag = Field(str, deprecated=True, default="")


def test_deprecated_var_produces_warning():
    r = DeprecatedConfig.validate(
        use_environ=False, overrides={"API_URL": "https://x", "OLD_FLAG": "1"}
    )
    assert r.ok is True and any("OLD_FLAG" in w for w in r.warnings)


def test_deprecated_var_absent_no_warning():
    r = DeprecatedConfig.validate(use_environ=False, overrides={"API_URL": "https://x"})
    assert r.warnings == []
