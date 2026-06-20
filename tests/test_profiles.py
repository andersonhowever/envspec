import pytest

from envspec import Config, Field, Profile, ValidationError


class C(Config):
    verify_ssl = Field(bool, default=False)
    api_token = Field(str, default="")
    log_level = Field(str, default="info")
    profiles = {
        "prod": Profile(overrides={"VERIFY_SSL": "true"}, require=["api_token"]),
        "dev": Profile(overrides={"LOG_LEVEL": "debug"}),
    }


def test_profile_override_applied():
    cfg = C.load(use_environ=False, profile="dev")
    assert cfg.log_level == "debug"


def test_prod_hardening_overrides_default():
    r = C.validate(use_environ=False, profile="prod", overrides={"API_TOKEN": "t"})
    assert r.ok and r.values["verify_ssl"] is True


def test_prod_requires_token():
    with pytest.raises(ValidationError) as exc:
        C.load(use_environ=False, profile="prod")
    assert "API_TOKEN" in exc.value.render()


def test_no_profile_uses_defaults():
    cfg = C.load(use_environ=False)
    assert cfg.verify_ssl is False and cfg.log_level == "info"
