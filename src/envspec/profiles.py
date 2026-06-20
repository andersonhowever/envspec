"""Профили dev/test/prod. См. SPEC.md §2 (Профили)."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as _dc_field

VALID_PROFILES = ("dev", "test", "prod")


@dataclass
class Profile:
    """Оверрайды и ужесточение правил для конкретного профиля.

    overrides: {ENV_NAME: значение} — накладывается верхним слоем (выше environ).
    require:   имена полей, которые в этом профиле становятся обязательными.
    """

    overrides: dict[str, str] = _dc_field(default_factory=dict)
    require: list[str] = _dc_field(default_factory=list)
