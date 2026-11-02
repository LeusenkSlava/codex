from logging.config import fileConfig

from alembic import context

from src.main.config.settings import settings
from src.outbound.database.models.base_model import BaseModel
from src.outbound.database.session import engine

# Конфиг alembic.ini текущего запуска.
config = context.config

# Логирование берём из alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные моделей для автогенерации миграций.
target_metadata = BaseModel.metadata


def do_run_migrations(connection):
    """Запускает миграции на синхронном соединении внутри транзакции."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Запускает миграции без подключения к БД.

    Генерирует SQL в stdout — соединение для этого не нужно.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Запускает миграции через подключение к БД."""
    connectable = engine

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    context.configure(
        url=settings.postgres.dsn,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    import asyncio

    asyncio.run(run_migrations_online())
