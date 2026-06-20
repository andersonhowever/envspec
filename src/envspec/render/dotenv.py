""".env.example генератор. См. SPEC.md §6."""

from __future__ import annotations

from envspec.config import Config


def render(config_cls: type[Config]) -> str:
    """Сгенерировать содержимое .env.example (детерминированно)."""
    lines = []
    for fld in config_cls.__fields__.values():
        flags = []
        if fld.required:
            flags.append("required")
        if fld.deprecated:
            flags.append("deprecated")
        if fld.secret:
            flags.append("secret")
        flag_str = f" ({', '.join(flags)})" if flags else ""
        doc = fld.doc or fld.env_name
        lines.append(f"# {doc}{flag_str}")
        if fld.secret:
            lines.append(f"{fld.env_name}=        # secret — заполните вручную")
        elif fld.example is not None:
            lines.append(f"{fld.env_name}={fld.example}")
        elif fld.has_default and fld.default not in (None, ""):
            lines.append(f"{fld.env_name}={fld.default}")
        else:
            lines.append(f"{fld.env_name}=")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
