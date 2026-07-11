import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Hello! I'm an AI-powered Telegram bot.\n\n"
        "I can chat with you in private messages, and I can join groups.\n"
        "In groups, tag me with @bot_username or reply to my messages to get my attention.\n\n"
        "<b>Commands:</b>\n"
        "/start - Show this message\n"
        "/help - Show help\n"
        "/clear - Clear conversation history\n"
        "/setmodel <model> - Change AI model (e.g., /setmodel gpt-4o)\n"
        "/photo <query> - Search photos\n"
        "/music <query> - Search music\n"
        "/search <query> - Search the web",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>How to use this bot:</b>\n\n"
        "• <b>Private chat</b>: Just send me a message and I'll respond.\n"
        "• <b>Groups</b>: Mention me with @bot_username or reply to one of my messages.\n"
        "• I support Markdown formatting in responses.\n"
        "• Use /clear to reset the conversation.\n"
        "• Use /setmodel to switch AI models.\n"
        "• Use /photo <query> to search for photos (Unsplash).\n"
        "• Use /music <query> to search for music (Deezer, YouTube).\n"
        "• Use /search <query> to search the web (Serper, Google, Bing, Brave, DuckDuckGo).\n\n"
        "Need more help? Contact the bot administrator.",
        parse_mode="HTML",
    )


@router.message(Command("clear"))
async def cmd_clear(message: Message, history_manager, bot_username: str):
    await history_manager.clear(message.chat.id)
    logger.info("History cleared for chat %s", message.chat.id)
    await message.answer("Conversation history has been cleared.")


@router.message(Command("setmodel"))
async def cmd_setmodel(message: Message, ai_client):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /setmodel <model_name>\nExample: /setmodel gpt-4o")
        return
    model_name = args[1].strip()
    ai_client.model = model_name
    logger.info("Model changed to %s by user %s in chat %s", model_name, message.from_user.id, message.chat.id)
    await message.answer(f"AI model changed to <b>{model_name}</b>.", parse_mode="HTML")
