# Telegram AI Chatbot

A production-ready Telegram bot powered by AI. Supports private chats and groups with mention/reply detection, conversation history, and streaming responses.

## Features

- **AI Chat** — Connects to any OpenAI-compatible API (OpenAI, Groq, Ollama, OpenRouter, etc.)
- **Group Support** — Responds when mentioned (@bot) or replied to; ignores other messages
- **Conversation Memory** — Redis-backed history (falls back to SQLite or in-memory)
- **Streaming** — Real-time response generation with typing indicator
- **Configurable** — System prompt, model, rate limiting, admin IDs
- **Polling & Webhook** — Supports both modes, configurable via env

## Setup

### 1. Get a Bot Token

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the API token you receive
4. **Disable privacy mode**: BotFather → `/mybots` → your bot → Settings → Group Privacy → Disable

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token from BotFather | — |
| `OPENAI_BASE_URL` | AI API endpoint | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | AI API key | — |
| `AI_MODEL` | Model name | `gpt-4o` |
| `SYSTEM_PROMPT` | Bot personality | (see .env.example) |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `WEBHOOK_URL` | Webhook URL (leave empty for polling) | — |
| `WEBHOOK_PORT` | Webhook listen port | `8443` |
| `RATE_LIMIT` | Messages per minute per chat | `10` |

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run

**Polling** (default, no webhook URL set):
```bash
python bot.py
```

**Webhook** (set `WEBHOOK_URL` in .env):
```bash
python bot.py
```

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose up -d --build
```

This starts both the bot and a Redis instance.

### VPS with systemd

```bash
# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo cat > /etc/systemd/system/telegram-ai-bot.service <<EOF
[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram-ai-bot
ExecStart=/usr/bin/python bot.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable telegram-ai-bot
sudo systemctl start telegram-ai-bot
```

### Railway / Render

1. Push to a GitHub repo
2. Connect to Railway or Render
3. Set the environment variables in the dashboard
4. Deploy

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and usage |
| `/help` | Detailed help |
| `/clear` | Clear conversation history |
| `/setmodel <model>` | Change AI model (e.g., `/setmodel gpt-4o`) |

## License

MIT
