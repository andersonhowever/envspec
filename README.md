# envspec

**Опиши конфиг один раз — получи валидацию, `.env.example`, доку, диагностику и миграции.**

Единый строгий и человекочитаемый стандарт для переменных окружения и конфигов
Python-проектов. README больше не расходится с реальными переменными, а переименование
переменной не ломает прод молча.

> Статус: ранняя разработка (v0.4). Публичный API стабилизируется к v1.0 — см. `ROADMAP.md`.

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

```bash
envspec --config app:AppConfig validate            # проверить текущее окружение
envspec --config app:AppConfig --profile prod validate
envspec --config app:AppConfig doctor              # что не так, откуда значение и как починить
envspec --config app:AppConfig export-example      # сгенерировать .env.example
envspec --config app:AppConfig docs                # markdown-дока по переменным
envspec diff --from .env.old --to .env.new --use-migrations
envspec --config app:AppConfig migrate             # dry-run; --write чтобы применить
```

Все команды поддерживают `--format json` (для CI) и `--profile {dev,test,prod}`.

Пример понятной ошибки:

```
✗ API_URL — обязательная переменная не задана
  ожидалось: Base API URL
  как починить: добавьте в .env строку  API_URL=...
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

```bash
$ envspec --config app:AppConfig migrate
План миграций:
  • переименовано: API_HOST → API_URL
  • преобразовано: VERIFY_SSL=0 → TLS_MODE=insecure
  • удалено устаревшее: OLD_FLAG (больше не используется)

(dry-run; добавьте --write чтобы применить)
```

`envspec diff --from .env.old --to .env.new --use-migrations` покажет ещё и переименования,
а не только added/removed.

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
