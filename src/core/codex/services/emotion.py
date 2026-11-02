from dataclasses import dataclass

from src.core.codex.interfaces import EmotionRepositoryProtocol, TagRepositoryProtocol
from src.core.codex.models.character import Emotion
from src.core.codex.models.enum import TagKind
from src.core.codex.models.tag import Tag


@dataclass(frozen=True, slots=True)
class EmotionMatchQuery:
    """Запрос на подбор эмоции: персонаж, slug'и тегов и необязательный спрайт."""

    character_id: int
    tags: list[str]
    sprite_id: int | None = None


@dataclass(frozen=True, slots=True)
class EmotionTags:
    """Теги эмоций персонажа, разложенные по роли."""

    base: list[Tag]
    modifiers: list[Tag]


def best_emotion(
    emotions: list[Emotion],
    tag_slugs: list[str],
    tags_by_slug: dict[str, Tag],
    sprite_id: int | None = None,
) -> Emotion | None:
    """Выбирает лучшую эмоцию из списка.

    Подходят только эмоции с нужным `base`-тегом. Среди них побеждает эмоция
    указанного `sprite_id`, затем — с большим числом совпавших `modifier`,
    при равенстве — с меньшим числом лишних `modifier`, затем — с меньшим `id`.
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

    # Без единственного base-тега подбирать не по чему.
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
    """Сервис эмоций: выдача и подбор по тегам."""

    def __init__(
        self,
        repository: EmotionRepositoryProtocol,
        tags: TagRepositoryProtocol,
    ) -> None:
        self._repository = repository
        self._tags = tags

    async def get_by_character(self, character_id: int) -> list[Emotion]:
        """Все эмоции персонажа по всем его спрайтам.

        :param character_id: id персонажа.
        :return: эмоции с тегами, по возрастанию id.
        """
        return await self._repository.get_by_character(character_id)

    async def get_tags_by_character(self, character_id: int) -> EmotionTags:
        """Теги эмоций персонажа, разложенные по роли.

        :param character_id: id персонажа.
        :return: `base`- и `modifier`-теги отдельными списками.
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
        """Подбирает эмоцию персонажа по тегам.

        :param character_id: id персонажа.
        :param tag_slugs: slug'и тегов: ровно один `base` + 0..N `modifier`.
        :param sprite_id: если задан, эмоции этого спрайта в приоритете.
        :return: лучшая эмоция или None, если подходящей нет.
        """
        tags = await self._tags.get_by_slugs(tag_slugs)
        emotions = await self._repository.get_by_character(character_id)
        return best_emotion(emotions, tag_slugs, tags, sprite_id)

    async def match_batch(
        self, queries: list[EmotionMatchQuery]
    ) -> dict[int, Emotion | None]:
        """Подбирает эмоцию для каждого персонажа из батча.

        Эмоции и теги загружаются одним запросом на всех.

        :param queries: запросы (персонаж + теги + спрайт).
        :return: `character_id` → эмоция или None, если ничего не подошло.
        """
        if not queries:
            return {}

        all_slugs = {slug for query in queries for slug in query.tags}
        tags = await self._tags.get_by_slugs(list(all_slugs))

        character_ids = [query.character_id for query in queries]
        emotions = await self._repository.get_by_character_ids(character_ids)

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
