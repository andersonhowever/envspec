# envspec

[![CI](https://github.com/andersonhowever/envspec/actions/workflows/ci.yml/badge.svg)](https://github.com/andersonhowever/envspec/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%E2%80%933.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Опиши конфиг один раз — получи валидацию, `.env.example`, доку, диагностику и миграции.**

Единый строгий и человекочитаемый стандарт для переменных окружения и конфигов
Python-проектов. README больше не расходится с реальными переменными, а переименование
переменной не ломает прод молча.

> Статус: стабильный (v1.0). Публичный API заморожен и подчиняется semver — см. `SPEC.md` §9.

## Зачем

- У каждого проекта свой ад с `.env`; в CI одно, локально другое, в k8s третье.
- Переименования переменных молча ломают деплой.
- Новые разработчики долго собирают рабочий конфиг.

`envspec` решает это из одного места: валидация, автодока, диагностика и миграции.

## Установка

```bash
pip install envspec
# опционально:
pip install "envspec[yaml]"      # источники YAML
pip install "envspec[pydantic]"  # интеграция с pydantic
```

## Быстрый старт

```python
from envspec import Config, Field

class AppConfig(Config):
    api_url    = Field(str,  required=True, doc="Base API URL")
    timeout_s  = Field(int,  default=30, min=1, max=300)
    verify_ssl = Field(bool, default=True)
    api_token  = Field(str,  secret=True)

cfg = AppConfig.load()     # читает .env + окружение, валидирует, бросает понятную ошибку
print(cfg.api_url, cfg.timeout_s)
```

## CLI

Где взять класс Config — флаг `--config module:Class` или `--config path.py:Class`.
Общие флаги: `--dotenv PATH`, `--profile {dev,test,prod}`, `--format {text,json}`.
Коды выхода: `0` ок · `1` ошибки валидации/проблемы · `2` ошибка использования.

### `validate` — проверить окружение

```console
$ envspec --config app:AppConfig validate
✓ конфиг валиден
```

Если что-то не так — выводятся **все** проблемы сразу (имя · что ожидалось · что
получено · как починить), код выхода `1`:

```console
$ envspec --config app:AppConfig validate
✗ API_URL — обязательная переменная не задана
  ожидалось: непустая строка (Base API URL)
  как починить: добавьте в .env строку  API_URL=...

✗ LOG_LEVEL — значение вне допустимого
  ожидалось: допустимо: ['debug', 'info', 'warning', 'error']
  получено: trace
  как починить: приведите LOG_LEVEL к допустимому значению

✗ TIMEOUT_S — значение вне допустимого
  ожидалось: максимум: 300
  получено: 999
  как починить: приведите TIMEOUT_S к допустимому значению
```

Для CI — `--format json` (machine-readable, тот же набор проблем):

```console
$ envspec --config app:AppConfig --format json validate
{
  "ok": false,
  "errors": [
    {
      "name": "API_URL",
      "summary": "обязательная переменная не задана",
      "expected": "непустая строка (Base API URL)",
      "fix": "добавьте в .env строку  API_URL=..."
    },
    {
      "name": "TIMEOUT_S",
      "summary": "значение вне допустимого",
      "expected": "максимум: 300",
      "fix": "приведите TIMEOUT_S к допустимому значению"
    },
    {
      "name": "LOG_LEVEL",
      "summary": "значение вне допустимого",
      "expected": "допустимо: ['debug', 'info', 'warning', 'error']",
      "fix": "приведите LOG_LEVEL к допустимому значению"
    }
  ],
  "warnings": []
}
```

### `doctor` — диагностика: значение, источник и что чинить

```console
$ envspec --config app:AppConfig doctor
✓ API_URL = https://api.example.com  [.env]
✓ TIMEOUT_S = 30  [.env]
✓ VERIFY_SSL = True  [default]
✓ API_TOKEN = ***  [.env]
✓ LOG_LEVEL = debug  [.env]

итог: OK
```

В колонке `[...]` видно, **откуда** пришло значение (`default`/`.env`/`environ`/`profile`/…),
секреты маскируются как `***`. С профилем `prod` подсвечиваются ужесточённые правила:

```console
$ envspec --config app:AppConfig --profile prod doctor
✗ API_URL = ∅  [default]
    обязательная переменная не задана — добавьте в .env строку  API_URL=...
✓ VERIFY_SSL = True  [profile]
✗ API_TOKEN = ∅  [default]
    обязательная переменная не задана — добавьте в .env строку  API_TOKEN=...
…
```

### `export-example` — сгенерировать `.env.example`

```console
$ envspec --config app:AppConfig export-example
# Base API URL (required)
API_URL=https://api.example.com

# HTTP timeout, секунды
TIMEOUT_S=30

# Проверять TLS-сертификат
VERIFY_SSL=True

# Токен доступа к API (secret)
API_TOKEN=        # secret — заполните вручную

# Уровень логирования
LOG_LEVEL=info
```

### `docs` — markdown-таблица переменных

```console
$ envspec --config app:AppConfig docs
| Переменная | Тип | Обязательна | Default | Secret | Описание |
|---|---|---|---|---|---|
| `API_URL` | str | да | — | нет | Base API URL |
| `TIMEOUT_S` | int | нет | `30` | нет | HTTP timeout, секунды |
| `VERIFY_SSL` | bool | нет | `True` | нет | Проверять TLS-сертификат |
| `API_TOKEN` | str | нет | — | да | Токен доступа к API |
| `LOG_LEVEL` | str | нет | `info` | нет | Уровень логирования |
```

### `diff` — что изменилось между двумя `.env`

```console
$ envspec --config app:AppConfig diff --from .env.old --to .env.new --use-migrations
~ переименовано: API_HOST → API_URL
+ добавлено: LOG_LEVEL=info
- удалено: OLD_FLAG=1
* изменено: TIMEOUT_S: 30 → 60
```

`--use-migrations` подтягивает правила миграций из `--config`, поэтому
переименования распознаются, а не показываются как «удалено + добавлено».

### `migrate` — применить миграции (dry-run по умолчанию)

```console
$ envspec --config app:AppConfig migrate
План миграций:
  • переименовано: API_HOST → API_URL
  • преобразовано: VERIFY_SSL=0 → TLS_MODE=insecure
  • удалено устаревшее: OLD_FLAG (больше не используется)

(dry-run; добавьте --write чтобы применить)
```

## Миграции (киллер-фича)

Переименование переменной больше не ломает прод молча — опиши правило один раз:

```python
from envspec import migration

@migration("0.1 -> 0.2")
def _(m):
    m.rename("API_HOST", "API_URL")
    m.transform("VERIFY_SSL", "TLS_MODE",
                lambda v: "insecure" if v in ("0", "false") else "verify")
    m.deprecate("OLD_FLAG", reason="больше не используется")
```

Дальше — `envspec migrate` (dry-run, превью плана; `--write` чтобы применить) и
`envspec diff --use-migrations` (распознаёт переименования) — вывод см. в разделе CLI выше.

## Профили

```python
from envspec import Config, Field, Profile

class AppConfig(Config):
    verify_ssl = Field(bool, default=False)
    api_token  = Field(str, secret=True, default="")
    profiles = {
        "prod": Profile(overrides={"VERIFY_SSL": "true"}, require=["api_token"]),
    }
```

В профиле `prod` `verify_ssl` форсится в `true`, а `api_token` становится обязательным.
Активный профиль задаётся флагом `--profile` (или аргументом `profile=`), либо
переменной окружения `ENVSPEC_PROFILE` — явный аргумент имеет приоритет над env.

## Pydantic-интероп (опционально)

Описал конфиг один раз в `envspec` — получи готовую модель **pydantic v2**, не дублируя
определение. Требует `pip install "envspec[pydantic]"`.

```python
from envspec.contrib.pydantic import to_pydantic

Model = to_pydantic(AppConfig)          # type[pydantic.BaseModel]
m = Model(API_URL="https://x", TIMEOUT_S=30)
```

Типы, `required`/`default`, границы (`min/max` → `ge/le` или `min_length/max_length`),
`choices` (→ `Literal`), `doc` и пометка `secret` переносятся автоматически; имена полей
модели совпадают с env-именами. Подробнее — SPEC §7.

## Документация проекта

- `SPEC.md` — спецификация API и CLI (источник истины).
- `docs/sources.md` — источники значений и приоритет слияния.
- `ROADMAP.md` — план релизов.
- `CONTRIBUTING.md` — как разрабатывать.
- `CLAUDE.md` — контекст для агентов/разработчиков.

## Лицензия

MIT.
