"""Источники значений и приоритет слияния. См. SPEC.md §2.

Приоритет (низший→высший): .env → json → yaml → environ → overrides → profile.
YAML требует extra `envspec[yaml]`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from envspec.errors import SourceError


def parse_dotenv(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        result[key] = value
    return result


def load_dotenv_file(path: str = ".env") -> dict[str, str]:
    p = Path(path)
    return parse_dotenv(p.read_text(encoding="utf-8")) if p.exists() else {}


def _flatten(d: dict[str, Any]) -> dict[str, str]:
    return {str(k): "" if v is None else str(v) for k, v in d.items()}


def load_json_file(path: str) -> dict[str, str]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SourceError(f"не удалось прочитать JSON {path}: {e.msg} (поз. {e.pos})") from None
    if not isinstance(data, dict):
        raise SourceError(f"JSON {path} должен быть объектом верхнего уровня")
    return _flatten(data)


def load_yaml_file(path: str) -> dict[str, str]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        raise SourceError("YAML-источник требует extra: pip install 'envspec[yaml]'") from None
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise SourceError(f"не удалось прочитать YAML {path}: {e}") from None
    if not isinstance(data, dict):
        raise SourceError(f"YAML {path} должен быть отображением верхнего уровня")
    return _flatten(data)


def collect(
    dotenv_path: str = ".env",
    *,
    use_environ: bool = True,
    overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    """Простое слияние (низший→высший): .env → environ → overrides."""
    merged: dict[str, str] = {}
    merged.update(load_dotenv_file(dotenv_path))
    if use_environ:
        merged.update(os.environ)
    if overrides:
        merged.update(overrides)
    return merged


def layered(
    dotenv_path: str = ".env",
    *,
    use_environ: bool = True,
    yaml_path: str | None = None,
    json_path: str | None = None,
    overrides: dict[str, str] | None = None,
    profile_overrides: dict[str, str] | None = None,
) -> list[tuple[str, dict[str, str]]]:
    """Список слоёв (origin, dict) в порядке возрастания приоритета."""
    layers: list[tuple[str, dict[str, str]]] = [(".env", load_dotenv_file(dotenv_path))]
    if json_path:
        layers.append(("json", load_json_file(json_path)))
    if yaml_path:
        layers.append(("yaml", load_yaml_file(yaml_path)))
    if use_environ:
        layers.append(("environ", dict(os.environ)))
    if overrides:
        layers.append(("override", dict(overrides)))
    if profile_overrides:
        layers.append(("profile", dict(profile_overrides)))
    return layers


def merge_with_origin(
    layers: list[tuple[str, dict[str, str]]],
) -> tuple[dict[str, str], dict[str, str]]:
    """Слить слои; вернуть (значения, откуда пришло каждое значение)."""
    merged: dict[str, str] = {}
    origin: dict[str, str] = {}
    for name, d in layers:
        for k, v in d.items():
            merged[k] = v
            origin[k] = name
    return merged, origin
