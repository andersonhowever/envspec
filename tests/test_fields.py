import pytest

from envspec import Field, SpecError
from envspec.fields import _MISSING


def test_bool_coercion():
    f = Field(bool)
    assert f.coerce("true") is True
    assert f.coerce("0") is False
    with pytest.raises(ValueError):
        f.coerce("maybe")


def test_int_coercion_and_bounds():
    f = Field(int, min=1, max=300)
    v, p = f.process("30")
    assert v == 30 and p is None
    _, p = f.process("999")
    assert p is not None and "максимум" in p.expected


def test_list_coercion():
    assert Field("list").coerce("a, b ,, c") == ["a", "b", "c"]


def test_json_coercion():
    f = Field("json")
    assert f.coerce('{"a": 1}') == {"a": 1}
    with pytest.raises(ValueError):
        f.coerce("{bad}")


def test_required_missing_produces_problem():
    f = Field(str, required=True, doc="Base API URL")
    f.name = "api_url"
    v, p = f.process(_MISSING)
    assert v is None and p is not None and p.name == "API_URL" and "как починить" in p.render()


def test_required_with_default_is_spec_error():
    with pytest.raises(SpecError):
        Field(str, required=True, default="x")


def test_choices():
    _, p = Field(str, choices=["a", "b"]).process("c")
    assert p is not None


def test_secret_masked_in_render():
    f = Field(str, secret=True, choices=["a"])
    f.name = "token"
    _, p = f.process("supersecret")
    assert "supersecret" not in p.render() and "***" in p.render()


def test_float_coercion():
    f = Field(float)
    assert f.coerce("3.14") == 3.14
    with pytest.raises(ValueError):
        f.coerce("nan?")


def test_list_generic_alias():

    assert Field(list[str]).coerce("a,b") == ["a", "b"]
    assert Field(list[str]).coerce("a,b") == ["a", "b"]


def test_custom_env_name():
    f = Field(str, env="MY_CUSTOM_URL")
    f.name = "api_url"
    assert f.env_name == "MY_CUSTOM_URL"


def test_default_env_name_uppercases():
    f = Field(str)
    f.name = "api_url"
    assert f.env_name == "API_URL"


def test_required_empty_string_is_missing():
    f = Field(str, required=True, doc="Base API URL")
    f.name = "api_url"
    v, p = f.process("   ")
    assert v is None and p is not None and "непустая строка" in p.expected


def test_str_length_bounds():
    f = Field(str, min=2, max=4)
    assert f.process("abc")[1] is None
    _, p = f.process("x")
    assert p is not None and "минимум" in p.expected


def test_non_required_missing_uses_default():
    f = Field(int, default=42)
    f.name = "timeout_s"
    v, p = f.process(_MISSING)
    assert v == 42 and p is None
