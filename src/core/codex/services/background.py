from dataclasses import dataclass

from src.core.codex.interfaces import (
    BackgroundRepositoryProtocol,
    TagRepositoryProtocol,
)
from src.core.codex.models.enum import TagKind, TagType
from src.core.codex.models.tag import Tag
from src.core.codex.models.universe import Background

# Задник размечен тегами двух типов (location и time_of_day), но роль тега
# задаётся полем kind: ровно один base (сама локация) + 0..N modifier
# (время суток, внутри/снаружи, свет, люди и т.п.).
BACKGROUND_TAG_TYPES = (TagType.LOCATION, TagType.TIME_OF_DAY)


@dataclass(frozen=True, slots=True)
class BackgroundMatchQuery:
    """Запрос на подбор задника: вселенная + набор тегов-смыслов (slug)."""

    universe_id: int
    tags: list[str]


@dataclass(frozen=True, slots=True)
class BackgroundTags:
    """Доступные вселенной теги задников, разделённые по роли."""

    base: list[Tag]
    modifiers: list[Tag]


class BackgroundService:
    """Сервис задников."""

    def __init__(
        self,
        repository: BackgroundRepositoryProtocol,
        tags: TagRepositoryProtocol,
    ) -> None:
        self._repository = repository
        self._tags = tags

    async def get_by_universe(self, universe_id: int) -> list[Background]:
        """Возвращает все задники вселенной.

        :param universe_id: id вселенной.
        :return: список задников с тегами.
        """
        return await self._repository.get_by_universe(universe_id)

    async def get_tags_by_universe(self, universe_id: int) -> BackgroundTags:
        """Возвращает доступные вселенной теги задников, разделённые по роли.

        :param universe_id: id вселенной.
        :return: базовые локации и модификаторы отдельными списками.
        """
        tags = await self._repository.get_tags_by_universe(universe_id)
        return BackgroundTags(
            base=[tag for tag in tags if tag.kind is TagKind.BASE],
            modifiers=[tag for tag in tags if tag.kind is TagKind.MODIFIER],
        )

    async def match(self, universe_id: int, tag_slugs: list[str]) -> Background | None:
        """Подбирает самый подходящий задник вселенной по тегам-смыслам.

        :param universe_id: id вселенной.
        :param tag_slugs: slug'и тегов (ровно один base + 0..N modifier).
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
        """Подбирает лучший задник для каждой вселенной из батча.

        :param queries: список запросов (вселенная + теги).
        :return: словарь universe_id -> лучший задник (None, если не найдено).
        """
        if not queries:
            return {}

        all_slugs = {slug for query in queries for slug in query.tags}
        tags = await self._tags.get_by_slugs_and_types(
            list(all_slugs), BACKGROUND_TAG_TYPES
        )

        universe_ids = list({query.universe_id for query in queries})
        backgrounds = await self._repository.get_by_universe_ids(universe_ids)

        # Группируем задники по universe_id, сохраняя порядок из БД
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

        Приоритет: совпадение base-тега (обязателен и должен быть ровно один) ->
        число совпавших modifier -> меньше лишних modifier -> меньший id.
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

        # base обязателен и должен быть ровно один
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
