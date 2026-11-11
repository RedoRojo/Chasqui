from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./chasqui.db"
    embedding_provider: str = "local"  # local | gemini | openai
    gemini_api_key: str = ""
    openai_api_key: str = ""
    daily_scrape_enabled: bool = True
    daily_scrape_hour: int = 6
    daily_scrape_minute: int = 0
    max_articles_per_source: int = 12
    event_similarity_threshold: float = 0.56
    thread_similarity_threshold: float = 0.46

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
