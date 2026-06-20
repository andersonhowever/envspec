"""Pydantic-интероп: Config → pydantic v2 модель. См. SPEC.md §7.

Направление одно (envspec → pydantic): envspec остаётся источником истины.
Требует extra: ``pip install 'envspec[pydantic]'``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from envspec.config import Config
from envspec.errors import SpecError
from envspec.fields import Field, _is_list_type

if TYPE_CHECKING:
    from pydantic import BaseModel


def _py_type(field: Field) -> Any:
    """Тип значения envspec → аннотация Python для pydantic."""
    t = field.type
    if t == "json":
        return Any
    if _is_list_type(t):
        return list[str]
    if t in (str, int, float, bool):
        return t
    return Any


def to_pydantic(config_cls: type[Config], *, name: str | None = None) -> type[BaseModel]:
    """Построить pydantic v2 модель из определения ``Config``. См. SPEC.md §7.

    Имена полей модели = env-имена полей Config (``api_url`` → ``API_URL``),
    типы/required/default/границы/choices/secret переносятся по правилам §7.
    """
    try:
        import pydantic
    except ImportError as e:  # pragma: no cover - сработает только без extra
        raise SpecError("pydantic-интероп требует extra: pip install 'envspec[pydantic]'") from e

    fields: dict[str, Any] = {}
    for field in config_cls.__fields__.values():
        tp = _py_type(field)
        if field.choices is not None:
            # динамический Literal из choices (рантайм-построение типа)
            tp = Literal[tuple(field.choices)]

        kwargs: dict[str, Any] = {}
        if field.doc:
            kwargs["description"] = field.doc
        is_numeric = field.type in (int, float)
        if field.min is not None:
            kwargs["ge" if is_numeric else "min_length"] = field.min
        if field.max is not None:
            kwargs["le" if is_numeric else "max_length"] = field.max
        if field.secret:
            kwargs["json_schema_extra"] = {"secret": True}

        if field.required:
            default: Any = ...
        elif field.has_default:
            default = field.default
        else:
            default = None
            tp = Optional[tp]  # noqa: UP045 — рантайм-построение типа, py3.9-safe

        fields[field.env_name] = (tp, pydantic.Field(default, **kwargs))

    model_name = name or f"{config_cls.__name__}Model"
    return pydantic.create_model(model_name, **fields)
