from dataclasses import dataclass, field

from src.core.codex.interfaces import (
    EmotionRepositoryProtocol,
    OutfitRepositoryProtocol,
    SpriteRepositoryProtocol,
    TagRepositoryProtocol,
)
from src.core.codex.models.character import Emotion, Outfit
from src.core.codex.models.enum import TagKind, TagType
from src.core.codex.services.emotion import best_emotion


@dataclass(frozen=True, slots=True)
class OutfitEmotion:
    """Тег эмоции, доступной для одежды."""

    slug: str
    name: str
    kind: TagKind | None = None


@dataclass(frozen=True, slots=True)
class OutfitTagWithEmotions:
    """Тег стиля одежды с доступными для него эмоциями."""

    outfit_tag: str
    name: str
    emotions: list[OutfitEmotion] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class VisualMatch:
    """Подобранные визуальные слои персонажа (asset_key слоёв)."""

    sprite_asset_key: str
    outfit_asset_key: str
    emotion_asset_key: str | None


class VisualService:
    """Сервис подбора визуальных слоёв персонажа и стилей одежды с эмоциями."""

    def __init__(
        self,
        outfits: OutfitRepositoryProtocol,
        sprites: SpriteRepositoryProtocol,
        emotions: EmotionRepositoryProtocol,
        tags: TagRepositoryProtocol,
    ) -> None:
        self._outfits = outfits
        self._sprites = sprites
        self._emotions = emotions
        self._tags = tags

    async def get_outfits_with_emotions_grouped(
        self, character_ids: list[int]
    ) -> dict[int, list[OutfitTagWithEmotions]]:
        """Группирует одежду персонажей по тегам стиля (`outfit_style`, `kind=base`).

        В каждой группе — теги эмоций тех спрайтов, к которым привязана одежда
        с этим стилем; сначала `base`, затем `modifier`. Тег стиля попадает в
        выдачу даже без эмоций (с пустым списком).

        :param character_ids: id персонажей.
        :return: `character_id` → группы тегов стиля.
        """
        if not character_ids:
            return {}

        sprites = await self._sprites.get_by_character_ids(character_ids)
        outfits = await self._outfits.get_by_character_ids(character_ids)
        emotions = await self._emotions.get_by_character_ids(character_ids)

        character_by_sprite = {sprite.id: sprite.character_id for sprite in sprites}

        # Эмоции спрайта считаем один раз и сразу дедуплицируем по slug тега.
        emotions_by_sprite: dict[int, dict[str, OutfitEmotion]] = {}
        for emotion in emotions:
            sprite_emotions = emotions_by_sprite.setdefault(emotion.sprite_id, {})
            for tag in emotion.tags:
                if tag.type is TagType.EMOTION:
                    sprite_emotions.setdefault(
                        tag.slug,
                        OutfitEmotion(slug=tag.slug, name=tag.name, kind=tag.kind),
                    )

        groups: dict[int, dict[str, _OutfitTagGroup]] = {
            character_id: {} for character_id in character_ids
        }
        for outfit in outfits:
            character_id = character_by_sprite.get(outfit.sprite_id)
            if character_id is None or character_id not in groups:
                continue

            sprite_emotions = emotions_by_sprite.get(outfit.sprite_id, {})

            for tag in outfit.tags:
                if tag.type is not TagType.OUTFIT_STYLE or tag.kind is not TagKind.BASE:
                    continue
                group = groups[character_id].setdefault(
                    tag.slug, _OutfitTagGroup(name=tag.name)
                )
                group.emotions.update(sprite_emotions)

        return {
            character_id: [
                OutfitTagWithEmotions(
                    outfit_tag=slug,
                    name=group.name,
                    emotions=sorted(
                        group.emotions.values(), key=_emotion_tag_sort_key
                    ),
                )
                for slug, group in character_groups.items()
            ]
            for character_id, character_groups in groups.items()
        }

    async def match(
        self,
        character_id: int,
        outfit_tag: str,
        emotion_tags: list[str],
    ) -> VisualMatch | None:
        """Подбирает согласованный набор слоёв: спрайт + наряд + эмоция.

        Наряд ищется по `outfit_tag` среди всех спрайтов персонажа. На каждый
        спрайт берётся наряд с большим `id`; предпочитается спрайт, у которого
        есть эмоция под `emotion_tags`, затем — наряд с большим `id`.

        :param character_id: id персонажа.
        :param outfit_tag: slug тега `outfit_style`.
        :param emotion_tags: slug'и тегов `emotion`: ровно один `base` +
            0..N `modifier`.
        :return: слои персонажа, `emotion_asset_key=None`, если эмоция не
            найдена ни у одного спрайта, или None, если наряда нет.
        """
        outfits = await self._outfits.get_by_character_and_tag(
            character_id, outfit_tag, include_tags=False
        )
        if not outfits:
            return None

        # Для каждого спрайта — наряд с наибольшим id.
        best_outfit_by_sprite: dict[int, Outfit] = {}
        for outfit in outfits:
            current = best_outfit_by_sprite.get(outfit.sprite_id)
            if current is None or outfit.id > current.id:
                best_outfit_by_sprite[outfit.sprite_id] = outfit

        tags = await self._tags.get_by_slugs(emotion_tags)
        emotions = await self._emotions.get_by_character(character_id)

        emotions_by_sprite: dict[int, list[Emotion]] = {}
        for emotion in emotions:
            emotions_by_sprite.setdefault(emotion.sprite_id, []).append(emotion)

        matched_outfit: Outfit | None = None
        matched_emotion: Emotion | None = None
        # Спрайты с нарядом с большим id — первыми.
        for sprite_id, outfit in sorted(
            best_outfit_by_sprite.items(), key=lambda item: item[1].id, reverse=True
        ):
            emotion = best_emotion(
                emotions_by_sprite.get(sprite_id, []), emotion_tags, tags
            )
            if emotion is not None:
                matched_outfit = outfit
                matched_emotion = emotion
                break

        if matched_outfit is None:
            # Эмоции нет ни у одного спрайта — отдаём наряд с большим id.
            matched_outfit = max(best_outfit_by_sprite.values(), key=lambda o: o.id)

        sprite = await self._sprites.get_by_id(matched_outfit.sprite_id)
        if sprite is None:
            return None

        return VisualMatch(
            sprite_asset_key=sprite.asset_key,
            outfit_asset_key=matched_outfit.asset_key,
            emotion_asset_key=matched_emotion.asset_key if matched_emotion else None,
        )


@dataclass(slots=True)
class _OutfitTagGroup:
    """Накопитель: тег стиля одежды и встреченные у него эмоции."""

    name: str
    emotions: dict[str, OutfitEmotion] = field(default_factory=dict)


def _emotion_tag_sort_key(emotion: OutfitEmotion) -> int:
    """Порядок эмоций в группе: `base`, затем `modifier`, затем прочие."""
    if emotion.kind is TagKind.BASE:
        return 0
    if emotion.kind is TagKind.MODIFIER:
        return 1
    return 2
