import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import config

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
        "/search <query> - Search the web (Tavily)\n"
        "/owner - Show owner information\n"
        "/me - Show your user info",
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
        "• Use /search <query> to search the web (Tavily).\n"
        "• Use /owner to see owner info.\n"
        "• Use /me to see your user info.\n\n"
        "Need more help? Contact the bot administrator.",
        parse_mode="HTML",
    )


@router.message(Command("clear", "clearhistory"))
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


@router.message(Command("owner"))
async def cmd_owner(message: Message):
    is_owner = message.from_user and message.from_user.id == config.owner_id
    if is_owner:
        await message.answer(
            f"👑 <b>Owner Information</b>\n\n"
            f"Name: {config.owner_name}\n"
            f"User ID: {config.owner_id}\n"
            f"Role: Creator & Developer\n\n"
            f"Hello, {config.owner_name}! You are the owner of this bot.",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"👑 <b>Owner Information</b>\n\n"
            f"Name: {config.owner_name}\n"
            f"User ID: {config.owner_id}\n"
            f"Role: Creator & Developer",
            parse_mode="HTML",
        )


@router.message(Command("me"))
async def cmd_me(message: Message):
    user = message.from_user
    is_owner = user and user.id == config.owner_id
    roles = []
    if is_owner:
        roles.append("👑 Owner (Creator & Developer)")
    
    await message.answer(
        f"👤 <b>Your Information</b>\n\n"
        f"Name: {user.first_name or 'N/A'} {user.last_name or ''}\n"
        f"Username: @{user.username or 'N/A'}\n"
        f"User ID: {user.id}\n"
        f"Language: {user.language_code or 'N/A'}\n"
        f"Is Premium: {user.is_premium}\n"
        f"Roles: {', '.join(roles) if roles else 'User'}",
        parse_mode="HTML",
    )