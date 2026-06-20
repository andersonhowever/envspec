# ROADMAP.md — envspec

Порядок строительства. Каждый этап — отдельный набор PR, всё зелёное (ruff+mypy+pytest)
перед переходом дальше. Версии по семверу.

---

## v0.1 — MVP ядро (валидация)
Цель: можно описать Config и провалидировать окружение с человекочитаемыми ошибками.

- [x] `fields.py`: `Field` со всеми параметрами из SPEC §1, приведение типов, границы.
- [x] `config.py`: метакласс, сбор полей, `load()` / `validate()`, агрегатор ошибок.
- [x] `sources.py`: `os.environ` + `.env` (без внешних зависимостей), приоритет слияния.
- [x] `errors.py`: иерархия исключений + рендер «что/почему/как чинить», маскировка секретов.
- [x] `tests/`: критерии приёмки SPEC §7 (типы, required, min/max, приоритет, секреты) — 25 тестов.
- [x] `__init__.py`: публичный экспорт `Config`, `Field`, исключения.

Готово ✓: `AppConfig.load()` работает, ошибки понятные, ядро покрыто тестами (25/25 зелёные).

## v0.2 — CLI + артефакты
Цель: `envspec` как команда; генерация example и docs.

- [x] `cli.py` (argparse): `validate`, `export-example`, `docs`, флаги `--config/--profile/--format`.
- [x] `render/dotenv.py`, `render/markdown.py` (детерминированный вывод).
- [x] `[project.scripts] envspec = "envspec.cli:main"`.
- [x] Тесты CLI (коды выхода, json-формат, детерминизм артефактов).

## v0.3 — профили + doctor ✓
- [x] `profiles.py`: dev/test/prod, оверрайды, ужесточение правил в prod.
- [x] `doctor.py`: показывает источник каждого значения, отсутствующие, deprecated, подсказки.
- [x] Тесты профилей и doctor.

## v0.4 — diff + миграции (киллер-фича) ✓ ← текущая остановка
- [x] `diff.py`: added/removed/changed/renamed между двумя наборами.
- [x] `migrate.py`: `rename`/`transform`/`deprecate`, dry-run и `--write`.
- [x] CLI `diff`, `migrate`.
- [x] Тесты: dry-run не пишет на диск; renamed детектится; deprecated → warning.

> JSON-источник и YAML-источник (extra) уже реализованы в `sources.py` авансом из v0.5.

## v0.5 — источники YAML/JSON + extras ✓
- [x] `sources.py`: YAML (extra `envspec[yaml]`) и JSON.
- [x] Опциональный pydantic-интероп (extra `envspec[pydantic]`): `to_pydantic`.
- [x] Документация по источникам и приоритету (`docs/sources.md`).

## v1.0 — стабилизация и публикация
- [x] Заморозка публичного API (semver-гарантии): SPEC §9 + снапшот-тест `test_public_api.py`.
- [ ] Полный README с примерами всех команд, CHANGELOG.
- [x] CI: матрица Python 3.9–3.13, lint+type+test, сборка (`.github/workflows/ci.yml`).
- [x] Workflow trusted publishing TestPyPI → PyPI (`.github/workflows/publish.yml`); запуск релиза — за мейнтейнером.
- [~] Бейджи (CI/Python/License добавлены; PyPI-бейдж — после первой публикации).

---

## Definition of Done (для каждого PR)
1. `ruff check .` и `ruff format --check .` — чисто.
2. `mypy src/envspec` (strict) — без ошибок.
3. `pytest -q` — зелёный, новое поведение покрыто тестом.
4. Поведение соответствует `SPEC.md` (или SPEC обновлён в том же PR).
5. Публичные изменения отражены в README/CHANGELOG.
