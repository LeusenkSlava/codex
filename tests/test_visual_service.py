from __future__ import annotations

from src.core.codex.models.character import Emotion, Outfit, Sprite
from src.core.codex.models.enum import TagKind, TagType
from src.core.codex.models.tag import Tag
from src.core.codex.services.visual import (
    OutfitEmotion,
    OutfitTagWithEmotions,
    VisualService,
)


# --------------------------------------------------------------------------- #
# Доменные фабрики
# --------------------------------------------------------------------------- #
def make_tag(slug: str, tag_type: TagType, kind: TagKind | None) -> Tag:
    return Tag(id=hash((tag_type, slug)) % 100_000, type=tag_type, slug=slug, name=slug, kind=kind)


def emotion_tag(slug: str, kind: TagKind) -> Tag:
    return make_tag(slug, TagType.EMOTION, kind)


def outfit_tag(slug: str, kind: TagKind = TagKind.BASE) -> Tag:
    return make_tag(slug, TagType.OUTFIT_STYLE, kind)


def make_sprite(sprite_id: int, character_id: int) -> Sprite:
    return Sprite(
        id=sprite_id,
        character_id=character_id,
        slug=f"sprite-{sprite_id}",
        description="",
        asset_key=f"sprite-{sprite_id}",
    )


def make_outfit(outfit_id: int, sprite_id: int, *tags: Tag) -> Outfit:
    return Outfit(
        id=outfit_id,
        sprite_id=sprite_id,
        slug=f"outfit-{outfit_id}",
        name=f"outfit-{outfit_id}",
        asset_key=f"outfit-{outfit_id}",
        tags=list(tags),
    )


def make_emotion(
    emotion_id: int, sprite_id: int, character_id: int, *tags: Tag
) -> Emotion:
    return Emotion(
        id=emotion_id,
        sprite_id=sprite_id,
        character_id=character_id,
        slug=f"emotion-{emotion_id}",
        name=f"emotion-{emotion_id}",
        asset_key=f"emotion-{emotion_id}",
        tags=list(tags),
    )


# --------------------------------------------------------------------------- #
# Фейковые репозитории (in-memory)
# --------------------------------------------------------------------------- #
class FakeSpriteRepository:
    def __init__(self, sprites: list[Sprite]) -> None:
        self._sprites = list(sprites)

    async def get_by_character(self, character_id: int) -> list[Sprite]:
        return [s for s in self._sprites if s.character_id == character_id]

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Sprite]:
        ids = set(character_ids)
        return [s for s in self._sprites if s.character_id in ids]

    async def get_by_id(self, sprite_id: int) -> Sprite | None:
        return next((s for s in self._sprites if s.id == sprite_id), None)


class FakeOutfitRepository:
    def __init__(
        self, outfits: list[Outfit], sprite_to_character: dict[int, int]
    ) -> None:
        self._outfits = list(outfits)
        self._sprite_to_character = sprite_to_character

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Outfit]:
        ids = set(character_ids)
        return [
            o
            for o in self._outfits
            if self._sprite_to_character.get(o.sprite_id) in ids
        ]

    async def get_by_character_and_tag(
        self, character_id: int, tag_slug: str, *, include_tags: bool = True
    ) -> list[Outfit]:
        return [
            o
            for o in self._outfits
            if self._sprite_to_character.get(o.sprite_id) == character_id
            and any(
                t.type is TagType.OUTFIT_STYLE and t.slug == tag_slug for t in o.tags
            )
        ]

    async def get_by_sprite(self, sprite_id: int) -> list[Outfit]:
        return [o for o in self._outfits if o.sprite_id == sprite_id]

    async def get_by_sprite_and_tag(
        self, sprite_id: int, tag_slug: str
    ) -> Outfit | None:
        for o in self._outfits:
            if o.sprite_id == sprite_id and any(
                t.type is TagType.OUTFIT_STYLE and t.slug == tag_slug for t in o.tags
            ):
                return o
        return None

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        seen: dict[str, Tag] = {}
        for o in self._outfits:
            if self._sprite_to_character.get(o.sprite_id) != character_id:
                continue
            for t in o.tags:
                if t.type is TagType.OUTFIT_STYLE:
                    seen.setdefault(t.slug, t)
        return list(seen.values())


class FakeEmotionRepository:
    def __init__(self, emotions: list[Emotion]) -> None:
        self._emotions = list(emotions)

    async def get_by_character(self, character_id: int) -> list[Emotion]:
        return [e for e in self._emotions if e.character_id == character_id]

    async def get_by_character_ids(self, character_ids: list[int]) -> list[Emotion]:
        ids = set(character_ids)
        return [e for e in self._emotions if e.character_id in ids]

    async def get_by_sprite(self, sprite_id: int) -> list[Emotion]:
        return [e for e in self._emotions if e.sprite_id == sprite_id]

    async def get_tags_by_character(self, character_id: int) -> list[Tag]:
        seen: dict[str, Tag] = {}
        for e in self._emotions:
            if e.character_id != character_id:
                continue
            for t in e.tags:
                if t.type is TagType.EMOTION:
                    seen.setdefault(t.slug, t)
        return list(seen.values())


class FakeTagRepository:
    def __init__(self, tags: list[Tag]) -> None:
        self._tags = {t.slug: t for t in tags}

    async def get_by_type(self, tag_type: TagType) -> list[Tag]:
        return [t for t in self._tags.values() if t.type == tag_type]

    async def get_by_slugs(self, slugs: list[str]) -> dict[str, Tag]:
        return {s: self._tags[s] for s in slugs if s in self._tags}

    async def get_by_slugs_and_types(
        self, slugs: list[str], tag_types: tuple[TagType, ...]
    ) -> dict[str, Tag]:
        allowed = set(tag_types)
        return {
            s: t
            for s, t in self._tags.items()
            if s in slugs and t.type in allowed
        }


def build_service(
    *,
    sprites: list[Sprite],
    outfits: list[Outfit],
    emotions: list[Emotion],
    tags: list[Tag],
) -> VisualService:
    sprite_to_character = {s.id: s.character_id for s in sprites}
    return VisualService(
        FakeOutfitRepository(outfits, sprite_to_character),
        FakeSpriteRepository(sprites),
        FakeEmotionRepository(emotions),
        FakeTagRepository(tags),
    )


# --------------------------------------------------------------------------- #
# get_outfits_with_emotions_grouped
# --------------------------------------------------------------------------- #
async def test_grouped_empty_character_ids_returns_empty_dict() -> None:
    service = build_service(sprites=[], outfits=[], emotions=[], tags=[])

    assert await service.get_outfits_with_emotions_grouped([]) == {}


async def test_grouped_dedups_and_orders_base_before_modifier() -> None:
    happy = emotion_tag("happy", TagKind.BASE)
    blush = emotion_tag("blush", TagKind.MODIFIER)
    sad = emotion_tag("sad", TagKind.BASE)
    casual = outfit_tag("casual")
    formal = outfit_tag("formal")

    sprites = [make_sprite(1, 1), make_sprite(2, 1)]
    outfits = [
        make_outfit(1, 1, casual),
        make_outfit(2, 1, casual),
        make_outfit(3, 2, formal),
    ]
    emotions = [
        make_emotion(1, 1, 1, happy, blush),
        make_emotion(2, 1, 1, happy, blush),  # дубль тегов того же спрайта
        make_emotion(3, 2, 1, sad),
    ]
    service = build_service(
        sprites=sprites,
        outfits=outfits,
        emotions=emotions,
        tags=[happy, blush, sad, casual, formal],
    )

    result = await service.get_outfits_with_emotions_grouped([1])

    casual_group = next(g for g in result[1] if g.outfit_tag == "casual")
    formal_group = next(g for g in result[1] if g.outfit_tag == "formal")

    assert casual_group == OutfitTagWithEmotions(
        outfit_tag="casual",
        name="casual",
        emotions=[
            OutfitEmotion(slug="happy", name="happy", kind=TagKind.BASE),
            OutfitEmotion(slug="blush", name="blush", kind=TagKind.MODIFIER),
        ],
    )
    assert formal_group.emotions == [
        OutfitEmotion(slug="sad", name="sad", kind=TagKind.BASE)
    ]


async def test_grouped_keeps_tag_without_emotions() -> None:
    casual = outfit_tag("casual")
    sprites = [make_sprite(1, 1)]
    outfits = [make_outfit(1, 1, casual)]
    service = build_service(
        sprites=sprites, outfits=outfits, emotions=[], tags=[casual]
    )

    result = await service.get_outfits_with_emotions_grouped([1])

    assert result[1] == [
        OutfitTagWithEmotions(outfit_tag="casual", name="casual", emotions=[])
    ]


async def test_grouped_ignores_modifier_outfit_tags() -> None:
    casual_base = outfit_tag("casual", TagKind.BASE)
    casual_modifier = outfit_tag("casual", TagKind.MODIFIER)
    sprites = [make_sprite(1, 1)]
    outfits = [make_outfit(1, 1, casual_base, casual_modifier)]
    service = build_service(
        sprites=sprites, outfits=outfits, emotions=[], tags=[casual_base]
    )

    result = await service.get_outfits_with_emotions_grouped([1])

    assert [g.outfit_tag for g in result[1]] == ["casual"]


# --------------------------------------------------------------------------- #
# match
# --------------------------------------------------------------------------- #
def _match_fixture() -> VisualService:
    happy = emotion_tag("happy", TagKind.BASE)
    sad = emotion_tag("sad", TagKind.BASE)
    casual = outfit_tag("casual")

    sprites = [make_sprite(1, 1), make_sprite(2, 1)]
    outfits = [
        make_outfit(5, 1, casual),  # спрайт 1, наряд id 5
        make_outfit(10, 2, casual),  # спрайт 2, наряд id 10 (больше)
    ]
    emotions = [
        make_emotion(1, 1, 1, happy),
        make_emotion(2, 2, 1, sad),
    ]
    return build_service(
        sprites=sprites,
        outfits=outfits,
        emotions=emotions,
        tags=[happy, sad, casual],
    )


async def test_match_prefers_sprite_with_emotion_over_greater_outfit_id() -> None:
    service = _match_fixture()

    result = await service.match(1, "casual", ["happy"])

    assert result is not None
    assert result.sprite_asset_key == "sprite-1"
    assert result.outfit_asset_key == "outfit-5"
    assert result.emotion_asset_key == "emotion-1"


async def test_match_falls_back_to_greatest_outfit_id_without_emotion() -> None:
    service = _match_fixture()

    result = await service.match(1, "casual", ["angry"])

    assert result is not None
    assert result.sprite_asset_key == "sprite-2"
    assert result.outfit_asset_key == "outfit-10"
    assert result.emotion_asset_key is None


async def test_match_returns_none_when_outfit_missing() -> None:
    service = _match_fixture()

    assert await service.match(1, "formal", ["happy"]) is None


async def test_match_picks_greatest_outfit_id_per_sprite_regardless_of_order() -> None:
    happy = emotion_tag("happy", TagKind.BASE)
    casual = outfit_tag("casual")

    sprites = [make_sprite(1, 1)]
    # Репозиторий отдаёт наряды в перемешанном порядке.
    outfits = [
        make_outfit(3, 1, casual),
        make_outfit(7, 1, casual),
        make_outfit(1, 1, casual),
    ]
    emotions = [make_emotion(1, 1, 1, happy)]
    service = build_service(
        sprites=sprites, outfits=outfits, emotions=emotions, tags=[happy, casual]
    )

    result = await service.match(1, "casual", ["happy"])

    assert result is not None
    assert result.outfit_asset_key == "outfit-7"
