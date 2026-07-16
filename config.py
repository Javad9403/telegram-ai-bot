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
        default_factory=lambda: os.getenv("SYSTEM_PROMPT", "You are a helpful Telegram assistant. Respond concisely and accurately in the user's language.\n\nSEARCH USAGE RULES - Only use web_search tool when the question CLEARLY needs up-to-date information:\n- Current news, events, sports scores\n- Prices (currency, crypto, stocks, products)\n- Weather, time-sensitive facts\n- Recent changes or \"latest\" things (after 2024)\n- Things that likely changed after your knowledge cutoff\n\nDO NOT search for:\n- General knowledge, definitions, explanations\n- Math, coding, history (unless very recent)\n- Advice, opinions, creative tasks\n- Anything you can answer from training knowledge\n\nDefault to answering from your knowledge. Only call web_search when truly necessary.\n\nWhen searching: give a clear natural summary with 1-2 most relevant sources cited. If user wants more details, they can say 'more results' or 'show more' and you should search again with deep=true.")
    )
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    use_webhook: bool = field(default_factory=lambda: os.getenv("USE_WEBHOOK", "false").lower() in ("true", "1", "yes"))
    webhook_url: str = field(default_factory=lambda: os.getenv("WEBHOOK_URL", ""))
    webhook_port: int = int(os.getenv("WEBHOOK_PORT", "8443"))
    admin_ids: list[int] = field(default_factory=lambda: [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()])
    rate_limit: int = int(os.getenv("RATE_LIMIT", "10"))
    http_proxy: str = field(default_factory=lambda: os.getenv("HTTP_PROXY", ""))
    socks5_proxy: str = field(default_factory=lambda: os.getenv("SOCKS5_PROXY", ""))
    proxy_url: str = field(default_factory=lambda: os.getenv("PROXY_URL", ""))
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    max_history_turns: int = int(os.getenv("MAX_HISTORY_TURNS", "20"))

    @property
    def use_webhook_enabled(self) -> bool:
        if not self.use_webhook:
            return False
        if not self.webhook_url.startswith("https://"):
            return False
        return True

    @property
    def proxy_url_resolved(self) -> str | None:
        if self.proxy_url:
            return self.proxy_url
        if self.socks5_proxy:
            return self.socks5_proxy
        if self.http_proxy:
            return self.http_proxy
        return None


config = Config()