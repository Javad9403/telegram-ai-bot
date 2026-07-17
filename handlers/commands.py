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
        "👋 <b>Hey there! I'm جاوید — your AI sidekick.</b>\n\n"
        "I chat in private, hang out in groups, and actually remember our conversation.\n"
        "In groups, just @mention me or reply to my messages.\n\n"
        "<b>Quick commands:</b>\n"
        "• /start — This friendly intro\n"
        "• /help — Tips & tricks\n"
        "• /clear — Fresh slate (forget our chat)\n"
        "• /setmodel <model> — Swap AI brain (e.g., <code>gpt-4o</code>)\n"
        "• /search <query> — Web search via Tavily\n"
        "• /owner — Meet my creator\n"
        "• /me — Your profile card\n\n"
        "Ready when you are! 🚀",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>📖 How to جاوید</b>\n\n"
        "• <b>Private chat:</b> Just talk. I'll reply.\n"
        "• <b>Groups:</b> @mention me or reply to my message.\n"
        "• <b>Markdown:</b> I speak **bold**, *italic*, `code`, and more.\n"
        "• <b>/clear</b> — Wipe my memory of this chat.\n"
        "• <b>/setmodel</b> — Try different AI models.\n"
        "• <b>/search</b> — Need fresh info? I'll browse the web.\n"
        "• <b>/owner</b> / <b>/me</b> — Fun little info cards.\n\n"
        "Stuck? Ping my developer — he's pretty cool. 😉",
        parse_mode="HTML",
    )


@router.message(Command("clear", "clearhistory"))
async def cmd_clear(message: Message, history_manager, bot_username: str):
    await history_manager.clear(message.chat.id)
    logger.info("History cleared for chat %s", message.chat.id)
    await message.answer("🧹 <b>Done!</b> Conversation history wiped clean. Fresh start!", parse_mode="HTML")


@router.message(Command("setmodel"))
async def cmd_setmodel(message: Message, ai_client):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: <code>/setmodel <model_name></code>\nExample: <code>/setmodel gpt-4o</code>", parse_mode="HTML")
        return
    model_name = args[1].strip()
    ai_client.model = model_name
    logger.info("Model changed to %s by user %s in chat %s", model_name, message.from_user.id, message.chat.id)
    await message.answer(f"🧠 <b>Brain swapped!</b> Now running <code>{model_name}</code>.", parse_mode="HTML")


@router.message(Command("owner"))
async def cmd_owner(message: Message):
    is_owner = message.from_user and message.from_user.id == config.owner_id
    if is_owner:
        await message.answer(
            f"👑 <b>Owner Info</b>\n\n"
            f"Name: {config.owner_name}\n"
            f"User ID: <code>{config.owner_id}</code>\n"
            f"Role: Creator & Developer\n\n"
            f"Hey {config.owner_name}! 👋 You built me. That's pretty cool.",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"👑 <b>Owner Info</b>\n\n"
            f"Name: {config.owner_name}\n"
            f"User ID: <code>{config.owner_id}</code>\n"
            f"Role: Creator & Developer\n\n"
            f"He's the one who brought me to life. 🤖✨",
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
        f"👤 <b>Your Profile</b>\n\n"
        f"Name: {user.first_name or 'N/A'} {user.last_name or ''}\n"
        f"Username: @{user.username or 'N/A'}\n"
        f"User ID: <code>{user.id}</code>\n"
        f"Language: {user.language_code or 'N/A'}\n"
        f"Premium: {'✅ Yes' if user.is_premium else '❌ No'}\n"
        f"Role: {', '.join(roles) if roles else '🙋 User'}",
        parse_mode="HTML",
    )