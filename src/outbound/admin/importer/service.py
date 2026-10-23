import io
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.datastructures import UploadFile

from src.core.codex.models.enum import TagType
from src.outbound.admin.importer.manifest import Manifest
from src.outbound.database.models import (
    CharacterModel,
    EmotionModel,
    OutfitModel,
    SpriteModel,
    TagModel,
    UniverseModel,
)
from src.outbound.media import media_storage
from src.outbound.media.storage import IMAGE_EXTENSIONS

IMAGE_FOLDERS = {
    "sprite": "sprites",
    "outfit": "outfits",
    "emotion": "emotions",
}


@dataclass
class ImportReport:
    """Результат импорта."""

    created_characters: int = 0
    created_sprites: int = 0
    created_outfits: int = 0
    created_emotions: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class ImportService:
    """Импорт персонажей из архива с манифестом."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def import_zip(self, upload: UploadFile) -> ImportReport:
        raw = await upload.read()
        try:
            archive = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile:
            return ImportReport(errors=["Файл не является корректным ZIP-архивом."])

        with archive:
            manifest = self._parse_manifest(archive)
            if manifest is None:
                return ImportReport(
                    errors=[
                        "В архиве нет manifest.json или он повреждён/не соответствует схеме."
                    ]
                )

            async with self._session_factory() as session:
                return await self._import(archive, manifest, session)

    def _parse_manifest(self, archive: zipfile.ZipFile) -> Manifest | None:
        """Читает и валидирует manifest.json из архива.

        :return: манифест или None, если файла нет или он невалиден.
        """
        try:
            text = archive.read("manifest.json").decode("utf-8")
        except KeyError as e:
            print(e)
            return None

        try:
            return Manifest.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as e:
            print(e)
            return None

    async def _import(
        self, archive: zipfile.ZipFile, manifest: Manifest, session: AsyncSession
    ) -> ImportReport:
        errors: list[str] = []

        if manifest.version != 1:
            errors.append(
                f"Неподдерживаемая версия манифеста {manifest.version!r}, ожидалась 1."
            )

        universe = await session.scalar(
            select(UniverseModel).where(UniverseModel.slug == manifest.universe_slug)
        )
        if universe is None:
            errors.append(f"Вселенная {manifest.universe_slug!r} не найдена.")
        else:
            await self._validate_db_conflicts(manifest, universe, session, errors)

        # Теги: все slug манифеста резолвим одним запросом, потом проверяем типы.
        tag_slugs = self._collect_tag_slugs(manifest)
        tags_by_slug: dict[str, list[TagModel]] = {}
        if tag_slugs:
            result = await session.scalars(
                select(TagModel).where(TagModel.slug.in_(tag_slugs))
            )
            for tag in result:
                tags_by_slug.setdefault(tag.slug, []).append(tag)

        self._validate_tags(manifest, tags_by_slug, errors)
        self._validate_conflicts(manifest, errors)
        self._validate_images(archive, manifest, errors)

        if universe is None or errors:
            return ImportReport(errors=errors)

        report = ImportReport()
        saved_urls: list[str] = []
        try:
            for character_entry in manifest.characters:
                character = CharacterModel(
                    universe_id=universe.id,
                    slug=character_entry.slug,
                    name=character_entry.name,
                    description=character_entry.description,
                    gender=character_entry.gender,
                    speech_style=character_entry.speech_style,
                    tags=self._tags_for(
                        character_entry.tags, TagType.ARCHETYPE, tags_by_slug
                    ),
                )
                session.add(character)
                report.created_characters += 1

                for sprite_entry in character_entry.sprites:
                    sprite = SpriteModel(
                        character=character,
                        slug=sprite_entry.slug,
                        description=sprite_entry.description,
                        asset_key=await self._save_image(
                            archive, sprite_entry.image, "sprite", saved_urls
                        ),
                        tags=self._tags_for(sprite_entry.tags, None, tags_by_slug),
                    )
                    session.add(sprite)
                    report.created_sprites += 1

                    for outfit_entry in sprite_entry.outfits:
                        outfit = OutfitModel(
                            sprite=sprite,
                            slug=outfit_entry.slug,
                            name=outfit_entry.name,
                            asset_key=await self._save_image(
                                archive, outfit_entry.image, "outfit", saved_urls
                            ),
                            tags=self._tags_for(
                                outfit_entry.tags, TagType.OUTFIT_STYLE, tags_by_slug
                            ),
                        )
                        session.add(outfit)
                        report.created_outfits += 1

                    for emotion_entry in sprite_entry.emotions:
                        emotion = EmotionModel(
                            sprite=sprite,
                            slug=emotion_entry.slug,
                            name=emotion_entry.name,
                            asset_key=await self._save_image(
                                archive, emotion_entry.image, "emotion", saved_urls
                            ),
                            tags=self._tags_for(
                                emotion_entry.tags, TagType.EMOTION, tags_by_slug
                            ),
                        )
                        session.add(emotion)
                        report.created_emotions += 1

            await session.commit()
        except Exception as exc:  # noqa: BLE001 — возвращаем ошибку в отчёт
            await session.rollback()
            for url in saved_urls:
                media_storage.delete(url)
            return ImportReport(errors=[f"Не удалось импортировать: {exc}"])

        return report

    # --- Валидация -----------------------------------------------------

    @staticmethod
    def _collect_tag_slugs(manifest: Manifest) -> set[str]:
        slugs: set[str] = set()
        for character in manifest.characters:
            slugs.update(character.tags)
            for sprite in character.sprites:
                slugs.update(sprite.tags)
                for outfit in sprite.outfits:
                    slugs.update(outfit.tags)
                for emotion in sprite.emotions:
                    slugs.update(emotion.tags)
        return slugs

    @staticmethod
    def _validate_tags(
        manifest: Manifest,
        tags_by_slug: dict[str, list[TagModel]],
        errors: list[str],
    ) -> None:
        """Проверяет, что все теги существуют и имеют правильный тип."""

        def check(slug: str, expected: TagType | None, where: str) -> None:
            variants = tags_by_slug.get(slug, [])
            if not variants:
                errors.append(f"{where}: тег {slug!r} не найден.")
                return
            if expected is not None and not any(t.type == expected for t in variants):
                actual = ", ".join(sorted({t.type.value for t in variants}))
                errors.append(
                    f"{where}: тег {slug!r} имеет тип(ы) {actual}, "
                    f"ожидался {expected.value!r}."
                )

        for character in manifest.characters:
            for slug in character.tags:
                check(slug, TagType.ARCHETYPE, f"персонаж {character.slug!r}")
            for sprite in character.sprites:
                for slug in sprite.tags:
                    check(
                        slug,
                        None,
                        f"персонаж {character.slug!r} → спрайт {sprite.slug!r}",
                    )
                for outfit in sprite.outfits:
                    for slug in outfit.tags:
                        check(
                            slug,
                            TagType.OUTFIT_STYLE,
                            f"персонаж {character.slug!r} → спрайт {sprite.slug!r} "
                            f"→ одежда {outfit.slug!r}",
                        )
                for emotion in sprite.emotions:
                    for slug in emotion.tags:
                        check(
                            slug,
                            TagType.EMOTION,
                            f"персонаж {character.slug!r} → спрайт {sprite.slug!r} "
                            f"→ эмоция {emotion.slug!r}",
                        )

    @staticmethod
    async def _validate_db_conflicts(
        manifest: Manifest,
        universe: UniverseModel,
        session: AsyncSession,
        errors: list[str],
    ) -> None:
        """Проверяет, что персонажи манифеста ещё не существуют во вселенной."""
        slugs = [character.slug for character in manifest.characters]
        result = await session.scalars(
            select(CharacterModel.slug).where(
                CharacterModel.universe_id == universe.id,
                CharacterModel.slug.in_(slugs),
            )
        )
        existing = set(result)
        for character in manifest.characters:
            if character.slug in existing:
                errors.append(
                    f"Персонаж {character.slug!r} уже существует "
                    f"во вселенной {manifest.universe_slug!r}."
                )

    @staticmethod
    def _validate_conflicts(manifest: Manifest, errors: list[str]) -> None:
        """Проверяет дубликаты slug внутри манифеста (и по персонажу)."""

        seen_characters: set[str] = set()
        for character in manifest.characters:
            if character.slug in seen_characters:
                errors.append(f"Дублируется slug персонажа {character.slug!r}.")
            seen_characters.add(character.slug)

            seen_sprites: set[str] = set()
            for sprite in character.sprites:
                if sprite.slug in seen_sprites:
                    errors.append(
                        f"Персонаж {character.slug!r}: дублируется slug спрайта {sprite.slug!r}."
                    )
                seen_sprites.add(sprite.slug)

                seen_outfits: set[str] = set()
                seen_emotions: set[str] = set()
                for outfit in sprite.outfits:
                    if outfit.slug in seen_outfits:
                        errors.append(
                            f"Персонаж {character.slug!r} → спрайт {sprite.slug!r}: "
                            f"дублируется slug одежды {outfit.slug!r}."
                        )
                    seen_outfits.add(outfit.slug)
                for emotion in sprite.emotions:
                    if emotion.slug in seen_emotions:
                        errors.append(
                            f"Персонаж {character.slug!r} → спрайт {sprite.slug!r}: "
                            f"дублируется slug эмоции {emotion.slug!r}."
                        )
                    seen_emotions.add(emotion.slug)

    @staticmethod
    def _validate_images(
        archive: zipfile.ZipFile, manifest: Manifest, errors: list[str]
    ) -> None:
        """Проверяет наличие файлов картинок и их расширения."""

        names = set(archive.namelist())
        allowed = IMAGE_EXTENSIONS

        def check(image: str, where: str) -> None:
            if image not in names:
                errors.append(f"{where}: файл {image!r} не найден в архиве.")
                return
            ext = Path(image).suffix.lower()
            if ext not in allowed:
                errors.append(
                    f"{where}: файл {image!r} имеет недопустимый формат {ext!r}."
                )

        for character in manifest.characters:
            for sprite in character.sprites:
                check(
                    sprite.image,
                    f"персонаж {character.slug!r} → спрайт {sprite.slug!r}",
                )
                for outfit in sprite.outfits:
                    check(
                        outfit.image,
                        f"персонаж {character.slug!r} → спрайт {sprite.slug!r} "
                        f"→ одежда {outfit.slug!r}",
                    )
                for emotion in sprite.emotions:
                    check(
                        emotion.image,
                        f"персонаж {character.slug!r} → спрайт {sprite.slug!r} "
                        f"→ эмоция {emotion.slug!r}",
                    )

    # --- Создание ------------------------------------------------------

    @staticmethod
    def _tags_for(
        slugs: list[str],
        expected: TagType | None,
        tags_by_slug: dict[str, list[TagModel]],
    ) -> list[TagModel]:
        """Возвращает ORM-теги по slug; теги уже проверены на существование/тип."""
        result: list[TagModel] = []
        for slug in slugs:
            variants = tags_by_slug[slug]
            if expected is None:
                result.append(variants[0])
            else:
                result.append(next(t for t in variants if t.type == expected))
        return result

    @staticmethod
    async def _save_image(
        archive: zipfile.ZipFile,
        image_path: str,
        kind: str,
        saved_urls: list[str],
    ) -> str:
        """Сохраняет картинку из архива в нужную папку медиа."""
        url = await media_storage.save_bytes(
            filename=Path(image_path).name,
            folder=IMAGE_FOLDERS[kind],
            content=archive.read(image_path),
        )
        saved_urls.append(url)
        return url
