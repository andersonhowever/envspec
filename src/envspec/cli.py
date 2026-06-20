"""CLI envspec. См. SPEC.md §4.

Подкоманды: validate, doctor, export-example, docs, diff, migrate.
Коды выхода: 0 ок, 1 ошибки валидации/миграции, 2 usage.
"""

from __future__ import annotations

import argparse
import json
import sys

from envspec import diff as diff_mod
from envspec import doctor as doctor_mod
from envspec import migrate as migrate_mod
from envspec.config import Config
from envspec.errors import EnvspecError, ValidationError
from envspec.render import dotenv as render_dotenv
from envspec.render import markdown as render_markdown
from envspec.sources import load_dotenv_file


def _load_config_class(spec: str) -> type[Config]:
    """Загрузить класс Config из 'module:Class' или 'path.py:Class'."""
    mod_part, _, cls_name = spec.partition(":")
    if not cls_name:
        raise SystemExit(2)
    if mod_part.endswith(".py"):
        import importlib.util
        import pathlib

        name = pathlib.Path(mod_part).stem
        loader = importlib.util.spec_from_file_location(name, mod_part)
        if loader is None or loader.loader is None:
            raise SystemExit(2)
        module = importlib.util.module_from_spec(loader)
        loader.loader.exec_module(module)
    else:
        import importlib

        module = importlib.import_module(mod_part)
    obj = getattr(module, cls_name, None)
    if not (isinstance(obj, type) and issubclass(obj, Config)):
        print(f"не найден класс Config: {spec}", file=sys.stderr)
        raise SystemExit(2)
    return obj


def _cmd_validate(args: argparse.Namespace) -> int:
    cls = _load_config_class(args.config)
    result = cls.validate(dotenv_path=args.dotenv, profile=args.profile)
    if args.format == "json":
        payload = {
            "ok": result.ok,
            "errors": [
                {"name": p.name, "summary": p.summary, "expected": p.expected, "fix": p.fix}
                for p in result.problems
            ],
            "warnings": result.warnings,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if result.ok else 1
    if result.ok:
        print("✓ конфиг валиден")
        for w in result.warnings:
            print(f"⚠ {w}")
        return 0
    print(ValidationError(result.problems).render())
    return 1


def _cmd_doctor(args: argparse.Namespace) -> int:
    cls = _load_config_class(args.config)
    report = doctor_mod.diagnose(cls, dotenv_path=args.dotenv, profile=args.profile)
    if args.format == "json":
        print(json.dumps(doctor_mod.to_dict(report), ensure_ascii=False, indent=2))
    else:
        print(doctor_mod.render_text(report))
    return 0 if report.ok else 1


def _cmd_export_example(args: argparse.Namespace) -> int:
    cls = _load_config_class(args.config)
    print(render_dotenv.render(cls), end="")
    return 0


def _cmd_docs(args: argparse.Namespace) -> int:
    cls = _load_config_class(args.config)
    print(render_markdown.render(cls), end="")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    old = load_dotenv_file(args.from_path)
    new = load_dotenv_file(args.to_path)
    rmap = migrate_mod.rename_map() if args.use_migrations else None
    if args.config_provided:
        # подгружаем конфиг, чтобы зарегистрировать миграции
        _load_config_class(args.config)
        rmap = migrate_mod.rename_map()
    result = diff_mod.diff_envs(old, new, rename_map=rmap)
    if args.format == "json":
        print(json.dumps(diff_mod.to_dict(result), ensure_ascii=False, indent=2))
    else:
        print(diff_mod.render_text(result))
    return 0


def _cmd_migrate(args: argparse.Namespace) -> int:
    _load_config_class(args.config)  # регистрирует миграции
    env = load_dotenv_file(args.dotenv)
    new_env, changes = migrate_mod.apply(env)
    if not changes:
        print("Миграции не требуются.")
        return 0
    print("План миграций:")
    for c in changes:
        print(f"  • {c}")
    if args.write:
        lines = [f"{k}={v}" for k, v in new_env.items()]
        with open(args.dotenv, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"\nПрименено к {args.dotenv}")
    else:
        print("\n(dry-run; добавьте --write чтобы применить)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="envspec", description="Стандарт конфигов и env-переменных.")
    p.add_argument("--config", default="config:AppConfig", help="module:Class или path.py:Class")
    p.add_argument("--dotenv", default=".env", help="путь к .env")
    p.add_argument("--profile", choices=("dev", "test", "prod"))
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--no-color", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="проверить окружение")
    sub.add_parser("doctor", help="диагностика: что не так и как починить")
    sub.add_parser("export-example", help="сгенерировать .env.example")
    sub.add_parser("docs", help="markdown-дока по переменным")
    dp = sub.add_parser("diff", help="сравнить два .env")
    dp.add_argument("--from", dest="from_path", required=True)
    dp.add_argument("--to", dest="to_path", required=True)
    dp.add_argument(
        "--use-migrations",
        action="store_true",
        help="детектить переименования по миграциям из --config",
    )
    sub.add_parser("migrate", help="применить миграции к .env")
    p.add_argument("--write", action="store_true", help="для migrate: записать изменения")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.config_provided = "--config" in (argv if argv is not None else sys.argv[1:])
    try:
        if args.command == "validate":
            return _cmd_validate(args)
        if args.command == "doctor":
            return _cmd_doctor(args)
        if args.command == "export-example":
            return _cmd_export_example(args)
        if args.command == "docs":
            return _cmd_docs(args)
        if args.command == "diff":
            return _cmd_diff(args)
        if args.command == "migrate":
            return _cmd_migrate(args)
    except EnvspecError as e:
        print(f"ошибка: {e}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
