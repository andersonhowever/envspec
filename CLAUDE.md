# CLAUDE.md — envspec

Контекст для любого агента/разработчика, который работает над этим репозиторием.
Читать **первым**. Связанные документы: `SPEC.md` (что строим — детально),
`ROADMAP.md` (порядок релизов), `CONTRIBUTING.md` (как контрибьютить).

---

## 1. Что это

`envspec` — единый строгий и человекочитаемый стандарт для переменных окружения
и конфигов Python-приложений. Конфиг описывается **один раз** в Python, а пакет
сам валидирует, документирует, диагностирует и мигрирует его.

Одна фраза для README: *"Опиши конфиг один раз — получи валидацию, .env.example,
доку, диагностику и миграции между версиями."*

### Боль, которую решаем
- У каждого проекта свой ад с `.env`; README расходится с реальными переменными.
- В CI одно, локально другое, в k8s третье.
- Переименование переменной молча ломает прод.
- Новый разработчик долго собирает рабочий конфиг.

### Что делает пакет
- Валидирует `.env`, переменные окружения, secrets, YAML/JSON.
- Генерирует `.env.example` и markdown-доку по всем переменным.
- Показывает: что обязательно, что deprecated, что secret.
- Профили: `dev` / `test` / `prod`.
- Проверка совместимости конфигов между версиями (diff).
- Миграции: `API_HOST` → `API_URL`, `VERIFY_SSL=0` → `TLS_MODE=insecure`.
- Человекочитаемые ошибки: не «missing var», а *что* сломано и *как* починить.

---

## 2. Целевой публичный API (запомнить наизусть)

```python
from envspec import Config, Field

class AppConfig(Config):
    api_url    = Field(str,  required=True, doc="Base API URL")
    timeout_s  = Field(int,  default=30, min=1, max=300)
    verify_ssl = Field(bool, default=True)
    api_token  = Field(str,  secret=True)
```

```bash
envspec validate                       # проверить текущее окружение
envspec doctor                         # диагностика: что не так и как починить
envspec export-example                 # сгенерировать .env.example
envspec docs                           # markdown-дока по переменным
envspec diff --from .env.old --to .env.new
envspec migrate                        # применить миграции к окружению/.env
```

Любое изменение API сверяется со `SPEC.md`. Если расходится — сначала правим SPEC,
потом код. SPEC — источник истины.

---

## 3. Архитектура и раскладка

src-layout, ядро **без тяжёлых зависимостей** (zero-deps core). Интеграция с
pydantic и др. — опциональные extras, не основной путь.

```
envspec/
├── src/envspec/
│   ├── __init__.py        # публичный экспорт: Config, Field, исключения
│   ├── fields.py          # Field: тип, default, required, min/max, secret, deprecated, дока
│   ├── config.py          # Config: метакласс, сбор полей, load()/validate()
│   ├── sources.py         # источники: os.environ, .env, yaml, json (+ приоритет/слияние)
│   ├── profiles.py        # dev/test/prod: оверрайды и выбор активного профиля
│   ├── errors.py          # типы ошибок + человекочитаемый рендер (что/почему/как чинить)
│   ├── doctor.py          # диагностика окружения
│   ├── diff.py            # сравнение двух наборов переменных/конфигов
│   ├── migrate.py         # правила миграций (rename, transform, deprecate)
│   ├── render/
│   │   ├── dotenv.py      # .env.example
│   │   └── markdown.py    # docs
│   └── cli.py             # точка входа CLI (validate/doctor/docs/diff/migrate/export-example)
├── tests/                 # pytest, зеркалит структуру src
├── docs/
├── pyproject.toml
├── README.md
├── CLAUDE.md  SPEC.md  ROADMAP.md  CONTRIBUTING.md
```

Поток данных: `sources` собирают сырые значения → `profiles` накладывают оверрайды
→ `config`+`fields` приводят типы и валидируют → `errors` рендерят проблемы.
`doctor`/`diff`/`migrate`/`render` — потребители этой модели, не дублируют логику.

---

## 4. Технологический стек

- Python **3.9+** (минимальная поддерживаемая версия; не использовать синтаксис новее).
- Сборка: **hatchling** (`pyproject.toml`, PEP 621).
- Тесты: **pytest** (+ `pytest-cov`).
- Линт/формат: **ruff** (заменяет flake8/isort/black).
- Типы: **mypy** в strict-режиме. Весь публичный код типизирован.
- CLI: стандартный **argparse** (zero-deps; не тянуть click/typer в ядро).
- Зависимости ядра: **по возможности ноль**. PyYAML — только опциональный extra
  `envspec[yaml]`. pydantic-интероп — extra `envspec[pydantic]`.

---

## 5. Команды разработки

```bash
# окружение
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# проверки (должны проходить все перед коммитом)
ruff check . && ruff format --check .
mypy src/envspec
pytest -q

# сборка пакета
python -m build           # создаёт dist/*.whl и *.tar.gz
twine check dist/*
```

«Зелёный» = ruff + mypy + pytest без ошибок. Это Definition of Done для любого PR.

---

## 6. Правила кода и стиля

- **SPEC — источник истины.** Сначала спецификация, потом реализация.
- **Zero-deps ядро.** Новая обязательная зависимость требует явного обоснования в PR.
- **Качество ошибок — главная фича.** Каждая ошибка валидации содержит: имя переменной,
  что ожидалось, что получено, и конкретный шаг как починить. Никаких голых трейсбеков
  пользователю CLI.
- **Типизировано.** Публичные функции/классы имеют аннотации; mypy strict без `# type: ignore`
  без причины в комментарии.
- **Тест на каждое поведение.** Особенно: парсинг источников, приоритет слияния,
  приведение типов, границы (min/max), профили, миграции.
- **Без сетевых вызовов** в ядре и тестах.
- **Секреты не логируем и не печатаем.** Поля `secret=True` маскируются в выводе
  (`docs`, ошибки, `doctor`) как `***`.
- Стиль: ruff defaults, строки ≤ 100, docstring у публичных API.
- **Семвер строго.** Ломающее изменение публичного API/CLI = major.

---

## 7. Что НЕ делаем (scope guard)

- Не пишем фреймворк управления секретами (Vault/KMS) — только читаем/маскируем.
- Не тянем в ядро тяжёлые зависимости ради удобства.
- Не дублируем логику валидации в `doctor`/`diff` — переиспользуем `config`+`fields`.
- Не поддерживаем Python < 3.9.

---

## 8. Релиз (кратко; детали в ROADMAP.md)

1. Обновить версию в `pyproject.toml` и `CHANGELOG.md`.
2. Все проверки зелёные, тег `vX.Y.Z`.
3. `python -m build && twine check dist/*`.
4. Публикация: сначала TestPyPI, проверка установки, затем PyPI (через CI + trusted publishing).
