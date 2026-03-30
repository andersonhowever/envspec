from __future__ import annotations


class Field:
    def __init__(
        self,
        type_,
        *,
        required: bool = False,
        default=None,
        env: str | None = None,
        doc: str | None = None,
        secret: bool = False,
        aliases: list[str] | None = None,
    ) -> None:
        self.type_ = type_
        self.required = required
        self.default = default
        self.env = env
        self.doc = doc
        self.secret = secret
        self.aliases = aliases or []