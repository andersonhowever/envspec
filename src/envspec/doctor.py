"""Диагностика окружения. См. SPEC.md §4 (doctor)."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as _dc_field
from typing import Any

from envspec.config import Config
from envspec.fields import Field


@dataclass
class Row:
    name: str
    status: str  # "ok" | "missing" | "error" | "deprecated"
    value: str  # уже замаскировано если secret
    origin: str  # default | .env | environ | profile | ...
    message: str = ""


@dataclass
class DoctorReport:
    ok: bool
    rows: list[Row] = _dc_field(default_factory=list)
    warnings: list[str] = _dc_field(default_factory=list)


def _mask(fld: Field, value: Any) -> str:
    if value is None:
        return ""
    if fld.secret:
        return "***"
    return str(value)


def diagnose(config_cls: type[Config], **kw: Any) -> DoctorReport:
    """Построить диагностику поверх Config.validate (не дублируем логику)."""
    result = config_cls.validate(**kw)
    problems = {p.name: p for p in result.problems}
    rows: list[Row] = []
    for key, fld in config_cls.__fields__.items():
        origin = result.origins.get(key, "default")
        if fld.env_name in problems:
            p = problems[fld.env_name]
            rows.append(Row(fld.env_name, "error", "", origin, p.summary + " — " + p.fix))
        elif fld.deprecated and origin != "default":
            rows.append(
                Row(
                    fld.env_name,
                    "deprecated",
                    _mask(fld, result.values.get(key)),
                    origin,
                    "устарела — см. envspec migrate",
                )
            )
        elif origin == "default" and not fld.has_default and not fld.required:
            rows.append(Row(fld.env_name, "missing", "", origin, "не задана (нет default)"))
        else:
            rows.append(Row(fld.env_name, "ok", _mask(fld, result.values.get(key)), origin))
    return DoctorReport(ok=result.ok, rows=rows, warnings=result.warnings)


_SYMBOL = {"ok": "✓", "missing": "·", "error": "✗", "deprecated": "⚠"}


def render_text(report: DoctorReport) -> str:
    lines = []
    for r in report.rows:
        sym = _SYMBOL.get(r.status, "?")
        base = f"{sym} {r.name} = {r.value or '∅'}  [{r.origin}]"
        if r.message:
            base += f"\n    {r.message}"
        lines.append(base)
    lines.append("")
    lines.append("итог: " + ("OK" if report.ok else "есть проблемы"))
    return "\n".join(lines)


def to_dict(report: DoctorReport) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "warnings": report.warnings,
        "vars": [
            {
                "name": r.name,
                "status": r.status,
                "value": r.value,
                "origin": r.origin,
                "message": r.message,
            }
            for r in report.rows
        ],
    }
