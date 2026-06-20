"""Markdown-дока по переменным. См. SPEC.md §6."""

from __future__ import annotations

from envspec.config import Config


def render(config_cls: type[Config]) -> str:
    """Markdown-таблица всех переменных (детерминированно). Секреты не раскрываются."""
    header = (
        "| Переменная | Тип | Обязательна | Default | Secret | Описание |\n"
        "|---|---|---|---|---|---|"
    )
    rows = [header]
    for fld in config_cls.__fields__.values():
        if fld.secret:
            default = "—"
        elif fld.has_default and fld.default is not None:
            default = f"`{fld.default}`"
        else:
            default = "—"
        required = "да" if fld.required else "нет"
        secret = "да" if fld.secret else "нет"
        doc = fld.doc or ""
        if fld.deprecated:
            doc = (doc + " (deprecated)").strip()
        rows.append(
            f"| `{fld.env_name}` | {fld.type_name} | {required} | {default} | {secret} | {doc} |"
        )
    return "\n".join(rows) + "\n"
