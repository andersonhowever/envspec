"""Тесты pydantic-интеропа (extra). См. SPEC.md §7."""

import pytest

from envspec import Config, Field
from envspec.contrib.pydantic import to_pydantic

pydantic = pytest.importorskip("pydantic")


class Cfg(Config):
    api_url = Field(str, required=True, doc="Base API URL")
    timeout_s = Field(int, default=30, min=1, max=300)
    verify_ssl = Field(bool, default=True)
    api_token = Field(str, secret=True)
    tags = Field("list")
    level = Field(str, choices=["debug", "info"], default="info")
    name = Field(str, min=2, max=4)


def test_field_names_are_env_names():
    model = to_pydantic(Cfg)
    assert set(model.model_fields) == {
        "API_URL",
        "TIMEOUT_S",
        "VERIFY_SSL",
        "API_TOKEN",
        "TAGS",
        "LEVEL",
        "NAME",
    }


def test_required_and_defaults():
    model = to_pydantic(Cfg)
    m = model(API_URL="https://x")
    assert m.API_URL == "https://x"
    assert m.TIMEOUT_S == 30
    assert m.VERIFY_SSL is True
    assert m.LEVEL == "info"
    assert m.TAGS is None  # optional, нет default
    with pytest.raises(pydantic.ValidationError):
        model()  # API_URL обязателен


def test_numeric_bounds():
    model = to_pydantic(Cfg)
    assert model(API_URL="x", TIMEOUT_S=1).TIMEOUT_S == 1
    with pytest.raises(pydantic.ValidationError):
        model(API_URL="x", TIMEOUT_S=0)
    with pytest.raises(pydantic.ValidationError):
        model(API_URL="x", TIMEOUT_S=301)


def test_str_length_bounds():
    model = to_pydantic(Cfg)
    assert model(API_URL="x", NAME="abcd").NAME == "abcd"
    with pytest.raises(pydantic.ValidationError):
        model(API_URL="x", NAME="a")
    with pytest.raises(pydantic.ValidationError):
        model(API_URL="x", NAME="abcde")


def test_choices_literal():
    model = to_pydantic(Cfg)
    assert model(API_URL="x", LEVEL="debug").LEVEL == "debug"
    with pytest.raises(pydantic.ValidationError):
        model(API_URL="x", LEVEL="trace")


def test_list_type():
    model = to_pydantic(Cfg)
    assert model(API_URL="x", TAGS=["a", "b"]).TAGS == ["a", "b"]


def test_secret_and_doc_metadata():
    model = to_pydantic(Cfg)
    assert model.model_fields["API_TOKEN"].json_schema_extra == {"secret": True}
    assert model.model_fields["API_URL"].description == "Base API URL"


def test_model_name():
    assert to_pydantic(Cfg).__name__ == "CfgModel"
    assert to_pydantic(Cfg, name="Custom").__name__ == "Custom"


def test_explicit_env_alias():
    class WithEnv(Config):
        host = Field(str, env="DB_HOST", default="localhost")

    model = to_pydantic(WithEnv)
    assert "DB_HOST" in model.model_fields
    assert model(DB_HOST="db").DB_HOST == "db"
    assert model().DB_HOST == "localhost"
