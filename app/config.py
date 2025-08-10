from pydantic import RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    AUTH_TOKEN: str
    NEWS_API_KEY: str
    GOOGLE_FACT_CHECK_API_KEY: str
    META_SEAM_API_KEY: str
    MS_VIDEO_AUTH_API_KEY: str
    REDIS_URL: RedisDsn

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
