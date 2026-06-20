"""Field — описание одной переменной окружения. См. SPEC.md §1."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from envspec.errors import Problem, SpecError

_MISSING = object()
_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}


def _is_list_type(t: Any) -> bool:
    """True для list, "list" и generic-алиасов вида list[str]."""
    return t == "list" or t is list or getattr(t, "__origin__", None) is list


class Field:
    """Описание переменной. Поведение задано в SPEC.md §1."""

    def __init__(
        self,
        type: Any,
        *,
        required: bool = False,
        default: Any = _MISSING,
        doc: str = "",
        env: str | None = None,
        secret: bool = False,
        deprecated: bool = False,
        min: float | None = None,
        max: float | None = None,
        choices: Sequence[Any] | None = None,
        example: str | None = None,
    ) -> None:
        if required and default is not _MISSING:
            raise SpecError("Field не может быть одновременно required и иметь default")
        self.type = type
        self.required = required
        self.default = default
        self.doc = doc
        self.env = env
        self.secret = secret
        self.deprecated = deprecated
        self.min = min
        self.max = max
        self.choices = choices
        self.example = example
        self.name = ""

    @property
    def env_name(self) -> str:
        return self.env or self.name.upper()

    @property
    def has_default(self) -> bool:
        return self.default is not _MISSING

    @property
    def type_name(self) -> str:
        t = self.type
        if isinstance(t, str):
            return t
        if _is_list_type(t):
            return "list[str]"
        return getattr(t, "__name__", str(t))

    def coerce(self, raw: str) -> Any:
        t = self.type
        if t is bool:
            low = raw.strip().lower()
            if low in _BOOL_TRUE:
                return True
            if low in _BOOL_FALSE:
                return False
            raise ValueError("ожидался bool (1/0/true/false/yes/no/on/off)")
        if t is int:
            try:
                return int(raw)
            except ValueError:
                raise ValueError("ожидалось целое число") from None
        if t is float:
            try:
                return float(raw)
            except ValueError:
                raise ValueError("ожидалось число") from None
        if t == "json":
            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError(f"невалидный JSON: {e.msg} (поз. {e.pos})") from None
        if _is_list_type(t):
            return [p.strip() for p in raw.split(",") if p.strip()]
        return raw

    def validate_value(self, value: Any) -> str | None:
        if self.choices is not None and value not in self.choices:
            return f"допустимо: {self.choices}"
        if self.min is not None or self.max is not None:
            measure = value if isinstance(value, (int, float)) else len(value)
            if self.min is not None and measure < self.min:
                return f"минимум: {self.min}"
            if self.max is not None and measure > self.max:
                return f"максимум: {self.max}"
        return None

    def process(self, raw: Any, required: bool | None = None) -> tuple[Any, Problem | None]:
        """Вернуть (значение, проблема|None). required переопределяет self.required."""
        eff_required = self.required if required is None else required
        is_empty = raw is not _MISSING and isinstance(raw, str) and raw.strip() == ""
        if raw is _MISSING or is_empty:
            if eff_required:
                expected = f"непустая строка ({self.doc})" if self.doc else "непустое значение"
                return None, Problem(
                    name=self.env_name,
                    summary="обязательная переменная не задана",
                    expected=expected,
                    fix=f"добавьте в .env строку  {self.env_name}=...",
                    secret=self.secret,
                )
            return (self.default if self.has_default else None), None
        try:
            value = self.coerce(str(raw))
        except ValueError as e:
            return None, Problem(
                name=self.env_name,
                summary="неверный формат значения",
                expected=str(e),
                got=str(raw),
                fix=f"исправьте значение {self.env_name}",
                secret=self.secret,
            )
        err = self.validate_value(value)
        if err is not None:
            return None, Problem(
                name=self.env_name,
                summary="значение вне допустимого",
                expected=err,
                got=str(raw),
                fix=f"приведите {self.env_name} к допустимому значению",
                secret=self.secret,
            )
        return value, None
