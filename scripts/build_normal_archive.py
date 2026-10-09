"""Собирает папку-архив для массового импорта из папки `normal/`.

Раскладывает исходные фото по спрайтам / одежде / эмоциям и генерирует
`manifest.json` с заготовками персонажей: slug = имя папки, name = код
(заменить на настоящее имя), description пустой.

Запуск из корня проекта:

    python scripts/build_normal_archive.py
"""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "normal"
TARGET = ROOT / "normal-archive"
UNIVERSE_SLUG = "Everlasting Summer"

# Слои-одежда (всё прочее, кроме body, — эмоции).
OUTFIT_SUFFIXES = {
    "pioneer",
    "pioneer2",
    "swim",
    "dress",
    "sport",
    "panama",
    "glasses",
    "stethoscope",
    "coat",
}

# Слои, которым соответствует тег одежды (outfit_style) в БД.
OUTFIT_TAGS = {
    "pioneer": "pioneer_uniform",
    "pioneer2": "pioneer_uniform",
    "swim": "swimsuit",
    "dress": "dress",
    "sport": "sports_suit",
    "glasses": "glasses",
    "stethoscope": "stethoscope",
    "coat": "coat",
    "panama": "panama",
}
# slug эмоции -> теги (ровно один base + 0..N modifier), как в scripts/tag_assets.py
EMOTION_TAGS = {
    "normal": ["normal"],
    "smile": ["smile"],
    "smile2": ["smile"],
    "smile3": ["smile"],
    "cry": ["cry"],
    "cry2": ["cry"],
    "sad": ["sad"],
    "angry": ["angry"],
    "angry2": ["angry"],
    "rage": ["rage"],
    "shy": ["shy"],
    "shy2": ["shy"],
    "grin": ["grin"],
    "laugh": ["laugh"],
    "laugh2": ["laugh"],
    "serious": ["serious"],
    "shocked": ["shocked"],
    "surprise": ["suprize"],
    "surprise2": ["suprize"],
    "surp1": ["suprize"],
    "surp2": ["suprize"],
    "surp3": ["suprize"],
    "scared": ["scared"],
    "fear": ["scared"],
    "guilty": ["guilty"],
    "upset": ["upset"],
    "dontlike": ["dontlike"],
    "bukal": ["dontlike"],
    "happy": ["happy"],
    "tender": ["tender"],
    "calml": ["calm"],
    "normal_smile": ["smile"],
    "cry_smile": ["smile", "tears"],
    "evil_smile": ["smile", "evil"],
    "fingal": ["normal", "bruise"],
}


README = """# Архив для массового импорта персонажей

Заготовка для страницы «Импорт» в админке (`/admin/importer`).

1. Открой `manifest.json` и замени `"name": "<код>"` у каждого персонажа
   на настоящее имя, заполни `"description"`.
2. При желании поправь `tags` у одежды и эмоций.
3. Заархивируй **содержимое** этой папки (manifest.json должен оказаться
   в корне архива):

   ```
   cd normal-archive && zip -r ../normal.zip .
   ```

4. Загрузи `normal.zip` на `/admin/importer`.

Фото уже разложены в `characters/<код>/...` и привязаны в манифесте.
Слои `*_body` — спрайты, остальные — одежда или эмоции.
Теги проставлены по таблицам `OUTFIT_TAGS` / `EMOTION_TAGS`; теги для новых
слоёв нужно сначала создать в БД (`scripts/tag_assets.py`).
"""


def pretty(slug: str) -> str:
    return slug.replace("_", " ").strip().capitalize()


def parse(name: str) -> tuple[str, str, str]:
    """Разбирает `cs_1_body.png` -> ('cs', '1', 'body')."""
    parts = name.removesuffix(".png").split("_")
    return parts[0], parts[1], "_".join(parts[2:])


def build_character(char_dir: Path) -> dict:
    """Собирает заготовку персонажа для манифеста."""
    ch = char_dir.name
    grouped: dict[str, dict[str, str]] = {}
    for file in sorted(char_dir.glob("*.png")):
        _, n, suffix = parse(file.name)
        grouped.setdefault(n, {})[suffix] = f"characters/{ch}/{file.name}"

    sprites = []
    for n in sorted(grouped):
        layers = dict(grouped[n])
        if "body" in layers:
            base_suffix = "body"
        else:
            # Нет отдельного тела (pi): базой делаем самый короткий слой.
            base_suffix = min(layers, key=len)
        base_image = layers.pop(base_suffix)

        outfits, emotions = [], []
        for suffix, image in sorted(layers.items()):
            if suffix in OUTFIT_SUFFIXES:
                outfits.append(
                    {
                        "slug": suffix,
                        "name": pretty(suffix),
                        "image": image,
                        "tags": [OUTFIT_TAGS[suffix]] if suffix in OUTFIT_TAGS else [],
                    }
                )
            else:
                slug = suffix
                # pi_1_pioneer_smile: имя эмоции без названия одежды.
                if base_suffix != "body" and slug.startswith(f"{base_suffix}_"):
                    slug = slug.split("_", 1)[1]
                emotions.append(
                    {
                        "slug": slug,
                        "name": pretty(slug),
                        "image": image,
                        "tags": EMOTION_TAGS.get(slug, []),
                    }
                )

        sprites.append(
            {
                "slug": f"body_{n}",
                "description": "",
                "image": base_image,
                "tags": [],
                "outfits": outfits,
                "emotions": emotions,
            }
        )

    return {
        "slug": ch,
        "name": ch,  # заменить на настоящее имя
        "description": "",
        "speech_style": None,
        "tags": [],
        "sprites": sprites,
    }


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    (TARGET / "characters").mkdir(parents=True)

    characters = []
    for char_dir in sorted(p for p in SOURCE.iterdir() if p.is_dir()):
        shutil.copytree(char_dir, TARGET / "characters" / char_dir.name)
        characters.append(build_character(char_dir))

    manifest = {
        "version": 1,
        "universe_slug": UNIVERSE_SLUG,
        "characters": characters,
    }
    (TARGET / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (TARGET / "README.md").write_text(README, encoding="utf-8")

    sprites = sum(len(c["sprites"]) for c in characters)
    outfits = sum(len(s["outfits"]) for c in characters for s in c["sprites"])
    emotions = sum(len(s["emotions"]) for c in characters for s in c["sprites"])
    print(f"Готово: {TARGET}")
    print(f"  персонажей: {len(characters)}")
    print(f"  спрайтов:   {sprites}")
    print(f"  одежды:     {outfits}")
    print(f"  эмоций:     {emotions}")
    print(f"  файлов:     {sum(1 for _ in (TARGET / 'characters').rglob('*.png'))}")


if __name__ == "__main__":
    main()
