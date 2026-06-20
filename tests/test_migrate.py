import pytest

from envspec import migrate, migration
from envspec.errors import MigrationError


def setup_function():
    migrate.clear_registry()


def test_rename():
    @migration("t")
    def _(m):
        m.rename("API_HOST", "API_URL")

    env = {"API_HOST": "x", "OTHER": "y"}
    new, changes = migrate.apply(env)
    assert new == {"API_URL": "x", "OTHER": "y"}
    assert any("переименовано" in c for c in changes)


def test_transform():
    @migration("t")
    def _(m):
        m.transform(
            "VERIFY_SSL", "TLS_MODE", lambda v: "insecure" if v in ("0", "false") else "verify"
        )

    new, changes = migrate.apply({"VERIFY_SSL": "0"})
    assert new == {"TLS_MODE": "insecure"}


def test_deprecate():
    @migration("t")
    def _(m):
        m.deprecate("OLD_FLAG", reason="не нужно")

    new, changes = migrate.apply({"OLD_FLAG": "1", "KEEP": "2"})
    assert new == {"KEEP": "2"} and any("удалено устаревшее" in c for c in changes)


def test_no_changes_when_absent():
    @migration("t")
    def _(m):
        m.rename("API_HOST", "API_URL")

    new, changes = migrate.apply({"UNRELATED": "1"})
    assert changes == [] and new == {"UNRELATED": "1"}


def test_rename_conflict_raises():
    @migration("t")
    def _(m):
        m.rename("API_HOST", "API_URL")

    with pytest.raises(MigrationError):
        migrate.apply({"API_HOST": "a", "API_URL": "b"})


def test_plan_is_dry_run():
    @migration("t")
    def _(m):
        m.rename("A", "B")

    env = {"A": "1"}
    changes = migrate.plan(env)
    assert env == {"A": "1"}  # план не мутирует исходный dict
    assert any("A → B" in c for c in changes)


def test_rename_map():
    @migration("t")
    def _(m):
        m.rename("API_HOST", "API_URL")
        m.transform("VERIFY_SSL", "TLS_MODE", lambda v: v)

    assert migrate.rename_map() == {"API_HOST": "API_URL", "VERIFY_SSL": "TLS_MODE"}
