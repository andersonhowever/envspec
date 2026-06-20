"""Config — сбор полей, загрузка, валидация, профили. См. SPEC.md §2."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as _dc_field
from typing import Any

from envspec import sources
from envspec.errors import Problem, ValidationError
from envspec.fields import _MISSING, Field
from envspec.profiles import Profile


@dataclass
class Result:
    ok: bool
    values: dict[str, Any]
    problems: list[Problem]
    warnings: list[str]
    origins: dict[str, str] = _dc_field(default_factory=dict)


class _ConfigMeta(type):
    __fields__: dict[str, Field]
    __profiles__: dict[str, Profile]

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        ns: dict[str, Any],
    ) -> _ConfigMeta:
        fields: dict[str, Field] = {}
        profs: dict[str, Profile] = {}
        for base in bases:
            fields.update(getattr(base, "__fields__", {}))
            profs.update(getattr(base, "__profiles__", {}))
        for key, value in ns.items():
            if isinstance(value, Field):
                value.name = key
                fields[key] = value
        profs.update(ns.get("profiles", {}) or {})
        cls = super().__new__(mcls, name, bases, ns)
        cls.__fields__ = fields
        cls.__profiles__ = profs
        return cls


class Config(metaclass=_ConfigMeta):
    """Базовый класс конфига."""

    __fields__: dict[str, Field] = {}
    __profiles__: dict[str, Profile] = {}

    def __init__(self, values: dict[str, Any]) -> None:
        for key in type(self).__fields__:
            setattr(self, key, values.get(key))

    @classmethod
    def validate(
        cls,
        *,
        dotenv_path: str = ".env",
        use_environ: bool = True,
        overrides: dict[str, str] | None = None,
        profile: str | None = None,
        yaml_path: str | None = None,
        json_path: str | None = None,
    ) -> Result:
        prof = cls.__profiles__.get(profile) if profile else None
        prof_overrides = prof.overrides if prof else None
        extra_required = set(prof.require) if prof else set()

        layers = sources.layered(
            dotenv_path,
            use_environ=use_environ,
            yaml_path=yaml_path,
            json_path=json_path,
            overrides=overrides,
            profile_overrides=prof_overrides,
        )
        raw, origin = sources.merge_with_origin(layers)

        values: dict[str, Any] = {}
        problems: list[Problem] = []
        warnings: list[str] = []
        origins: dict[str, str] = {}
        for key, fld in cls.__fields__.items():
            present = raw.get(fld.env_name, _MISSING)
            if fld.deprecated and present is not _MISSING:
                warnings.append(f"{fld.env_name} устарела — см. миграции (envspec migrate)")
            required = fld.required or (key in extra_required)
            value, problem = fld.process(present, required=required)
            origins[key] = origin.get(fld.env_name, "default")
            if problem is not None:
                problems.append(problem)
            else:
                values[key] = value
        return Result(
            ok=not problems, values=values, problems=problems, warnings=warnings, origins=origins
        )

    @classmethod
    def load(
        cls,
        *,
        dotenv_path: str = ".env",
        use_environ: bool = True,
        overrides: dict[str, str] | None = None,
        profile: str | None = None,
        yaml_path: str | None = None,
        json_path: str | None = None,
    ) -> Config:
        result = cls.validate(
            dotenv_path=dotenv_path,
            use_environ=use_environ,
            overrides=overrides,
            profile=profile,
            yaml_path=yaml_path,
            json_path=json_path,
        )
        if not result.ok:
            raise ValidationError(result.problems)
        return cls(result.values)
