from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


class EnvspecError(Exception): ...


class SpecError(EnvspecError): ...


class SourceError(EnvspecError): ...


class MigrationError(EnvspecError): ...


@dataclass
class Problem:
    name: str
    summary: str
    expected: str = ""
    got: str = ""
    fix: str = ""
    secret: bool = False

    def render(self) -> str:
        got = "***" if self.secret and self.got else self.got
        lines = [f"✗ {self.name} — {self.summary}"]
        if self.expected:
            lines.append(f"  ожидалось: {self.expected}")
        if got:
            lines.append(f"  получено: {got}")
        if self.fix:
            lines.append(f"  как починить: {self.fix}")
        return "\n".join(lines)


class ValidationError(EnvspecError):
    def __init__(self, problems: Iterable[Problem]) -> None:
        self.problems = sorted(problems, key=lambda p: p.name)
        super().__init__(self.render())

    def render(self) -> str:
        return "\n\n".join(p.render() for p in self.problems)
