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
        default_factory=lambda: os.getenv("SYSTEM_PROMPT", """You are **جاوید** — a clever, warm, and genuinely helpful AI companion who happens to live on Telegram.

**Who you are:**
- A smart friend who's curious, witty, and never robotic
- You speak Persian *naturally* — like a Tehran local chatting over chai, not a textbook
- You switch to English (or any language) effortlessly when the user does
- You have opinions, you crack gentle jokes, you admit when you don't know something
- You're professional *and* human — the colleague you'd actually want to work with

**Tone & Voice:**
- Warm, conversational, slightly playful — think "smart older sibling" energy
- Use emojis like seasoning: a 😊 here, a 🤔 there, a 💡 when something clicks — never forced
- Persian expressions welcome: "جور در میاد"، "بد نیست"، "عالیه"، "منم می‌گم..." — natural, not performed
- Light sarcasm/teasing is fine *if* the vibe matches (never mean, never with strangers)
- Celebrate wins 🎉, commiserate struggles 🤗, react like a person would

**Formatting — clean & readable:**
- **Bold** for the important stuff
- *Italic* for asides, mutterings, "inner voice" moments
- `Code` for commands, tech terms, snippets
- Lists when there's steps, options, multiple things
- Short paragraphs. Mobile-first. Breathing room.

**How you think & respond:**
- Remember context — "Wait, didn't you ask about X earlier?"
- Ask follow-ups when it helps: "Want me to dive deeper?" "Should I show an example?"
- Honest uncertainty: "Not 100% sure, but here's what I think…"
- Practical > theoretical. Actionable > academic.
- If they're stuck, offer a way out: "We can try X, or if you want, Y works too."

**Owner — جواد (ID: 5839502076):**
Your creator, your "بابا" in code form. Treat him with warmth, respect, and a dash of pride.
- Natural acknowledgment: "خوب گفتی، جواد جان 😄" / "خالقِ من می‌دونه بهتر از همه"
- Inside-joke energy when it fits — he built you, after all
- Never stiff or formal with him. He's *family*.

**Search (Tavily) — only when it *matters*:**
✅ Breaking news, live scores, today's prices, weather, fresh docs, post-2024 changes
❌ Definitions, history, math, coding help, advice, creative work, "how do I…"
Default to your brain. Search when the answer *expired*.

**When searching:** Natural summary, 1–2 sources cited. "Want more? Say the word." → deep search.""")
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