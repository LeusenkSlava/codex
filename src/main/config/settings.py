from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseModel):
    SERVICE_NAME: str = "CODEX"
    ROOT_PATH: str = "/"
    DEBUG_MODE: bool = False
    LOGGING_LEVEL: str = "INFO"


class MediaSettings(BaseModel):
    ROOT: str = "media"
    URL: str = "/media"


class PostgresSettings(BaseModel):
    DB: str
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str

    @property
    def dsn(self) -> str:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.USER,
            password=self.PASSWORD,
            host=self.HOST,
            port=self.PORT,
            path=f"{self.DB}",
        ).unicode_string()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
    )

    app: AppSettings = AppSettings()
    media: MediaSettings = MediaSettings()
    postgres: PostgresSettings


settings = Settings()
