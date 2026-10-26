from dataclasses import dataclass, field

from src.core.codex.interfaces import (
    EmotionRepositoryProtocol,
    OutfitRepositoryProtocol,
    SpriteRepositoryProtocol,
    TagRepositoryProtocol,
)
from src.core.codex.models.character import Emotion, Outfit
from src.core.codex.models.tag import Tag
from src.core.codex.services.emotion import best_emotion


@dataclass(frozen=True, slots=True)
class OutfitWithEmotions:
    """Одежда вместе с эмоциями спрайта, к которому она привязана."""

    id: int
    sprite_id: int
    slug: str
    name: str
    asset_key: str
    tags: list[Tag] = field(default_factory=list)
    emotions: list[Emotion] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class VisualMatch:
    """Подобранные визуальные слои персонажа (asset_key спрайта, одежды и эмоции)."""

    sprite_asset_key: str
    outfit_asset_key: str
    emotion_asset_key: str | None


class VisualService:
    """Сервис подбора визуальных слоёв персонажа (спрайт + одежда + эмоция)."""

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
    ) -> dict[int, list[OutfitWithEmotions]]:
        """Группирует одежду персонажей по нарядам, вкладывая в каждый его эмоции.

        Эмоции наряда — это эмоции спрайта, к которому наряд привязан.

        :param character_ids: id персонажей.
        :return: словарь character_id -> список нарядов с вложенными эмоциями.
        """
        grouped = {character_id: [] for character_id in character_ids}
        if not character_ids:
            return grouped

        sprites = await self._sprites.get_by_character_ids(character_ids)
        outfits = await self._outfits.get_by_character_ids(character_ids)
        emotions = await self._emotions.get_by_character_ids(character_ids)

        sprite_to_character = {sprite.id: sprite.character_id for sprite in sprites}

        emotions_by_sprite: dict[int, list[Emotion]] = {}
        for emotion in emotions:
            emotions_by_sprite.setdefault(emotion.sprite_id, []).append(emotion)

        for outfit in outfits:
            character_id = sprite_to_character.get(outfit.sprite_id)
            if character_id is None or character_id not in grouped:
                continue
            grouped[character_id].append(
                OutfitWithEmotions(
                    id=outfit.id,
                    sprite_id=outfit.sprite_id,
                    slug=outfit.slug,
                    name=outfit.name,
                    asset_key=outfit.asset_key,
                    tags=outfit.tags,
                    emotions=emotions_by_sprite.get(outfit.sprite_id, []),
                )
            )

        return grouped

    async def match(
        self,
        character_id: int,
        outfit_tag: str,
        emotion_tags: list[str],
    ) -> VisualMatch | None:
        """Подбирает согласованный набор слоёв: спрайт + наряд + эмоция.

        Наряд ищется по (character_id, outfit_tag) среди всех спрайтов персонажа.
        Среди спрайтов, у которых есть такой наряд, предпочитается тот, у которого
        также есть эмоция под emotion_tags — так спрайт, наряд и эмоция берутся с
        одного тела. При нескольких подходящих спрайтах выбирается наряд с наибольшим
        id. Если подходящей эмоции нет ни у одного спрайта, возвращается наряд с
        наибольшим id и emotion_asset_key=None; если наряд не найден — None.

        :param character_id: id персонажа.
        :param outfit_tag: slug тега одежды (outfit_style).
        :param emotion_tags: slug'и emotion-тегов (ровно один base + 0..N modifier).
        :return: подобранные слои или None, если наряд не найден.
        """
        outfits = await self._outfits.get_by_character_and_tag(character_id, outfit_tag)
        if not outfits:
            return None

        tags = await self._tags.get_by_slugs(emotion_tags)
        emotions = await self._emotions.get_by_character(character_id)

        emotions_by_sprite: dict[int, list[Emotion]] = {}
        for emotion in emotions:
            emotions_by_sprite.setdefault(emotion.sprite_id, []).append(emotion)

        # outfits отсортированы по id desc, поэтому первый встреченный наряд спрайта —
        # с наибольшим id, а порядок ключей повторяет порядок убывания id наряда.
        best_outfit_by_sprite: dict[int, Outfit] = {}
        for outfit in outfits:
            best_outfit_by_sprite.setdefault(outfit.sprite_id, outfit)

        matched_outfit: Outfit | None = None
        matched_emotion: Emotion | None = None
        for sprite_id, outfit in best_outfit_by_sprite.items():
            emotion = best_emotion(
                emotions_by_sprite.get(sprite_id, []), emotion_tags, tags
            )
            if emotion is not None:
                matched_outfit = outfit
                matched_emotion = emotion
                break

        if matched_outfit is None:
            # Эмоции нет ни на одном спрайте с нарядом — отдаём наряд с наибольшим id.
            matched_outfit = next(iter(best_outfit_by_sprite.values()))

        sprite = await self._sprites.get_by_id(matched_outfit.sprite_id)
        if sprite is None:
            return None

        return VisualMatch(
            sprite_asset_key=sprite.asset_key,
            outfit_asset_key=matched_outfit.asset_key,
            emotion_asset_key=matched_emotion.asset_key if matched_emotion else None,
        )
