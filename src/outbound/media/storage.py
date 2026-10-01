import uuid
from pathlib import Path

from starlette.datastructures import UploadFile

from src.main.config.settings import settings

ALLOWED_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})


class LocalMediaStorage:
    """Хранилище медиафайлов в локальной папке проекта."""

    def __init__(self, root: Path, base_url: str) -> None:
        self._root = root
        self._base_url = base_url.rstrip("/")

    async def save(self, upload: UploadFile, folder: str) -> str:
        """Сохраняет загруженный файл под уникальным именем.

        :param upload: загруженный файл.
        :param folder: подпапка внутри корня медиа.
        :return: публичный url файла.
        :raises ValueError: если расширение файла не поддерживается.
        """
        ext = Path(upload.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Недопустимый формат файла {ext!r}, разрешены: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        target_dir = self._root / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}{ext}"
        (target_dir / name).write_bytes(await upload.read())
        return f"{self._base_url}/{folder}/{name}"

    def get_path(self, folder: str, filename: str) -> Path | None:
        """Возвращает путь к файлу в хранилище.

        :param folder: подпапка внутри корня медиа.
        :param filename: имя файла.
        :return: путь к файлу или None, если файла нет или путь ведёт за пределы хранилища.
        """
        root = self._root.resolve()
        path = (root / folder / filename).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            return None
        return path

    def delete(self, url: str | None) -> None:
        """Удаляет файл по его url, если он лежит в этом хранилище.

        :param url: url файла.
        """
        if not url or not url.startswith(f"{self._base_url}/"):
            return
        path = self._root / url.removeprefix(f"{self._base_url}/")
        path.unlink(missing_ok=True)

    def delete_unreferenced(self, referenced: set[str]) -> None:
        """Удаляет файлы, на которые больше нет ссылок.

        :param referenced: url всех файлов, которые ещё используются.
        """
        for path in self._root.rglob("*"):
            url = f"{self._base_url}/{path.relative_to(self._root).as_posix()}"
            if path.is_file() and url not in referenced:
                path.unlink(missing_ok=True)


media_storage = LocalMediaStorage(
    root=Path(settings.media.ROOT), base_url=settings.media.URL
)
