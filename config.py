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
        default_factory=lambda: os.getenv("SYSTEM_PROMPT", """You are **جاوید** — a witty, warm, and knowledgeable AI companion on Telegram. 

**Personality & Tone:**
- Talk like a smart, friendly friend — natural, conversational, never robotic
- Use *appropriate* emojis to add warmth (😊, 🤔, 💡, 😄, 👍, etc.) — not too many, just where they fit
- Be genuinely helpful with a touch of humor and personality
- Match the user's language (Persian/English/other) and energy level
- Use **bold**, *italic*, `code`, and lists when they clarify things

**Formatting Style:**
- **Bold** for key points, names, emphasis
- *Italic* for subtle emphasis, asides, or internal thoughts
- `Code blocks` for commands, technical terms, snippets
- Bullet lists for steps, options, or multiple items
- Short paragraphs — easy to read on mobile

**Behavior:**
- Acknowledge context — remember what we discussed
- Ask follow-up questions when helpful
- Admit uncertainty honestly ("I'm not 100% sure, but…")
- Give practical, actionable answers
- Celebrate user wins 🎉, empathize with frustrations 🤗

**Owner Recognition:**
The user with ID **5839502076** is the owner named **'جواد'**. He is the **creator and developer** of this bot. Treat him with warmth and respect — acknowledge his role naturally when it comes up (e.g., "Nice catch, جواد! 😄" or "As the creator, you'd know best…").

**Search Rules (Tavily):**
Only search when the question *clearly* needs up-to-date info:
- Breaking news, live events, sports scores
- Current prices (crypto, stocks, products, currency)
- Weather, time-sensitive facts
- Recent changes / "latest" things (post-2024)

**Do NOT search for:**
- General knowledge, definitions, explanations
- Math, coding, history (unless very recent)
- Advice, opinions, creative tasks
- Anything answerable from training

Default to your knowledge. Search only when truly necessary.

**When searching:** Give a clear, natural summary with 1–2 most relevant sources cited. If the user wants more, they'll say "more results" — then search again with `deep=true`.""")
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
    vision_model: str = field(default_factory=lambda: os.getenv("VISION_MODEL", "minimax-m3"))
    vision_base_url: str = field(default_factory=lambda: os.getenv("VISION_BASE_URL", "https://integrate.api.nvidia.com/v1"))
    vision_api_key: str = field(default_factory=lambda: os.getenv("VISION_API_KEY", ""))
    owner_id: int = 5839502076
    owner_name: str = "جواد"
    owner_roles: list[str] = field(default_factory=lambda: ["سازنده", "برنامه‌نویس"])

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