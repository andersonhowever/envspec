"""Миграции конфига между версиями. См. SPEC.md §5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from envspec.errors import MigrationError


@dataclass
class Op:
    kind: str  # "rename" | "transform" | "deprecate"
    old: str
    new: str | None = None
    fn: Callable[[str], str] | None = None
    reason: str = ""


class Migration:
    """Набор операций для перехода между версиями."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.ops: list[Op] = []

    def rename(self, old: str, new: str) -> Migration:
        self.ops.append(Op("rename", old, new))
        return self

    def transform(self, old: str, new: str, fn: Callable[[str], str]) -> Migration:
        self.ops.append(Op("transform", old, new, fn=fn))
        return self

    def deprecate(self, name: str, reason: str = "") -> Migration:
        self.ops.append(Op("deprecate", name, reason=reason))
        return self


_REGISTRY: list[Migration] = []


def migration(label: str) -> Callable[[Callable[[Migration], None]], Callable[[Migration], None]]:
    """Декоратор: регистрирует миграцию. Тело получает builder `m`."""

    def deco(fn: Callable[[Migration], None]) -> Callable[[Migration], None]:
        m = Migration(label)
        fn(m)
        _REGISTRY.append(m)
        return fn

    return deco


def registered() -> list[Migration]:
    return list(_REGISTRY)


def clear_registry() -> None:
    _REGISTRY.clear()


def rename_map(migrations: list[Migration] | None = None) -> dict[str, str]:
    """Сводная карта переименований old->new по всем операциям rename/transform."""
    migrations = registered() if migrations is None else migrations
    result: dict[str, str] = {}
    for m in migrations:
        for op in m.ops:
            if op.kind in ("rename", "transform") and op.new:
                result[op.old] = op.new
    return result


def plan(env: dict[str, str], migrations: list[Migration] | None = None) -> list[str]:
    """Человекочитаемый план изменений (без применения)."""
    _, changes = apply(env, migrations)
    return changes


def apply(
    env: dict[str, str], migrations: list[Migration] | None = None
) -> tuple[dict[str, str], list[str]]:
    """Применить миграции к набору переменных. Вернуть (новый_набор, список_изменений)."""
    migrations = registered() if migrations is None else migrations
    result = dict(env)
    changes: list[str] = []
    for m in migrations:
        for op in m.ops:
            if op.kind == "rename":
                assert op.new is not None  # гарантировано Migration.rename
                if op.old in result:
                    if op.new in result:
                        raise MigrationError(
                            f"[{m.label}] нельзя переименовать {op.old}→{op.new}: "
                            f"{op.new} уже задана"
                        )
                    result[op.new] = result.pop(op.old)
                    changes.append(f"переименовано: {op.old} → {op.new}")
            elif op.kind == "transform":
                assert op.new is not None  # гарантировано Migration.transform
                if op.old in result:
                    old_val = result.pop(op.old)
                    new_val = op.fn(old_val) if op.fn else old_val
                    result[op.new] = new_val
                    changes.append(f"преобразовано: {op.old}={old_val} → {op.new}={new_val}")
            elif op.kind == "deprecate" and op.old in result:
                result.pop(op.old)
                suffix = f" ({op.reason})" if op.reason else ""
                changes.append(f"удалено устаревшее: {op.old}{suffix}")
    return result, changes
