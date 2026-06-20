"""Сравнение двух наборов конфигов. См. SPEC.md §4 (diff)."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as _dc_field
from typing import Any


@dataclass
class DiffResult:
    added: dict[str, str] = _dc_field(default_factory=dict)
    removed: dict[str, str] = _dc_field(default_factory=dict)
    changed: dict[str, tuple[str, str]] = _dc_field(default_factory=dict)  # name -> (old, new)
    renamed: dict[str, str] = _dc_field(default_factory=dict)  # old -> new

    @property
    def empty(self) -> bool:
        return not (self.added or self.removed or self.changed or self.renamed)


def diff_envs(
    old: dict[str, str], new: dict[str, str], rename_map: dict[str, str] | None = None
) -> DiffResult:
    """Сравнить два набора переменных. rename_map (old->new) включает детект переименований."""
    res = DiffResult()
    for k, v in new.items():
        if k not in old:
            res.added[k] = v
        elif old[k] != v:
            res.changed[k] = (old[k], v)
    for k, v in old.items():
        if k not in new:
            res.removed[k] = v
    if rename_map:
        for old_name, new_name in rename_map.items():
            if old_name in res.removed and new_name in res.added:
                res.renamed[old_name] = new_name
                res.removed.pop(old_name)
                res.added.pop(new_name)
    return res


def render_text(d: DiffResult) -> str:
    if d.empty:
        return "Различий нет."
    lines = []
    for k, v in sorted(d.renamed.items()):
        lines.append(f"~ переименовано: {k} → {v}")
    for k, v in sorted(d.added.items()):
        lines.append(f"+ добавлено: {k}={v}")
    for k, v in sorted(d.removed.items()):
        lines.append(f"- удалено: {k}={v}")
    for k, (a, b) in sorted(d.changed.items()):
        lines.append(f"* изменено: {k}: {a} → {b}")
    return "\n".join(lines)


def to_dict(d: DiffResult) -> dict[str, Any]:
    return {
        "added": d.added,
        "removed": d.removed,
        "changed": {k: {"from": a, "to": b} for k, (a, b) in d.changed.items()},
        "renamed": d.renamed,
    }
