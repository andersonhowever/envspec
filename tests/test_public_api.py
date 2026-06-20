"""Заморозка публичного API (SPEC §9). Падение здесь = осознанное ломающее изменение.

Если меняешь что-то тут — это semver-major; обнови SPEC §9 и CHANGELOG в том же PR.
"""

import inspect

import envspec
from envspec.config import Result
from envspec.contrib.pydantic import to_pydantic
from envspec.errors import Problem


def _params(func):
    return [p for p in inspect.signature(func).parameters if p not in ("self", "cls")]


def test_top_level_exports_frozen():
    assert envspec.__all__ == [
        "Config",
        "Field",
        "Profile",
        "migration",
        "EnvspecError",
        "SpecError",
        "ValidationError",
        "SourceError",
        "MigrationError",
    ]
    for name in envspec.__all__:
        assert hasattr(envspec, name), name


def test_version_exposed():
    assert isinstance(envspec.__version__, str)


def test_field_signature_frozen():
    assert _params(envspec.Field.__init__) == [
        "type",
        "required",
        "default",
        "doc",
        "env",
        "secret",
        "deprecated",
        "min",
        "max",
        "choices",
        "example",
    ]


def test_config_entrypoints_frozen():
    expected = ["dotenv_path", "use_environ", "overrides", "profile", "yaml_path", "json_path"]
    assert _params(envspec.Config.load) == expected
    assert _params(envspec.Config.validate) == expected


def test_result_and_problem_shape_frozen():
    assert list(Result.__dataclass_fields__) == ["ok", "values", "problems", "warnings", "origins"]
    assert list(Problem.__dataclass_fields__) == [
        "name",
        "summary",
        "expected",
        "got",
        "fix",
        "secret",
    ]


def test_profile_and_migration_and_pydantic_frozen():
    assert _params(envspec.Profile.__init__) == ["overrides", "require"]
    assert _params(envspec.migration) == ["label"]
    assert _params(to_pydantic) == ["config_cls", "name"]


def test_exception_hierarchy_frozen():
    for exc in (
        envspec.SpecError,
        envspec.ValidationError,
        envspec.SourceError,
        envspec.MigrationError,
    ):
        assert issubclass(exc, envspec.EnvspecError)


def test_envspec_profile_env_selects_profile(monkeypatch):
    class Cfg(envspec.Config):
        verify_ssl = envspec.Field(bool, default=False)
        profiles = {"prod": envspec.Profile(overrides={"VERIFY_SSL": "true"})}

    # без env и без аргумента — дефолт
    monkeypatch.delenv("ENVSPEC_PROFILE", raising=False)
    assert Cfg.validate(use_environ=False).values["verify_ssl"] is False

    # ENVSPEC_PROFILE выбирает профиль, когда аргумент не передан
    monkeypatch.setenv("ENVSPEC_PROFILE", "prod")
    assert Cfg.validate(use_environ=False).values["verify_ssl"] is True

    # явный аргумент имеет приоритет над env
    assert Cfg.validate(use_environ=False, profile="dev").values["verify_ssl"] is False
