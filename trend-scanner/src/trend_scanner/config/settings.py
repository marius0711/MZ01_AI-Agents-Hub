from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Reddit JSON ingestion needs a transparent UA
    reddit_user_agent: str = Field(alias="REDDIT_USER_AGENT")

    # OAuth fields (optional for later)
    reddit_client_id: str | None = Field(default=None, alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str | None = Field(default=None, alias="REDDIT_CLIENT_SECRET")

    # Project settings
    subreddits: str = Field(default="Fitness,Running", alias="SUBREDDITS")
    post_limit: int = Field(default=50, alias="POST_LIMIT")
    db_url: str = Field(default="sqlite:///./data/trend_scanner.sqlite", alias="DB_URL")
    output_dir: str = Field(default="./out", alias="OUTPUT_DIR")

    # Slack (Webhook optional, Bot token for file upload + threads)
    slack_webhook_url: str | None = Field(default=None, alias="SLACK_WEBHOOK_URL")
    slack_bot_token: str | None = Field(default=None, alias="SLACK_BOT_TOKEN")
    slack_channel_id: str | None = Field(default=None, alias="SLACK_CHANNEL_ID")

    def subreddit_list(self) -> list[str]:
        return [s.strip() for s in self.subreddits.split(",") if s.strip()]
