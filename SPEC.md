# SPEC.md — спецификация envspec

Источник истины для публичного API и CLI. Код обязан соответствовать этому документу.
Расходится — сначала правим SPEC, потом код.

---

## 1. Модель: `Field`

`Field` описывает одну переменную окружения.

```python
Field(
    type,                 # str | int | float | bool | list[str] | "json" — тип значения
    *,
    required=False,       # обязательна ли (несовместимо с default)
    default=None,         # значение по умолчанию, если переменной нет
    doc="",               # человекочитаемое описание (идёт в docs/.env.example)
    env=None,             # имя переменной окружения; по умолчанию ВЕРХНИЙ_РЕГИСТР имени поля
    secret=False,         # маскировать значение в любом выводе
    deprecated=False,     # пометить устаревшей (предупреждение, а не ошибка)
    min=None, max=None,   # границы для int/float; для str/list — длина
    choices=None,         # допустимый набор значений
    example=None,         # пример значения для .env.example (если не secret)
)
```

Правила:
- `required=True` и `default` вместе — ошибка определения (`SpecError`).
- `secret=True` → значение никогда не печатается целиком; в выводе `***`,
  в `.env.example` — пустое значение с комментарием `# secret`.
- `deprecated=True` → при наличии переменной выдаётся warning с подсказкой
  (если есть migrate-правило — указывает на замену).
- Имя env-переменной: явный `env=` > авто из имени поля (`api_url` → `API_URL`).

### Приведение типов
- `bool`: `1/true/yes/on` → True; `0/false/no/off` → False (регистр игнорируется);
  иначе ошибка.
- `int`/`float`: строгий парсинг; нечисловое значение → ошибка с показом полученного.
- `list[str]`: split по запятой, trim пробелов, пустые элементы отбрасываются.
- `"json"`: `json.loads`; ошибка парсинга → понятное сообщение с позицией.

---

## 2. Модель: `Config`

```python
class AppConfig(Config):
    api_url   = Field(str, required=True, doc="Base API URL")
    timeout_s = Field(int, default=30, min=1, max=300)
```

Поведение:
- Метакласс собирает все `Field` в порядке объявления → `AppConfig.__fields__`.
- `cfg = AppConfig.load(*, dotenv_path=".env", use_environ=True, overrides=None,
  profile=None, yaml_path=None, json_path=None)` — собрать значения, привести типы,
  провалидировать. Возвращает инстанс с атрибутами-значениями (`cfg.api_url`).
- При ошибках валидации `load()` бросает `ValidationError`, агрегирующую **все**
  проблемы сразу (не падать на первой).
- `AppConfig.validate(...)` — те же аргументы, но возвращает `Result`
  (`ok`, `values`, `problems`, `warnings`, `origins`) без выброса; используется CLI и тестами.

### Источники и приоритет (`sources.py`)
По умолчанию (от низшего приоритета к высшему):
1. `default` из `Field`
2. файл `.env` (если есть)
3. YAML/JSON конфиг (если передан)
4. `os.environ`
5. профиль-оверрайды (`profiles.py`)

Приоритет настраивается; верхний слой перекрывает нижний. Слияние детерминированное
и логируемо (в `doctor` видно, откуда пришло значение).

### Профили (`profiles.py`)
- Активный профиль: аргумент `profile=` или env `ENVSPEC_PROFILE` (`dev`/`test`/`prod`).
- Профиль задаёт оверрайды дефолтов и может ужесточать правила
  (например, в `prod` `verify_ssl` обязан быть True).

---

## 3. Ошибки (`errors.py`) — ключевая фича

Каждая проблема рендерится по шаблону:

```
✗ API_URL — обязательная переменная не задана
  ожидалось: непустая строка (Base API URL)
  как починить: добавьте в .env строку  API_URL=https://api.example.com

✗ TIMEOUT_S — значение вне допустимого диапазона
  получено: 999
  допустимо: 1..300
  как починить: установите TIMEOUT_S в этот диапазон (например, 30)
```

Требования:
- Агрегировать все ошибки, выводить списком, со стабильной сортировкой по имени.
- Всегда: имя · что ожидалось · что получено · конкретный шаг.
- Секреты в значениях — маскировать.
- Коды выхода CLI: `0` ок, `1` есть ошибки валидации, `2` ошибка использования.

Иерархия исключений:
`EnvspecError` → { `SpecError` (кривое определение), `ValidationError` (агрегат),
`SourceError` (не прочитать источник), `MigrationError` }.

---

## 4. CLI (`cli.py`)

Точка входа `envspec` (через `[project.scripts]`). Подкоманды:

| Команда | Делает | Выход |
|---|---|---|
| `validate` | Грузит конфиг, валидирует текущее окружение/профиль | 0/1 |
| `doctor` | Расширенная диагностика: значения + источник каждого, что отсутствует, deprecated, подсказки | 0/1 |
| `export-example` | Генерирует `.env.example` из определения Config | 0 |
| `docs` | Генерирует markdown-таблицу всех переменных | 0 |
| `diff --from A --to B` | Сравнивает два `.env`/конфига: добавлено/удалено/изменено/переименовано | 0 |
| `migrate [--write]` | Применяет правила миграций; без `--write` — dry-run с превью | 0/1 |

Общие флаги: `--config path.py:AppConfig` (где взять класс Config),
`--profile {dev,test,prod}`, `--format {text,json}`, `--no-color`.

`--format json` обязателен для CI-интеграций (machine-readable вывод validate/diff/doctor).

---

## 5. Миграции (`migrate.py`)

Правила миграций объявляются рядом с Config:

```python
from envspec import migration

@migration("0.1 -> 0.2")
def _(m):
    m.rename("API_HOST", "API_URL")                      # переименование
    m.transform("VERIFY_SSL", "TLS_MODE",                # преобразование значения
                lambda v: "insecure" if v in ("0","false") else "verify")
    m.deprecate("OLD_FLAG", reason="больше не используется")
```

- `migrate` показывает план до применения (что переименуется/преобразуется/удалится).
- Без `--write` — только превью (dry-run). С `--write` — правит `.env`/выводит новый набор.
- Deprecated-переменные, для которых есть правило, в `validate`/`doctor` дают warning
  с указанием замены — предупреждаем **до** падения в проде.

---

## 6. Генерация артефактов (`render/`)

### `.env.example` (`render/dotenv.py`)
- Все переменные в порядке объявления.
- Каждая: комментарий с `doc`, пометки `(required)`/`(deprecated)`, затем `KEY=` или `KEY=example`.
- Секреты: `KEY=        # secret — заполните вручную`.

### `docs` (`render/markdown.py`)
Markdown-таблица: `Переменная | Тип | Обязательна | Default | Secret | Описание`.
Секретные дефолты не раскрываются. Deprecated помечаются и указывают замену.

---

## 7. Pydantic-интероп (extra `envspec[pydantic]`)

Опциональный мост: из определения `Config` сгенерировать модель **pydantic v2**.
Направление одно — envspec → pydantic (envspec остаётся единственным источником
истины: «опиши конфиг один раз»). Ядро остаётся zero-deps; интероп живёт в
`envspec.contrib.pydantic` и импортируется только при наличии extra.

```python
from envspec.contrib.pydantic import to_pydantic

Model = to_pydantic(AppConfig)            # type[pydantic.BaseModel]
m = Model(API_URL="https://x", TIMEOUT_S=30)
```

`to_pydantic(config_cls, *, name=None) -> type[BaseModel]`:
- Имя модели: `name` или `<ConfigName>Model`.
- Имя поля модели = env-имя поля (`api_url` → `API_URL`, либо явный `env=`),
  чтобы модель принимала те же ключи, что и переменные окружения.
- Соответствие типов: `str/int/float/bool` → как есть; `list[str]` → `list[str]`;
  `"json"` → `Any`.
- `required=True` → обязательное поле; иначе — поле с `default` (или `None`, если
  дефолта нет; тип становится `Optional`).
- Границы: для `int/float` → `ge`/`le`; для `str`/`list` → `min_length`/`max_length`.
- `choices` → `Literal[...]`.
- `doc` → `description`; `secret=True` → `json_schema_extra={"secret": True}`.
- Если pydantic не установлен — `SpecError` с подсказкой `pip install 'envspec[pydantic]'`.

Что НЕ делаем (scope guard): обратное направление (pydantic → envspec), генерацию
`BaseSettings`, кастомные валидаторы pydantic. Только структурный маппинг определения.

---

## 8. Критерии приёмки (для тестов)

- Отсутствие `required` → ошибка с подсказкой; код выхода 1.
- Значение вне `min/max`/`choices` → ошибка с диапазоном.
- Все типы приводятся согласно §1; неверный ввод → понятная ошибка.
- Приоритет источников соблюдается (env перекрывает .env перекрывает default).
- Профиль `prod` ужесточает указанные правила.
- `secret=True` нигде не раскрывается в выводе.
- `export-example` и `docs` детерминированы (одинаковый ввод → одинаковый вывод).
- `diff` корректно классифицирует added/removed/changed.
- `migrate` без `--write` ничего не меняет на диске.
- `--format json` даёт валидный JSON для validate/diff/doctor.
- `to_pydantic` строит модель с корректными типами, required/default, границами,
  `choices` (Literal) и пометкой secret; имена полей = env-имена.

---

## 9. Публичный API и semver (заморожено в 1.0)

С версии **1.0** перечисленное ниже — стабильный контракт. Ломающее изменение —
только мажорная версия (см. CLAUDE.md §6). Всё остальное (в т.ч. имена с `_`,
модули `sources`/`diff`/`doctor`/`migrate`/`render` и их функции) — внутреннее
и может меняться в minor/patch.

**Стабильно (semver-покрыто):**
- `envspec.__version__`.
- `from envspec import Config, Field, Profile, migration` и исключения
  `EnvspecError`, `SpecError`, `ValidationError`, `SourceError`, `MigrationError`.
- Конструктор `Field(...)` — параметры из §1.
- `Config.load(...)` / `Config.validate(...)` — сигнатуры из §2; `Config.__fields__`.
- Структура результата: `Result(ok, values, problems, warnings, origins)` и
  `Problem(name, summary, expected, got, fix, secret)` — состав полей.
- `Profile(overrides, require)`; декоратор `migration(label)` и билдер `m`
  (`rename`/`transform`/`deprecate`); выбор профиля через `ENVSPEC_PROFILE`.
- `from envspec.contrib.pydantic import to_pydantic` (extra `envspec[pydantic]`).
- CLI: подкоманды и флаги из §4; коды выхода `0/1/2`.

**Явно НЕ часть публичного API (может меняться):**
- Программные функции `sources.*`, `diff.*`, `doctor.*`, `migrate.apply/plan/rename_map`,
  `render.*` — используются CLI, но не гарантируются как библиотечный API в 1.x.
- Внутренние типы `Migration`, `Op`, метакласс, любые `_`-имена.
