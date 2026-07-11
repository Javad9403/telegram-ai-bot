import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    ai_model: str = field(default_factory=lambda: os.getenv("AI_MODEL", "gpt-4o"))
    system_prompt: str = field(
        default_factory=lambda: os.getenv("SYSTEM_PROMPT", "You are a helpful Telegram assistant. Respond concisely and accurately.")
    )
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    use_webhook: bool = field(default_factory=lambda: os.getenv("USE_WEBHOOK", "false").lower() in ("true", "1", "yes"))
    webhook_url: str = field(default_factory=lambda: os.getenv("WEBHOOK_URL", ""))
    webhook_port: int = int(os.getenv("WEBHOOK_PORT", "8443"))
    admin_ids: list[int] = field(default_factory=lambda: [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()])
    rate_limit: int = int(os.getenv("RATE_LIMIT", "10"))

    # Photo search APIs
    unsplash_access_key: str = field(default_factory=lambda: os.getenv("UNSPLASH_ACCESS_KEY", ""))

    # Music search APIs
    youtube_api_key: str = field(default_factory=lambda: os.getenv("YOUTUBE_API_KEY", ""))

    # Web search APIs
    google_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    google_cx: str = field(default_factory=lambda: os.getenv("GOOGLE_CX", ""))
    bing_api_key: str = field(default_factory=lambda: os.getenv("BING_API_KEY", ""))
    brave_api_key: str = field(default_factory=lambda: os.getenv("BRAVE_API_KEY", ""))
    serper_api_key: str = field(default_factory=lambda: os.getenv("SERPER_API_KEY", ""))

    @property
    def use_webhook_enabled(self) -> bool:
        if not self.use_webhook:
            return False
        if not self.webhook_url.startswith("https://"):
            return False
        return True


config = Config()
