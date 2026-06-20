"""envspec — единый стандарт для переменных окружения и конфигов."""

from envspec.config import Config
from envspec.errors import (
    EnvspecError,
    MigrationError,
    SourceError,
    SpecError,
    ValidationError,
)
from envspec.fields import Field
from envspec.migrate import migration
from envspec.profiles import Profile

__all__ = [
    "Config",
    "Field",
    "Profile",
    "migration",
    "EnvspecError",
    "SpecError",
    "ValidationError",
    "SourceError",
    "MigrationError",
]
__version__ = "0.4.0"
