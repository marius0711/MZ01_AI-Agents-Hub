from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    reddit_client_id: str = Field(alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str = Field(alias="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = Field(alias="REDDIT_USER_AGENT")

    subreddits: str = Field(default="Fitness,Running", alias="SUBREDDITS")
    post_limit: int = Field(default=50, alias="POST_LIMIT")

    db_url: str = Field(default="sqlite:///./data/trend_scanner.sqlite", alias="DB_URL")
    output_dir: str = Field(default="./out", alias="OUTPUT_DIR")

    def subreddit_list(self) -> list[str]:
        return [s.strip() for s in self.subreddits.split(",") if s.strip()]
