"""Регистрация всех sqladmin-вьюх и каталога кастомных шаблонов."""

from pathlib import Path

from src.outbound.admin.importer.view import ImporterView
from src.outbound.admin.views.characters import (
    CharacterAdmin,
    EmotionAdmin,
    OutfitAdmin,
    SpriteAdmin,
)
from src.outbound.admin.views.tags import TagAdmin
from src.outbound.admin.views.universes import BackgroundAdmin, UniverseAdmin

# Каталог с кастомными шаблонами админки (страница импорта).
ADMIN_TEMPLATES_DIR = str(Path(__file__).resolve().parent.parent / "templates")

ADMIN_VIEWS = [
    UniverseAdmin,
    CharacterAdmin,
    SpriteAdmin,
    OutfitAdmin,
    EmotionAdmin,
    BackgroundAdmin,
    TagAdmin,
    ImporterView,
]
