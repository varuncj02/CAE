from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        str_strip_whitespace=True,
        strict=False,
    )

    INFLECTION_API_KEY: str
    INFLECTION_BASE_URL: str
    INFLECTION_MODEL: str
    LLM_API_KEY: str
    LLM_API_BASE_URL: str
    LLM_MODEL_NAME: str
    EMBEDDING_MODEL_API_KEY: str
    EMBEDDING_MODEL_BASE_URL: str
    EMBEDDING_MODEL_NAME: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_SECRET: str
    LOG_LEVEL: str | None = "INFO"
    LLM_TIMEOUT_SECONDS: int = 600  # Default 10 minutes, can be overridden by env var


app_settings = Config()
