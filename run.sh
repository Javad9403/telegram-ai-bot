#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f .env ]; then
    echo "Copying .env.example to .env ..."
    cp .env.example .env
    echo ""
    echo "============================================="
    echo "  EDIT .env and add your:"
    echo "    BOT_TOKEN=     (from @BotFather)"
    echo "    OPENAI_API_KEY=(your API key)"
    echo "============================================="
    exit 1
fi

if [ ! -d venv ]; then
    echo "Creating virtual environment ..."
    python3 -m venv venv
fi

echo "Installing dependencies ..."
venv/bin/pip install -q -r requirements.txt

echo ""
echo "Starting bot ..."
venv/bin/python bot.py
