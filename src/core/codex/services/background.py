from dataclasses import dataclass

from src.core.codex.interfaces import (
    BackgroundRepositoryProtocol,
    TagRepositoryProtocol,
)
from src.core.codex.models.enum import TagKind, TagType
from src.core.codex.models.tag import Tag
from src.core.codex.models.universe import Background

# Задники тегируются только этими типами: location и time_of_day. Роль тега
# задаёт kind: base (сама локация) или modifier (время суток, внутри/снаружи и т.п.).
BACKGROUND_TAG_TYPES = (TagType.LOCATION, TagType.TIME_OF_DAY)


@dataclass(frozen=True, slots=True)
class BackgroundMatchQuery:
    """Запрос на подбор задника: вселенная и slug'и тегов."""

    universe_id: int
    tags: list[str]


@dataclass(frozen=True, slots=True)
class BackgroundTags:
    """Теги задников вселенной, разложенные по роли."""

    base: list[Tag]
    modifiers: list[Tag]


class BackgroundService:
    """Сервис задников: выдача и подбор по тегам."""

    def __init__(
        self,
        repository: BackgroundRepositoryProtocol,
        tags: TagRepositoryProtocol,
    ) -> None:
        self._repository = repository
        self._tags = tags

    async def get_by_universe(self, universe_id: int) -> list[Background]:
        """Все задники вселенной.

        :param universe_id: id вселенной.
        :return: задники с тегами и звуком, по возрастанию id.
        """
        return await self._repository.get_by_universe(universe_id)

    async def get_tags_by_universe(self, universe_id: int) -> BackgroundTags:
        """Теги задников вселенной, разложенные по роли.

        :param universe_id: id вселенной.
        :return: `base`- и `modifier`-теги отдельными списками.
        """
        tags = await self._repository.get_tags_by_universe(universe_id)
        return BackgroundTags(
            base=[tag for tag in tags if tag.kind is TagKind.BASE],
            modifiers=[tag for tag in tags if tag.kind is TagKind.MODIFIER],
        )

    async def match(self, universe_id: int, tag_slugs: list[str]) -> Background | None:
        """Подбирает задник вселенной по тегам.

        :param universe_id: id вселенной.
        :param tag_slugs: slug'и тегов: ровно один `base` + 0..N `modifier`.
        :return: лучший задник или None, если подходящего нет.
        """
        tags = await self._tags.get_by_slugs_and_types(
            tag_slugs, BACKGROUND_TAG_TYPES
        )
        backgrounds = await self._repository.get_by_universe(universe_id)
        return self._best_match(backgrounds, tag_slugs, tags)

    async def match_batch(
        self, queries: list[BackgroundMatchQuery]
    ) -> dict[int, Background | None]:
        """Подбирает задник для каждой вселенной из батча.

        Задники и теги загружаются одним запросом на всех.

        :param queries: запросы (вселенная + теги).
        :return: `universe_id` → задник или None, если ничего не подошло.
        """
        if not queries:
            return {}

        all_slugs = {slug for query in queries for slug in query.tags}
        tags = await self._tags.get_by_slugs_and_types(
            list(all_slugs), BACKGROUND_TAG_TYPES
        )

        universe_ids = list({query.universe_id for query in queries})
        backgrounds = await self._repository.get_by_universe_ids(universe_ids)

        backgrounds_by_universe: dict[int, list[Background]] = {}
        for background in backgrounds:
            backgrounds_by_universe.setdefault(background.universe_id, []).append(
                background
            )

        return {
            query.universe_id: self._best_match(
                backgrounds_by_universe.get(query.universe_id, []),
                query.tags,
                tags,
            )
            for query in queries
        }

    @staticmethod
    def _best_match(
        backgrounds: list[Background],
        tag_slugs: list[str],
        tags_by_slug: dict[str, Tag],
    ) -> Background | None:
        """Выбирает лучший задник.

        Подходят только задники с нужным `base`-тегом. Среди них побеждает
        задник с большим числом совпавших `modifier`, при равенстве — с меньшим
        числом лишних `modifier`, затем — с меньшим `id`.
        """
        base_slugs = {
            slug
            for slug in tag_slugs
            if (tag := tags_by_slug.get(slug)) and tag.kind is TagKind.BASE
        }
        modifier_slugs = {
            slug
            for slug in tag_slugs
            if (tag := tags_by_slug.get(slug)) and tag.kind is TagKind.MODIFIER
        }

        # Без единственного base-тега подбирать не по чему.
        if len(base_slugs) != 1:
            return None
        base_slug = next(iter(base_slugs))

        best: Background | None = None
        best_key: tuple[int, int, int] | None = None
        for background in backgrounds:
            if base_slug not in {
                tag.slug for tag in background.tags if tag.kind is TagKind.BASE
            }:
                continue

            background_modifiers = {
                tag.slug for tag in background.tags if tag.kind is TagKind.MODIFIER
            }
            matched = len(modifier_slugs & background_modifiers)
            extra = len(background_modifiers - modifier_slugs)
            key = (matched, -extra, -background.id)

            if best_key is None or key > best_key:
                best = background
                best_key = key

        return best
