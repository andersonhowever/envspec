# Changelog

Формат основан на [Keep a Changelog](https://keepachangelog.com/), версии по [SemVer](https://semver.org/).

## [Unreleased] — путь к 1.0
### Added
- Выбор профиля через переменную `ENVSPEC_PROFILE` (когда аргумент `profile=` не передан;
  явный аргумент имеет приоритет) — закрывает заявленное в SPEC §2 поведение.
- SPEC §9: заморозка публичного API и semver-гарантии (что стабильно, что внутреннее).
- `tests/test_public_api.py`: снапшот публичной поверхности (экспорты, сигнатуры,
  состав `Result`/`Problem`, иерархия исключений) — ловит случайные ломающие изменения.
- CI (GitHub Actions): матрица Python 3.9–3.13, lint+type+test, build; workflow
  trusted-publishing (TestPyPI → PyPI). Бейджи в README.
### Changed
- SPEC §2: сигнатура `Config.load/validate` приведена к реальной (устранено расхождение).

## [0.5.0] — источники YAML/JSON + pydantic-интероп
### Added
- `envspec.contrib.pydantic.to_pydantic(Config)` — генерация модели pydantic v2 из
  определения Config (типы, required/default, границы, `choices`→`Literal`, `doc`,
  пометка secret; имена полей = env-имена). Extra `envspec[pydantic]`.
- `docs/sources.md`: документация по источникам значений и приоритету слияния.
### Notes
- YAML/JSON-источники были добавлены ранее (в 0.3.0) авансом; в 0.5 закрыт остаток
  вехи — pydantic-интероп и документация источников.

## [0.4.0] — diff + миграции (киллер-фича)
### Added
- `migrate.py`: декоратор `@migration`, операции `rename`/`transform`/`deprecate`,
  реестр миграций, `apply`/`plan` (dry-run по умолчанию), сводная `rename_map`.
- `diff.py`: классификация added/removed/changed + детект переименований по миграциям.
- CLI `diff --from --to [--use-migrations]` и `migrate [--write]` (dry-run/применение).

## [0.3.0] — профили + doctor
### Added
- `profiles.py`: `Profile` (overrides + require); профили dev/test/prod,
  ужесточение правил в prod (форс значений, доп. обязательные поля).
- `doctor.py`: диагностика с источником каждого значения, статусами
  ok/missing/error/deprecated, маскировкой секретов; text и json вывод.
- `sources.py`: слоистое слияние с трекингом происхождения (`layered`/`merge_with_origin`),
  JSON-источник и YAML-источник (extra `envspec[yaml]`).
- CLI `doctor`, флаг `--profile`.

## [0.2.0] — рендер артефактов + CLI
### Added
- `render/dotenv.py`: генерация `.env.example` (детерминированно, секреты не раскрываются).
- `render/markdown.py`: markdown-таблица переменных.
- CLI `export-example`, `docs`; флаг `--format {text,json}`.
- `Field.type_name` для рендера.

## [0.1.0] — ядро (валидация)
### Added
- Скелет репозитория: src-layout, pyproject (hatchling), ruff/mypy/pytest конфиг.
- Ядро: `Field` (типы str/int/float/bool/list[str]/json, required/default, min/max,
  choices, secret, deprecated, кастомное имя `env=`), `Config` (метакласс, `load`/`validate`,
  агрегация всех ошибок сразу), `sources` (.env + environ + приоритет слияния),
  человекочитаемые ошибки (имя · ожидалось · получено · как починить) с маскировкой секретов.
- `required` отвергает пустую/пробельную строку (SPEC §3).
- CLI `envspec validate`; остальные подкоманды — заглушки по ROADMAP.
- 25 тестов по критериям приёмки SPEC §7 (все зелёные).
- Документы: CLAUDE.md, SPEC.md, ROADMAP.md, CONTRIBUTING.md; пример `examples/app_config.py`.
