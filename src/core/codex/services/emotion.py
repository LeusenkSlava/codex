from dataclasses import dataclass

from src.core.codex.interfaces import EmotionRepositoryProtocol, TagRepositoryProtocol
from src.core.codex.models.character import Emotion
from src.core.codex.models.enum import TagKind
from src.core.codex.models.tag import Tag


@dataclass(frozen=True, slots=True)
class EmotionMatchQuery:
    """Запрос на подбор эмоции: персонаж + набор тегов-смыслов (slug)."""

    character_id: int
    tags: list[str]
    sprite_id: int | None = None


@dataclass(frozen=True, slots=True)
class EmotionTags:
    """Доступные персонажу emotion-теги, разделённые по роли."""

    base: list[Tag]
    modifiers: list[Tag]


def best_emotion(
    emotions: list[Emotion],
    tag_slugs: list[str],
    tags_by_slug: dict[str, Tag],
    sprite_id: int | None = None,
) -> Emotion | None:
    """Выбирает лучшую эмоцию из списка.

    Приоритет: совпадение спрайта -> число совпавших modifier ->
    меньше лишних modifier -> меньший id. base обязателен и должен быть ровно один.
    """
    base_slugs = [
        slug
        for slug in tag_slugs
        if (tag := tags_by_slug.get(slug)) and tag.kind is TagKind.BASE
    ]
    modifier_slugs = {
        slug
        for slug in tag_slugs
        if (tag := tags_by_slug.get(slug)) and tag.kind is TagKind.MODIFIER
    }

    # base обязателен и должен быть ровно один
    if len(base_slugs) != 1:
        return None
    base_slug = base_slugs[0]

    best: Emotion | None = None
    best_key: tuple[bool, int, int, int] | None = None
    for emotion in emotions:
        if base_slug not in {
            tag.slug for tag in emotion.tags if tag.kind is TagKind.BASE
        }:
            continue

        emotion_modifiers = {
            tag.slug for tag in emotion.tags if tag.kind is TagKind.MODIFIER
        }
        matched = len(modifier_slugs & emotion_modifiers)
        extra = len(emotion_modifiers - modifier_slugs)
        sprite_match = sprite_id is not None and emotion.sprite_id == sprite_id
        key = (sprite_match, matched, -extra, -emotion.id)

        if best_key is None or key > best_key:
            best = emotion
            best_key = key

    return best


class EmotionService:
    """Сервис эмоций."""

    def __init__(
        self,
        repository: EmotionRepositoryProtocol,
        tags: TagRepositoryProtocol,
    ) -> None:
        self._repository = repository
        self._tags = tags

    async def get_by_character(self, character_id: int) -> list[Emotion]:
        """Возвращает все эмоции персонажа по всем его спрайтам.

        :param character_id: id персонажа.
        :return: список эмоций с тегами.
        """
        return await self._repository.get_by_character(character_id)

    async def get_tags_by_character(self, character_id: int) -> EmotionTags:
        """Возвращает доступные персонажу emotion-теги, разделённые по роли.

        :param character_id: id персонажа.
        :return: базовые эмоции и модификаторы отдельными списками.
        """
        tags = await self._repository.get_tags_by_character(character_id)
        return EmotionTags(
            base=[tag for tag in tags if tag.kind is TagKind.BASE],
            modifiers=[tag for tag in tags if tag.kind is TagKind.MODIFIER],
        )

    async def match(
        self,
        character_id: int,
        tag_slugs: list[str],
        sprite_id: int | None = None,
    ) -> Emotion | None:
        """Подбирает самую подходящую эмоцию персонажа по тегам-смыслам.

        :param character_id: id персонажа.
        :param tag_slugs: slug'и тегов (ровно один base + 0..N modifier).
        :param sprite_id: id спрайта; если задан, эмоции этого спрайта в приоритете.
        :return: лучшая эмоция или None, если подходящей нет.
        """
        tags = await self._tags.get_by_slugs(tag_slugs)
        emotions = await self._repository.get_by_character(character_id)
        return best_emotion(emotions, tag_slugs, tags, sprite_id)

    async def match_batch(
        self, queries: list[EmotionMatchQuery]
    ) -> dict[int, Emotion | None]:
        """Подбирает лучшую эмоцию для каждого персонажа из батча.

        :param queries: список запросов (персонаж + теги).
        :return: словарь character_id -> лучшая эмоция (None, если не найдено).
        """
        if not queries:
            return {}

        all_slugs = {slug for query in queries for slug in query.tags}
        tags = await self._tags.get_by_slugs(list(all_slugs))

        character_ids = [query.character_id for query in queries]
        emotions = await self._repository.get_by_character_ids(character_ids)

        # Группируем эмоции по character_id, сохраняя порядок из БД
        emotions_by_character: dict[int, list[Emotion]] = {}
        for emotion in emotions:
            emotions_by_character.setdefault(emotion.character_id, []).append(emotion)

        return {
            query.character_id: best_emotion(
                emotions_by_character.get(query.character_id, []),
                query.tags,
                tags,
                query.sprite_id,
            )
            for query in queries
        }
