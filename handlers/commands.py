import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from handlers.keyboards import (
    get_main_menu_keyboard, get_settings_keyboard, get_help_keyboard,
    get_model_selection_keyboard, get_chat_followup_keyboard, get_model_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message):
    is_owner = message.from_user and message.from_user.id == config.owner_id
    user_name = message.from_user.first_name or "رفیق"
    
    if is_owner:
        welcome_text = (
            f"👑 <b>سلام جواد جان! خالق من خوش اومدی 😍</b>\n\n"
            f"من جاوید هستم، همشیرِ کد تو. هر چی خواستی بپرس، کد بنویس، تحلیل کن، یا فقط باهام گپ بزن.\n\n"
            f"<b>🎯 دستورات مخصوص تو:</b>\n"
            f"• /model — عوض کردن مدل AI با کیبورد شیک\n"
            f"• /clear — ریست حافظه\n"
            f"• /owner — اطلاعات خالق (همون تو!)\n"
            f"• /me — پروفایل تو\n"
            f"• /help — راهنمای کامل\n\n"
            f"دستور بده، بی‌زحمت! 🚀"
        )
    else:
        welcome_text = (
            f"🌟 <b>سلام {user_name}! من جاوید هستم — رفیق هوش‌مصنوعی‌ت.</b>\n\n"
            f"💬 در چت خصوصی باهام حرف بزن، در گروه‌ها منشن کن یا ریپلای بده.\n"
            f"🧠 مکالمه‌هامو یادم میره: کد نویسی، ترجمه، تحلیل، خلاقیت و...\n\n"
            f"<b>🎯 دستورات سریع:</b>\n"
            f"• /model — تغییر مدل AI با دکمه‌های شیک\n"
            f"• /clear — پاک کردن حافظه چت\n"
            f"• /search <جستجو> — سرچ وب با Tavily\n"
            f"• /owner — خالق من رو ببین\n"
            f"• /me — پروفایل خودت\n"
            f"• /help — راهنمای کامل\n\n"
            f"چه کاری از دست من برمیاد؟ 😊"
        )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>📖 راهنمای جاوید</b>\n\n"
        "• <b>چت خصوصی:</b> مستقیم باهام حرف بزن، جواب می‌دم.\n"
        "• <b>گروه‌ها:</b> منشن کن (@username) یا به پیام‌ام ریپلای بده.\n"
        "• <b>فرمت‌دهی:</b> **پرش**, *کج*, `کد`, لیست‌ها و... رو می‌فهمم.\n"
        "• <b>حافظه:</b> /clear برای ریست کردن گفتگو.\n"
        "• <b>مدل‌ها:</b> /model برای انتخاب مدل AI (GLM-5.2، Nemotron، GPT-4o، Claude...).\n"
        "• <b>جستجو:</b> /search یا بپرس \"آخرین قیمت بیت‌کوین چقدره؟\" — خودم سرچ می‌کنم.\n"
        "• <b>عکس:</b> عکس بفرست، توضیح می‌دم، متن استخراج می‌کنم (OCR)، ترجمه می‌کنم.\n\n"
        "⚡ <b>نکته:</b> من فارسی母语 هستم، انگلیسی هم بلدم، ادم‌هم باهام راحت باش!\n\n"
        "کمکی لازم داری؟ /model بزن یه مدل انتخاب کن و شروع کن! 🚀",
        parse_mode="HTML",
        reply_markup=get_help_keyboard()
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


@router.message(Command("model"))
async def cmd_model(message: Message, ai_client):
    """Show model selection menu with inline keyboard."""
    current_model = ai_client.model if ai_client else "gpt-4o"
    await message.answer(
        f"🤖 <b>انتخاب مدل AI</b>\n\n"
        f"مدل فعلی: <code>{current_model}</code>\n\n"
        f"یه مدل انتخاب کن تا بلافاصله عوض بشه:",
        parse_mode="HTML",
        reply_markup=get_model_keyboard(current_model)
    )


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


# Callback handlers for inline keyboards
@router.callback_query(lambda c: c.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery):
    is_owner = callback.from_user.id == config.owner_id
    if is_owner:
        text = (
            f"👑 <b>سلام جواد جان! خالق من خوش اومدی 😍</b>\n\n"
            f"من جاوید هستم، همشیرِ کد تو. هر چی خواستی بپرس، کد بنویس، تحلیل کن، یا فقط باهام گپ بزن.\n\n"
            f"<b>🎯 دستورات مخصوص تو:</b>\n"
            f"• /model — عوض کردن مدل AI با کیبورد شیک\n"
            f"• /clear — ریست حافظه\n"
            f"• /owner — اطلاعات خالق (همون تو!)\n"
            f"• /me — پروفایل تو\n"
            f"• /help — راهنمای کامل\n\n"
            f"دستور بده، بی‌زحمت! 🚀"
        )
    else:
        user_name = callback.from_user.first_name or "رفیق"
        text = (
            f"🌟 <b>سلام {user_name}! من جاوید هستم — رفیق هوش‌مصنوعی‌ت.</b>\n\n"
            f"💬 در چت خصوصی باهام حرف بزن، در گروه‌ها منشن کن یا ریپلای بده.\n"
            f"🧠 مکالمه‌هامو یادم میره: کد نویسی، ترجمه، تحلیل، خلاقیت و...\n\n"
            f"<b>🎯 دستورات سریع:</b>\n"
            f"• /model — تغییر مدل AI با دکمه‌های شیک\n"
            f"• /clear — پاک کردن حافظه چت\n"
            f"• /search <جستجو> — سرچ وب با Tavily\n"
            f"• /owner — خالق من رو ببین\n"
            f"• /me — پروفایل خودت\n"
            f"• /help — راهنمای کامل\n\n"
            f"چه کاری از دست من برمیاد؟ 😊"
        )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:help")
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>📖 راهنمای جاوید</b>\n\n"
        "• <b>چت خصوصی:</b> مستقیم باهام حرف بزن، جواب می‌دم.\n"
        "• <b>گروه‌ها:</b> منشن کن (@username) یا به پیام‌ام ریپلای بده.\n"
        "• <b>فرمت‌دهی:</b> **پرش**, *کج*, `کد`, لیست‌ها و... رو می‌فهمم.\n"
        "• <b>حافظه:</b> /clear برای ریست کردن گفتگو.\n"
        "• <b>مدل‌ها:</b> /model برای انتخاب مدل AI (GLM-5.2، Nemotron، Llama، Gemma...).\n"
        "• <b>جستجو:</b> /search یا بپرس \"آخرین قیمت بیت‌کوین چقدره؟\" — خودم سرچ می‌کنم.\n"
        "• <b>عکس:</b> عکس بفرست، توضیح می‌دم، متن استخراج می‌کنم (OCR)، ترجمه می‌کنم.\n\n"
        "⚡ <b>نکته:</b> من فارسی مادربازی هستم، انگلیسی هم بلدم، آدم‌هم باهام راحت باش!\n\n"
        "کمکی لازم داری؟ /model بزن یه مدل انتخاب کن و شروع کن! 🚀",
        parse_mode="HTML",
        reply_markup=get_help_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:model")
async def cb_model_menu(callback: CallbackQuery, ai_client):
    """Show model selection from main menu."""
    current = ai_client.model if ai_client else "z-ai/glm-5.2"
    from handlers.keyboards import get_model_display_name
    current_display = get_model_display_name(current)
    await callback.message.edit_text(
        f"🤖 <b>انتخاب مدل AI</b>\n\n"
        f"مدل فعلی: <b>{current_display}</b>\n"
        f"<code>{current}</code>\n\n"
        f"یه مدل انتخاب کن تا بلافاصله عوض بشه:",
        parse_mode="HTML",
        reply_markup=get_model_keyboard(current)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:settings")
async def cb_settings(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>تنظیمات</b>\n\nتجربه جاوید رو سفارشی کن:",
        parse_mode="HTML",
        reply_markup=get_settings_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "settings:model")
async def cb_model_selection(callback: CallbackQuery, ai_client):
    current = ai_client.model if ai_client else "z-ai/glm-5.2"
    from handlers.keyboards import get_model_display_name
    current_display = get_model_display_name(current)
    await callback.message.edit_text(
        f"🤖 <b>انتخاب مدل AI</b>\n\n"
        f"مدل فعلی: <b>{current_display}</b>\n"
        f"<code>{current}</code>\n\n"
        f"یه مدل انتخاب کن تا بلافاصله عوض بشه:",
        parse_mode="HTML",
        reply_markup=get_model_selection_keyboard(current)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("model:"))
async def cb_model_selected(callback: CallbackQuery, ai_client):
    model_id = callback.data.split(":", 1)[1]
    ai_client.model = model_id
    logger.info("Model changed to %s by user %s via callback", model_id, callback.from_user.id)
    
    # Find model display name from keyboards
    from handlers.keyboards import get_model_display_name
    display_name = get_model_display_name(model_id)
    
    await callback.message.edit_text(
        f"✅ <b>مدل با موفقیت تغییر کرد!</b>\n\n"
        f"مدل فعال: <b>{display_name}</b>\n"
        f"<code>{model_id}</code>\n\n"
        f"حالا می‌تونی از مدل جدید استفاده کنی 😊",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")],
            [InlineKeyboardButton(text="🤖 انتخاب مدل دیگر", callback_data="settings:model")],
        ])
    )
    await callback.answer(f"✅ به {display_name} تغییر کرد")


@router.callback_query(lambda c: c.data == "menu:owner")
async def cb_owner(callback: CallbackQuery):
    is_owner = callback.from_user.id == config.owner_id
    if is_owner:
        text = (
            f"👑 <b>Owner Info</b>\n\n"
            f"Name: {config.owner_name}\n"
            f"User ID: <code>{config.owner_id}</code>\n"
            f"Role: Creator & Developer\n\n"
            f"Hey {config.owner_name}! 👋 You built me. That's pretty cool."
        )
    else:
        text = (
            f"👑 <b>Owner Info</b>\n\n"
            f"Name: {config.owner_name}\n"
            f"User ID: <code>{config.owner_id}</code>\n"
            f"Role: Creator & Developer\n\n"
            f"He's the one who brought me to life. 🤖✨"
        )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:profile")
async def cb_profile(callback: CallbackQuery):
    user = callback.from_user
    is_owner = user.id == config.owner_id
    roles = []
    if is_owner:
        roles.append("👑 Owner (Creator & Developer)")
    
    await callback.message.edit_text(
        f"👤 <b>Your Profile</b>\n\n"
        f"Name: {user.first_name or 'N/A'} {user.last_name or ''}\n"
        f"Username: @{user.username or 'N/A'}\n"
        f"User ID: <code>{user.id}</code>\n"
        f"Language: {user.language_code or 'N/A'}\n"
        f"Premium: {'✅ Yes' if user.is_premium else '❌ No'}\n"
        f"Role: {', '.join(roles) if roles else '🙋 User'}",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:chat")
async def cb_chat(callback: CallbackQuery):
    await callback.message.edit_text(
        "💬 <b>Start Chatting</b>\n\nJust send me a message! I'll reply naturally.\n\n"
        "<b>Tips:</b>\n"
        "• Ask questions, get explanations\n"
        "• Request code, writing, analysis\n"
        "• Follow up — I remember context\n"
        "• Use /clear to reset\n\n"
        "What's on your mind? 🤔",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:image")
async def cb_image(callback: CallbackQuery):
    await callback.message.edit_text(
        "🖼️ <b>Image Analysis</b>\n\nSend me a photo and I'll:\n"
        "• Describe what's in it\n"
        "• Extract text (OCR) — just ask \"read this\"\n"
        "• Analyze charts, diagrams, screenshots\n"
        "• Translate text in images\n\n"
        "Just drop an image in chat! 📸",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:search")
async def cb_search(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 <b>Web Search</b>\n\nNeed fresh info? Use:\n"
        "<code>/search your query here</code>\n\n"
        "Or just ask me — I'll search when needed.\n\n"
        "<b>Best for:</b>\n"
        "• Current news, prices, weather\n"
        "• Recent tech docs, releases\n"
        "• Live sports, crypto, stocks\n\n"
        "What do you want to find? 🔎",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("help:"))
async def cb_help_detail(callback: CallbackQuery):
    topic = callback.data.split(":", 1)[1]
    texts = {
        "chat": (
            "💬 <b>Chat Tips</b>\n\n"
            "• Be specific — better questions = better answers\n"
            "• Follow up! I remember our conversation\n"
            "• Ask for code, explanations, creative writing\n"
            "• Use <code>/clear</code> when switching topics\n"
            "• Works in Persian, English, or mixed"
        ),
        "image": (
            "🖼️ <b>Image Tips</b>\n\n"
            "• Send any photo — I'll analyze it\n"
            "• Add a caption for specific questions\n"
            "• Say \"read this\" or \"متن رو بخون\" for OCR\n"
            "• Works with screenshots, docs, handwriting\n"
            "• I can translate text in images too"
        ),
        "search": (
            "🔍 <b>Search Tips</b>\n\n"
            "• Use <code>/search query</code> for manual search\n"
            "• I auto-search for current info when needed\n"
            "• Say \"more results\" or \"بیشتر\" for deep search\n"
            "• Best for: news, prices, recent docs"
        ),
        "commands": (
            "⚙️ <b>All Commands</b>\n\n"
            "/start — Main menu\n"
            "/help — This guide\n"
            "/clear — Reset chat memory\n"
            "/setmodel <name> — Change AI model\n"
            "/search <query> — Web search\n"
            "/owner — Creator info\n"
            "/me — Your profile"
        ),
    }
    await callback.message.edit_text(
        texts.get(topic, "Topic not found"),
        parse_mode="HTML",
        reply_markup=get_help_keyboard()
    )
    await callback.answer()


# Chat follow-up callbacks
@router.callback_query(lambda c: c.data == "chat:regenerate")
async def cb_regenerate(callback: CallbackQuery, ai_client, history_manager, bot_username: str, system_prompt: str):
    """Regenerate the last response."""
    # Get last user message from history
    history = await history_manager.get_history(callback.message.chat.id)
    if not history:
        await callback.answer("Nothing to regenerate.", show_alert=True)
        return
    
    # Find last user message
    last_user_msg = None
    for msg in reversed(history):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break
    
    if not last_user_msg:
        await callback.answer("Nothing to regenerate.", show_alert=True)
        return
    
    await callback.message.edit_text("🔄 <b>Regenerating...</b>", parse_mode="HTML")
    
    messages = [{"role": "system", "content": system_prompt}]
    # Add history without the last assistant message
    for msg in history:
        if not (msg["role"] == "assistant" and msg == history[-1]):
            messages.append(msg)
    
    full_response = ""
    async for partial in ai_client.get_response(messages):
        full_response = partial
    
    if not full_response:
        full_response = "I couldn't generate a response."
    
    # Update history
    await history_manager.clear(callback.message.chat.id)
    for msg in history[:-1]:  # Exclude last assistant message
        await history_manager.add_message(callback.message.chat.id, msg["role"], msg["content"])
    await history_manager.add_message(callback.message.chat.id, "assistant", full_response)
    
    await callback.message.edit_text(full_response, parse_mode="Markdown", reply_markup=get_chat_followup_keyboard())
    await callback.answer("Regenerated!")


@router.callback_query(lambda c: c.data == "chat:search")
async def cb_chat_search(callback: CallbackQuery):
    """Trigger web search for the last topic."""
    await callback.message.edit_text(
        "🔍 <b>Web Search</b>\n\nUse <code>/search your query</code> or just ask me to search for something specific!",
        parse_mode="HTML",
        reply_markup=get_chat_followup_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "chat:explain")
async def cb_chat_explain(callback: CallbackQuery, ai_client, history_manager, bot_username: str, system_prompt: str):
    """Ask AI to explain more about the last topic."""
    history = await history_manager.get_history(callback.message.chat.id)
    if not history:
        await callback.answer("No context to explain.", show_alert=True)
        return
    
    # Get last exchange
    last_user = ""
    last_assistant = ""
    for msg in reversed(history):
        if msg["role"] == "user" and not last_user:
            last_user = msg["content"]
        elif msg["role"] == "assistant" and not last_assistant:
            last_assistant = msg["content"]
        if last_user and last_assistant:
            break
    
    if not last_user:
        await callback.answer("Nothing to explain.", show_alert=True)
        return
    
    await callback.message.edit_text("💡 <b>Explaining more...</b>", parse_mode="HTML")
    
    messages = [
        {"role": "system", "content": system_prompt + "\n\nThe user wants a more detailed explanation of the previous response. Elaborate with examples, analogies, and deeper details."},
        {"role": "user", "content": last_user},
        {"role": "assistant", "content": last_assistant},
        {"role": "user", "content": "Explain this in more detail with examples and deeper analysis."}
    ]
    
    full_response = ""
    async for partial in ai_client.get_response(messages):
        full_response = partial
    
    if not full_response:
        full_response = "I couldn't generate a detailed explanation."
    
    await history_manager.add_message(callback.message.chat.id, "user", "Explain more detail")
    await history_manager.add_message(callback.message.chat.id, "assistant", full_response)
    
    await callback.message.edit_text(full_response, parse_mode="Markdown", reply_markup=get_chat_followup_keyboard())
    await callback.answer("Explained!")


@router.callback_query(lambda c: c.data == "chat:translate")
async def cb_chat_translate(callback: CallbackQuery, ai_client, history_manager, bot_username: str, system_prompt: str):
    """Translate the last response."""
    history = await history_manager.get_history(callback.message.chat.id)
    if not history:
        await callback.answer("Nothing to translate.", show_alert=True)
        return
    
    # Get last assistant message
    last_assistant = ""
    for msg in reversed(history):
        if msg["role"] == "assistant":
            last_assistant = msg["content"]
            break
    
    if not last_assistant:
        await callback.answer("Nothing to translate.", show_alert=True)
        return
    
    await callback.message.edit_text("🌐 <b>Translating...</b>", parse_mode="HTML")
    
    messages = [
        {"role": "system", "content": system_prompt + "\n\nTranslate the following text to the user's language (detect from context). Keep formatting."},
        {"role": "user", "content": f"Translate this:\n\n{last_assistant}"}
    ]
    
    full_response = ""
    async for partial in ai_client.get_response(messages):
        full_response = partial
    
    if not full_response:
        full_response = "Translation failed."
    
    await history_manager.add_message(callback.message.chat.id, "user", "Translate last response")
    await history_manager.add_message(callback.message.chat.id, "assistant", full_response)
    
    await callback.message.edit_text(full_response, parse_mode="Markdown", reply_markup=get_chat_followup_keyboard())
    await callback.answer("Translated!")


@router.callback_query(lambda c: c.data == "chat:clear")
async def cb_chat_clear(callback: CallbackQuery, history_manager, bot_username: str):
    """Clear conversation history."""
    await history_manager.clear(callback.message.chat.id)
    await callback.message.edit_text(
        "🧹 <b>Done!</b> Conversation history wiped clean. Fresh start!",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer("History cleared!")