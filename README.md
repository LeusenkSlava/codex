# codex

Сервис-каталог ассетов для интерактивных визуальных новелл.

## О сервисе

Codex хранит «библиотеку» всего, из чего собирается сцена визуальной новеллы, и отдаёт её по HTTP API
другим сервисам (например, генератору сюжета), чтобы они могли подбирать персонажей, позы, эмоции,
одежду и локации по описаниям и тегам.

Сущности:

| Сущность | Что это | Принадлежит |
|---|---|---|
| **Universe** | Вселенная / сеттинг новеллы | — |
| **Character** | Персонаж: имя, пол (`gender`), описание, стиль речи (`speech_style`, JSON) | вселенной |
| **Sprite** | Базовый слой персонажа (тело/поза) с изображением | персонажу |
| **Outfit** | Слой одежды поверх спрайта | спрайту |
| **Emotion** | Слой лица (эмоция) поверх спрайта | спрайту |
| **Background** | Задник / локация | вселенной |
| **Sound** | Звук: музыка или звуковой эффект (аудиофайл) | вселенной |
| **Tag** | Теги для подбора: `emotion`, `outfit_style`, `location`, `time_of_day`, `archetype`, `music`, `sfx`; у `emotion`-тегов есть `kind`: `base` (ровно один на эмоцию) и `modifier` (0..N); у `outfit_style`-тегов — `base` (ровно один на одежду) | — |

Возможности:

- **REST API (только чтение)** — списки вселенных, персонажей, спрайтов, эмоций, одежды и задников.
- **Админка** на `/admin` (sqladmin) — создание и редактирование всех сущностей, загрузка изображений и аудио.
- **Массовый импорт персонажей** — страница «Импорт» в админке: загрузка ZIP-архива с `manifest.json` и картинками, создающего персонажей со спрайтами, одеждой и эмоциями одной операцией.
- **Раздача медиа** — загруженные изображения и аудио сохраняются в папку `media/` и отдаются по `/media/<folder>/<file>`.
- **Healthcheck** — `GET /health`.

Стек: Python 3.12+, FastAPI, SQLAlchemy (async), Alembic, PostgreSQL 18, sqladmin, uv, Docker Compose.

### API

| Метод | Путь | Описание |
|---|---|---|
| GET | `/universes` | Все вселенные |
| GET | `/universes/{universe_id}` | Вселенная по id |
| GET | `/universes/{universe_id}/characters` | Персонажи вселенной |
| GET | `/universes/{universe_id}/backgrounds` | Задники вселенной |
| GET | `/universes/{universe_id}/backgrounds/tags` | Теги задников вселенной: локации (`base`) и модификаторы (`modifiers`) отдельными списками |
| POST | `/universes/{universe_id}/backgrounds/match` | Подбор одного самого подходящего задника по тегам (`{"tags": ["library", "night"]}`: ровно один `base` + 0..N `modifier`) |
| POST | `/universes/backgrounds/batch` | Батч подбора задников (`[{"universe_id": 1, "tags": [...]}, ...]` → `dict[universe_id, background]`) |
| GET | `/characters/{character_id}/sprites` | Спрайты персонажа |
| GET | `/characters/{character_id}/emotions` | Эмоции персонажа по всем его спрайтам |
| GET | `/characters/{character_id}/emotions/tags` | Теги эмоций персонажа: `base` и `modifiers` отдельными списками |
| POST | `/characters/{character_id}/emotions/match` | Подбор одной самой подходящей эмоции по тегам (`{"sprite_id": 1, "tags": ["happy", "blush"]}` — `sprite_id` необязателен) |
| POST | `/characters/emotions/batch` | Батч подбора эмоций (`[{"character_id": 1, "sprite_id": 1, "tags": [...]}, ...]` → `dict[character_id, emotion]`) |
| GET | `/sprites/{sprite_id}/outfits` | Одежда спрайта |
| GET | `/characters/{character_id}/outfits/tags` | Теги одежды персонажа (type=outfit_style) без повторений |
| POST | `/sprites/{sprite_id}/outfits/match` | Подбор одной одежды по тегу (`{"tag": "casual"}`; при нескольких — с наибольшим `id`) |
| POST | `/characters/outfits-with-emotions/batch` | Батч группировки: `[id, ...]` → `dict[character_id, наряды с вложенными эмоциями]` |
| POST | `/characters/{character_id}/visuals/match` | Подбор спрайта + наряда + эмоции (`{"outfit_tag": "red-dress", "emotion_tags": ["angry", "soft"]}` → `{sprite_asset_key, outfit_asset_key, emotion_asset_key}`; спрайт/наряд/эмоция берутся с одного тела; эмоция не найдена → `emotion_asset_key: null`, наряд не найден → `404`) |
| GET | `/media/{folder}/{filename}` | Файл медиа: изображение или аудио (значение `asset_key`) |
| GET | `/health` | Проверка состояния сервиса |

Полная схема — в Swagger: `/docs`.

### Массовый импорт персонажей

В админке (`/admin`) есть страница **«Импорт»**: она принимает ZIP-архив с `manifest.json` и картинками
и создаёт персонажа вместе со спрайтами, одеждой и эмоциями одной операцией — связи и папки медиа
подставляются автоматически. Импорт атомарный: если есть хоть одна ошибка, ничего не создаётся,
а на странице показывается список проблем.

Архив:

```
alice.zip
├── manifest.json
└── alice/
    ├── body.png      # спрайт
    ├── casual.png    # одежда
    └── happy.png     # эмоция
```

`manifest.json` (можно описать несколько персонажей сразу):

```json
{
  "version": 1,
  "universe_slug": "my-novel",
  "characters": [
    {
      "slug": "alice",
      "name": "Алиса",
      "description": "Главная героиня",
      "gender": "female",
      "speech_style": {"tone": "soft"},
      "tags": ["tsundere"],
      "sprites": [
        {
          "slug": "default",
          "description": "Стандартная поза",
          "image": "alice/body.png",
          "outfits": [
            {"slug": "casual", "name": "Повседневная", "image": "alice/casual.png", "tags": ["casual"]}
          ],
          "emotions": [
            {"slug": "happy", "name": "Радость", "image": "alice/happy.png", "tags": ["happy"]}
          ]
        }
      ]
    }
  ]
}
```

Правила:

- `universe_slug` — вселенная должна уже существовать.
- Теги указываются по `slug` и должны существовать заранее; тип проверяется по контексту
  (персонаж → `archetype`, одежда → `outfit_style`, эмоция → `emotion`; теги спрайта — любой тип).
- `gender` — обязательный пол персонажа, строго `male` или `female`.
- `image` — путь к файлу внутри архива; картинка кладётся в `sprites` / `outfits` / `emotions`.
- Повторный импорт уже существующего `slug` персонажа — ошибка (существующее не перезаписывается).

### Теги эмоций и одежды

Каждой эмоции вешается ровно один `base`-тег и 0..N `modifier`-тегов — по ним эмоция
подбирается в `POST /characters/{id}/emotions/match`. Базовые эмоции: `normal`, `smile`,
`grin`, `laugh`, `cry`, `sad`, `angry`, `rage`, `serious`, `shy`, `shocked`, `suprize`,
`scared`, `guilty`, `upset`, `dontlike`, `happy`, `tender`, `calm`; модификаторы: `tears`,
`evil`, `bruise`, `frightening`.

Одежда (`outfit_style`) тегируется одним `base`-тегом: `pioneer_uniform`, `dress`,
`swimsuit`, `sports_suit`, `glasses`, `stethoscope`, `coat`, `panama` — подбор
в `POST /sprites/{id}/outfits/match`.

Если эмоции/одежда уже созданы в БД, но остались без тегов, их дотегирует идемпотентный
скрипт (недостающие теги создаёт сам, заодно чинит slug'и с опечатками):

```bash
docker compose -p codex exec app python scripts/tag_assets.py
docker compose -p codex exec app python scripts/tag_assets.py --only одежда
```

Правила «slug → теги» лежат в `scripts/tag_assets.py` и продублированы
в `EMOTION_TAGS` / `OUTFIT_TAGS` в `scripts/build_normal_archive.py`.

### Теги задников

Задник размечен тегами двух типов, а роль тега задаёт `kind` — как у эмоций:
ровно один `base` (сама локация: `library`, `square`, `dining_room`, домики, ...)
и 0..N `modifier` (время суток `morning`/`day`/`evening`/`night`, а также
`inside`/`outside`, `light_turn_on`/`light_turn_off`, `with_people`/`without_people`,
`bedroom`).

- `GET /universes/{id}/backgrounds/tags` возвращает доступные вселенной теги,
  сгруппированные по **роли**: `{"base": [...], "modifiers": [...]}`
  (внутри — по slug, без повторов).
- `POST /universes/{id}/backgrounds/match` принимает `{"tags": ["library", "night"]}`:
  ровно один `base`-тег обязателен. Побеждает задник с большим числом совпавших
  `modifier`, затем — с меньшим числом лишних `modifier`, при равенстве —
  с меньшим `id`. Если подходящего задника нет — `404`.
- `POST /universes/backgrounds/batch` делает то же для списка
  `[{"universe_id": 1, "tags": [...]}, ...]` и возвращает
  `{"1": background | null, ...}`.

Примеры: `["library", "inside", "day"]` → `int_library_day`;
`["library", "night"]` → `int_library_night2` (при равном счёте побеждает меньший `id`);
`["library", "night", "light_turn_off"]` → `int_library_night`.

Разметку задников и пробелы в slug'ах тегов чинит идемпотентный скрипт
(по умолчанию только показывает план):

```bash
docker compose -p codex exec app python scripts/fix_background_tags.py --dry-run
docker compose -p codex exec app python scripts/fix_background_tags.py
```

### Структура

```
src/
├── core/        # доменные модели, сервисы, Protocol-интерфейсы репозиториев
├── inbound/     # HTTP-слой: роутеры, схемы, зависимости
├── outbound/    # БД (модели, репозитории, миграции), медиа-хранилище, админка
└── main/        # точка входа (run.py), настройки, подключение админки
```

## Запуск

### Требования

- Docker и Docker Compose
- make
- Внешняя docker-сеть `traefik` и запущенный Traefik с entrypoint `web` — приложение публикуется
  через него на `http://codex.localhost`. Если сети ещё нет:

  ```bash
  docker network create traefik
  ```

### Шаги

1. Создайте файл `.secrets` в корне проекта (он не коммитится) с доступами к Postgres:

   ```dotenv
   POSTGRES__USER=codex
   POSTGRES__PASSWORD=change-me
   ```

   Остальные переменные лежат в `env.example`. Файл `.env` собирается автоматически
   из `env.example` + `.secrets` при каждом вызове `make` — руками его не правьте.

2. Поднимите сервис:

   ```bash
   make upd   # сборка и запуск в фоне
   # или
   make up    # сборка и запуск с логами в терминале
   ```

   Compose поднимет Postgres, прогонит миграции (`alembic upgrade head`) и запустит приложение.

3. Откройте:

   - API / Swagger — http://codex.localhost/docs
   - Админка — http://codex.localhost/admin
   - Postgres снаружи доступен на `localhost:9879`

### Полезные команды

| Команда | Что делает |
|---|---|
| `make upd` / `make up` | Пересобрать и запустить (в фоне / с логами) |
| `make just_up` | Запустить без пересборки |
| `make stop` / `make start` / `make restart` | Остановить / запустить / перезапустить контейнеры |
| `make down` | Остановить и удалить контейнеры |
| `make migration m="описание"` | Сгенерировать миграцию Alembic (приложение должно быть запущено) |
| `make prune` | Почистить docker-ресурсы проекта |

### Миграции

История миграций схлопнута в одну базовую:
`src/outbound/database/versions/2026-10-23_232318_initial_schema.py`
(ревизия `0bdbf43eb96b`). Она создаёт всю схему с нуля.

- Новая (пустая) БД — обычный `alembic upgrade head`; compose делает это сам при старте.
- Если БД уже существует и её схема соответствует моделям, baseline выполнять **нельзя**
  (таблицы уже есть). Её нужно только пометить как применённую:

  ```bash
  docker compose -p codex exec app alembic stamp head
  ```

- Дальнейшие изменения схемы — обычные миграции через `make migration m="..."`.

Повторить схлопывание (аналог Django `squashmigrations`):

1. Временно убрать файлы из `src/outbound/database/versions/` и поднять пустую БД.
2. Сгенерировать baseline: `alembic revision --autogenerate -m "Initial schema"`.
3. Проверить его на пустой БД: `alembic upgrade head` и `alembic check`; при необходимости
   дописать в `downgrade` удаление нативных enum-типов.
4. Удалить старые файлы миграций.
5. На всех существующих БД выполнить `alembic stamp head`.

### Переменные окружения

Настройки читаются из `.env`, вложенные поля разделяются `__`.

| Переменная | По умолчанию | Описание |
|---|---|---|
| `POSTGRES__DB` | `postgres` | Имя БД |
| `POSTGRES__HOST` | `db_pg` | Хост БД |
| `POSTGRES__PORT` | `5432` | Порт БД |
| `POSTGRES__USER` | — | Пользователь БД (в `.secrets`) |
| `POSTGRES__PASSWORD` | — | Пароль БД (в `.secrets`) |
| `APP__LOGGING_LEVEL` | `INFO` | Уровень логирования |
| `APP__DEBUG_MODE` | `false` | Режим отладки |
| `APP__ROOT_PATH` | `/` | Root path приложения (если стоит за прокси с префиксом) |
| `MEDIA__ROOT` | `media` | Папка для загруженных изображений |
| `MEDIA__URL` | `/media` | URL-префикс раздачи изображений |
