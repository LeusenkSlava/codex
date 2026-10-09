"""Дотегирует уже созданные в БД эмоции и одежду.

Эмоции/одежда, импортированные без тегов, не участвуют в подборе
(`/characters/{id}/emotions/match`, `/sprites/{id}/outfits/match`), поэтому
скрипт вешает им теги по slug'у: сначала создаёт недостающие теги, затем
раскладывает их по владельцам, у которых ещё нет base-тега.

Запуск из корня проекта (в контейнере приложения, где есть доступ к БД):

    docker compose -p codex exec app python scripts/tag_assets.py
    docker compose -p codex exec app python scripts/tag_assets.py --only outfits

Скрипт идемпотентен: повторный запуск ничего не меняет.
"""

import argparse
import asyncio
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# запуск как `python scripts/tag_assets.py` из корня проекта
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from src.core.codex.models.enum import TagKind, TagType  # noqa: E402
from src.outbound.database.dependencies import get_session_scope  # noqa: E402
from src.outbound.database.models.character import (  # noqa: E402
    EmotionModel,
    OutfitModel,
)
from src.outbound.database.models.tag import TagModel  # noqa: E402


@dataclass(frozen=True)
class TagRule:
    """Тег, который нужно создать, если его ещё нет в БД."""

    type: TagType
    slug: str
    name: str
    kind: TagKind | None = None


# Новые теги, которых не было в БД.
NEW_TAGS: tuple[TagRule, ...] = (
    # эмоции: base
    TagRule(TagType.EMOTION, "scared", "Испуг", TagKind.BASE),
    TagRule(TagType.EMOTION, "guilty", "Вина", TagKind.BASE),
    TagRule(TagType.EMOTION, "upset", "Расстройство", TagKind.BASE),
    TagRule(TagType.EMOTION, "dontlike", "Недовольство", TagKind.BASE),
    TagRule(TagType.EMOTION, "happy", "Радость", TagKind.BASE),
    TagRule(TagType.EMOTION, "tender", "Нежность", TagKind.BASE),
    TagRule(TagType.EMOTION, "calm", "Спокойствие", TagKind.BASE),
    # эмоции: modifier
    TagRule(TagType.EMOTION, "tears", "Со слезами", TagKind.MODIFIER),
    TagRule(TagType.EMOTION, "evil", "Злая", TagKind.MODIFIER),
    TagRule(TagType.EMOTION, "bruise", "Фингал", TagKind.MODIFIER),
    # одежда: base
    TagRule(TagType.OUTFIT_STYLE, "glasses", "Очки", TagKind.BASE),
    TagRule(TagType.OUTFIT_STYLE, "stethoscope", "Стетоскоп", TagKind.BASE),
    TagRule(TagType.OUTFIT_STYLE, "coat", "Пальто", TagKind.BASE),
    TagRule(TagType.OUTFIT_STYLE, "panama", "Панама", TagKind.BASE),
)

# Опечатки в уже существующих тегах: (старый slug, новый slug, новое имя).
RENAMED_TAGS: tuple[tuple[TagType, str, str, str], ...] = (
    # в БД тег был записан как ' sports_suit' (с ведущим пробелом), из-за чего
    # подбор по slug 'sports_suit' не работал
    (TagType.OUTFIT_STYLE, " sports_suit", "sports_suit", "Спортивный костюм"),
)

# slug эмоции -> теги (ровно один base + 0..N modifier).
EMOTION_TAGS: dict[str, tuple[str, ...]] = {
    "normal": ("normal",),
    "smile": ("smile",),
    "smile2": ("smile",),
    "smile3": ("smile",),
    "cry": ("cry",),
    "cry2": ("cry",),
    "sad": ("sad",),
    "angry": ("angry",),
    "angry2": ("angry",),
    "rage": ("rage",),
    "shy": ("shy",),
    "shy2": ("shy",),
    "grin": ("grin",),
    "laugh": ("laugh",),
    "laugh2": ("laugh",),
    "serious": ("serious",),
    "shocked": ("shocked",),
    "surprise": ("suprize",),
    "surprise2": ("suprize",),
    "surp1": ("suprize",),
    "surp2": ("suprize",),
    "surp3": ("suprize",),
    "scared": ("scared",),
    "fear": ("scared",),
    "guilty": ("guilty",),
    "upset": ("upset",),
    "dontlike": ("dontlike",),
    "bukal": ("dontlike",),  # Женя: взгляд исподлобья, недовольная
    "happy": ("happy",),
    "tender": ("tender",),
    "calml": ("calm",),
    "normal_smile": ("smile",),  # сдержанная улыбка
    "cry_smile": ("smile", "tears"),  # улыбка сквозь слёзы
    "evil_smile": ("smile", "evil"),
    "fingal": ("normal", "bruise"),  # обычное лицо с фингалом
}

# slug одежды -> теги (ровно один base).
OUTFIT_TAGS: dict[str, tuple[str, ...]] = {
    "pioneer": ("pioneer_uniform",),
    "pioneer2": ("pioneer_uniform",),
    "swim": ("swimsuit",),
    "dress": ("dress",),
    "sport": ("sports_suit",),
    "glasses": ("glasses",),
    "stethoscope": ("stethoscope",),
    "coat": ("coat",),
    "panama": ("panama",),
}


@dataclass(frozen=True)
class Target:
    """Что дотегируем: тип тега, ORM-модель владельца и правила по slug'у."""

    title: str
    tag_type: TagType
    model: Any
    rules: dict[str, tuple[str, ...]]


TARGETS: tuple[Target, ...] = (
    Target("эмоции", TagType.EMOTION, EmotionModel, EMOTION_TAGS),
    Target("одежда", TagType.OUTFIT_STYLE, OutfitModel, OUTFIT_TAGS),
)


async def rename_tags(session) -> list[str]:
    """Чинит slug'и/имена уже существующих тегов; возвращает список правок."""
    changes: list[str] = []
    for tag_type, old_slug, new_slug, new_name in RENAMED_TAGS:
        tag = await session.scalar(
            select(TagModel).where(
                TagModel.type == tag_type, TagModel.slug == old_slug
            )
        )
        if tag is None:
            continue
        conflict = await session.scalar(
            select(TagModel).where(
                TagModel.type == tag_type, TagModel.slug == new_slug
            )
        )
        if conflict is not None:
            raise ValueError(
                f"тег {new_slug!r} уже существует, {old_slug!r} не переименован"
            )
        tag.slug, tag.name = new_slug, new_name
        changes.append(f"{old_slug!r} -> {new_slug!r} ({new_name})")

    await session.flush()
    return changes


async def ensure_tags(session) -> tuple[dict[tuple[TagType, str], TagModel], list[str]]:
    """Создаёт недостающие теги и возвращает их по (тип, slug)."""
    existing = {
        (tag.type, tag.slug): tag
        for tag in (await session.scalars(select(TagModel))).all()
    }

    created: list[str] = []
    for rule in NEW_TAGS:
        if (rule.type, rule.slug) in existing:
            continue
        tag = TagModel(
            type=rule.type, slug=rule.slug, name=rule.name, kind=rule.kind
        )
        session.add(tag)
        existing[(rule.type, rule.slug)] = tag
        created.append(f"{rule.type.value}:{rule.slug}")

    await session.flush()
    return existing, created


async def tag_target(
    session,
    target: Target,
    tags: dict[tuple[TagType, str], TagModel],
) -> dict[str, list[str]]:
    """Дотегирует владельцев (эмоции/одежду) без base-тега."""
    owners = (
        await session.scalars(
            select(target.model)
            .options(selectinload(target.model.tags))
            .order_by(target.model.id)
        )
    ).all()

    tagged: dict[str, list[str]] = {}
    for owner in owners:
        if any(tag.kind is TagKind.BASE for tag in owner.tags):
            continue
        if owner.slug not in target.rules:
            continue

        wanted = target.rules[owner.slug]
        current = {tag.slug for tag in owner.tags}
        for slug in wanted:
            tag = tags.get((target.tag_type, slug))
            if tag is None:
                raise KeyError(f"тег {slug!r} ({target.tag_type.value}) не найден")
            if slug not in current:
                owner.tags.append(tag)

        tagged[f"{owner.id}:{owner.slug}"] = list(wanted)

    await session.flush()
    return tagged


async def untagged_left(session, target: Target) -> list[str]:
    owners = (
        await session.scalars(
            select(target.model)
            .options(selectinload(target.model.tags))
            .order_by(target.model.id)
        )
    ).all()
    return [
        f"{owner.id}:{owner.slug}"
        for owner in owners
        if not any(tag.kind is TagKind.BASE for tag in owner.tags)
    ]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        choices=[target.title for target in TARGETS] + ["all"],
        default="all",
        help="что дотегировать (по умолчанию всё)",
    )
    return parser.parse_args(argv)


async def main() -> None:
    args = parse_args()
    targets = [
        target
        for target in TARGETS
        if args.only in ("all", target.title)
    ]

    async with get_session_scope() as session:
        renamed = await rename_tags(session)
        tags, created = await ensure_tags(session)

        report: list[tuple[Target, dict[str, list[str]], list[str]]] = []
        for target in targets:
            tagged = await tag_target(session, target, tags)
            left = await untagged_left(session, target)
            report.append((target, tagged, left))

    if renamed:
        print(f"Исправлено тегов: {len(renamed)} — {'; '.join(renamed)}")
    print(f"Создано тегов: {len(created)}" + (f" — {', '.join(created)}" if created else ""))

    for target, tagged, left in report:
        print(f"\n[{target.title}] теги проставлены {len(tagged)} записям:")
        for key, slugs in tagged.items():
            print(f"  {key}: {', '.join(slugs)}")
        if left:
            print(f"[{target.title}] осталось без base-тега: {len(left)}")
            for key in left:
                print(f"  {key}")


if __name__ == "__main__":
    asyncio.run(main())
