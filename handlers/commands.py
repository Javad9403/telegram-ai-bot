import logging
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from handlers.keyboards import (
    get_main_menu_keyboard, get_settings_keyboard, get_help_keyboard,
    get_model_selection_keyboard, get_chat_followup_keyboard, get_model_keyboard,
    get_owner_keyboard, get_profile_keyboard, get_model_changed_keyboard,
    get_model_display_name,
    get_secretary_keyboard, get_secretary_task_keyboard,
    get_secretary_remind_keyboard, get_secretary_note_keyboard,
    get_secretary_calendar_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message):
    is_owner = message.from_user and message.from_user.id == config.owner_id
    user_name = message.from_user.first_name or "رفیق"
    
    if is_owner:
        welcome_text = (
            "👑 <b>سلام جواد جان! خالق من خوش اومدی 😍</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "من <b>جاوید</b> هستم، همشیرِ کد تو.\n"
            "هرچی خواستی بپرس، کد بنویس، تحلیل کن،\n"
            "یا فقط باهام گپ بزن.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 <b>دستورات مخصوص تو:</b>\n"
            "┌────────────────────────┐\n"
            "│  /model    🤖  مدل AI   │\n"
            "│  /clear    🗑️  حافظه    │\n"
            "│  /owner    👑  من        │\n"
            "│  /me       👤  پروفایل  │\n"
            "│  /help     ❓  راهنما   │\n"
            "└────────────────────────┘\n\n"
            "دستور بده، بی‌زحمت! 🚀"
        )
    else:
        current_model = config.ai_model
        model_display = get_model_display_name(current_model)
        welcome_text = (
            f"🌟 <b>سلام {user_name}!</b> من <b>جاوید</b> هستم — رفیق هوش‌مصنوعی‌ت.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 <b>چت خصوصی:</b> مستقیم باهام حرف بزن\n"
            "👥 <b>گروه‌ها:</b> منشن کن (@username) یا ریپلای بده\n"
            "🧠 <b>حافظه:</b> مکالمه‌هامو یادم میره\n"
            "🤖 <b>مدل فعلی:</b> " + model_display + f"\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 <b>دستورات سریع:</b>\n"
            "┌─────────────────────────────┐\n"
            "│  /model      🤖  تغییر مدل   │\n"
            "│  /clear      🗑️  پاک حافظه  │\n"
            "│  /search     🔍  جستجوی وب   │\n"
            "│  /owner      👑  خالق من      │\n"
            "│  /me         👤  پروفایل     │\n"
            "│  /help       ❓  راهنما      │\n"
            "└─────────────────────────────┘\n\n"
            "💡 <b>نکته:</b> عکس هم بفرست، تحلیل می‌کنم!\n\n"
            "چه کاری از دست من برمیاد؟ 😊"
        )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 <b>راهنمای جاوید</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 <b>چت خصوصی:</b> مستقیم باهام حرف بزن، جواب می‌دم.\n"
        "👥 <b>گروه‌ها:</b> منشن کن (@username) یا به پیام‌ام ریپلای بده.\n"
        "🎨 <b>فرمت‌دهی:</b> <b>پرشت</b>, <i>کج</i>, <code>کد</code>, لیست‌ها و... رو می‌فهمم.\n"
        "🧠 <b>حافظه:</b> /clear برای ریست کردن گفتگو.\n"
        "🤖 <b>مدل‌ها:</b> /model برای انتخاب مدل AI (GLM-5.2، Nemotron، Llama، Gemma...).\n"
        "🔍 <b>جستجو:</b> /search یا بپرس \"آخرین قیمت بیت‌کوین چقدره؟\" — خودم سرچ می‌کنم.\n"
        "🖼️ <b>عکس:</b> عکس بفرست، توضیح می‌دم، متن استخراج می‌کنم (OCR)، ترجمه می‌کنم.\n\n"
        "⚡ <b>نکته:</b> من فارسی‌زبانم، انگلیسی هم بلدم، آدم‌هم باهام راحت باش!\n\n"
        "کمکی لازم داری؟ /model بزن یه مدل انتخاب کن و شروع کن! 🚀"
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_help_keyboard())


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
    logger.info("cb_main_menu triggered by user %s", callback.from_user.id)
    try:
        is_owner = callback.from_user.id == config.owner_id
        if is_owner:
            text = (
                "👑 <b>سلام جواد جان! خالق من خوش اومدی 😍</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "من <b>جاوید</b> هستم، همشیرِ کد تو.\n"
                "هرچی خواستی بپرس، کد بنویس، تحلیل کن،\n"
                "یا فقط باهام گپ بزن.\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🎯 <b>دستورات مخصوص تو:</b>\n"
                "┌────────────────────────┐\n"
                "│  /model    🤖  مدل AI   │\n"
                "│  /clear    🗑️  حافظه    │\n"
                "│  /owner    👑  من        │\n"
                "│  /me       👤  پروفایل  │\n"
                "│  /help     ❓  راهنما   │\n"
                "└────────────────────────┘\n\n"
                "دستور بده، بی‌زحمت! 🚀"
            )
        else:
            user_name = callback.from_user.first_name or "رفیق"
            current_model = config.ai_model
            model_display = get_model_display_name(current_model)
            text = (
                f"🌟 <b>سلام {user_name}!</b> من <b>جاوید</b> هستم — رفیق هوش‌مصنوعی‌ت.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💬 <b>چت خصوصی:</b> مستقیم باهام حرف بزن\n"
                "👥 <b>گروه‌ها:</b> منشن کن (@username) یا ریپلای بده\n"
                "🧠 <b>حافظه:</b> مکالمه‌هامو یادم میره\n"
                f"🤖 <b>مدل فعلی:</b> {model_display}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🎯 <b>دستورات سریع:</b>\n"
                "┌─────────────────────────────┐\n"
                "│  /model      🤖  تغییر مدل   │\n"
                "│  /clear      🗑️  پاک حافظه  │\n"
                "│  /search     🔍  جستجوی وب   │\n"
                "│  /owner      👑  خالق من      │\n"
                "│  /me         👤  پروفایل     │\n"
                "│  /help       ❓  راهنما      │\n"
                "└─────────────────────────────┘\n\n"
                "💡 <b>نکته:</b> عکس هم بفرست، تحلیل می‌کنم!\n\n"
                "چه کاری از دست من برمیاد؟ 😊"
            )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logger.error("Error in cb_main_menu: %s", e, exc_info=True)
        await callback.answer("❌ خطا در بازگشت به منو", show_alert=True)
    else:
        await callback.answer()


@router.callback_query(lambda c: c.data == "menu:help")
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text(
        "📖 <b>راهنمای جاوید</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 <b>چت خصوصی:</b> مستقیم باهام حرف بزن، جواب می‌دم.\n"
        "👥 <b>گروه‌ها:</b> منشن کن (@username) یا به پیام‌ام ریپلای بده.\n"
        "🎨 <b>فرمت‌دهی:</b> <b>بولد</b>, <i>ایتالیک</i>, <code>کد</code>, لیست‌ها و...\n"
        "🧠 <b>حافظه:</b> <code>/clear</code> برای ریست کردن گفتگو.\n"
        "🤖 <b>مدل‌ها:</b> <code>/model</code> برای انتخاب مدل AI.\n"
        "🔍 <b>جستجو:</b> <code>/search</code> یا بپرس \"آخرین قیمت بیت‌کوین؟\" — خودم سرچ می‌کنم.\n"
        "🖼️ <b>عکس:</b> عکس بفرست، توضیح می‌دم، OCR می‌کنم، ترجمه می‌کنم.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ <b>نکته:</b> من فارسی‌زبانم، انگلیسی هم بلدم، باهام راحت باش!\n\n"
        "🚀 <b>آمده باش؟</b> <code>/model</code> بزن، مدل انتخاب کن و شروع کن!",
        parse_mode="HTML",
        reply_markup=get_help_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:model")
async def cb_model_menu(callback: CallbackQuery, ai_client):
    """Show model selection from main menu."""
    current = ai_client.model if ai_client else "z-ai/glm-5.2"
    current_display = get_model_display_name(current)
    await callback.message.edit_text(
        f"🤖 <b>انتخاب مدل AI</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <b>مدل فعلی:</b> {current_display}\n"
        f"<code>{current}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"یه مدل انتخاب کن تا بلافاصله عوض بشه:",
        parse_mode="HTML",
        reply_markup=get_model_keyboard(current)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:settings")
async def cb_settings(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>تنظیمات</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "تجربه جاوید رو سفارشی کن:\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML",
        reply_markup=get_settings_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "settings:model")
async def cb_model_selection(callback: CallbackQuery, ai_client):
    current = ai_client.model if ai_client else "z-ai/glm-5.2"
    current_display = get_model_display_name(current)
    await callback.message.edit_text(
        f"🤖 <b>انتخاب مدل AI</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <b>مدل فعلی:</b> {current_display}\n"
        f"<code>{current}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
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
    
    display_name = get_model_display_name(model_id)
    
    await callback.message.edit_text(
        f"✅ <b>مدل با موفقیت تغییر کرد!</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 <b>مدل فعال:</b> {display_name}\n"
        f"<code>{model_id}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"حالا می‌تونی از مدل جدید استفاده کنی 😊",
        parse_mode="HTML",
        reply_markup=get_model_changed_keyboard()
    )
    await callback.answer(f"✅ به {display_name} تغییر کرد")


@router.callback_query(lambda c: c.data == "menu:owner")
async def cb_owner(callback: CallbackQuery):
    is_owner = callback.from_user.id == config.owner_id
    if is_owner:
        text = (
            "👑 <b>اطلاعات خالق</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 <b>نام:</b> {config.owner_name}\n"
            f"🆔 <b>شناسه:</b> <code>{config.owner_id}</code>\n"
            f"🎭 <b>نقش:</b> Creator & Developer\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Hey {config.owner_name}! 👋 تو من رو ساختی. خیلی قشنگه! 😎"
        )
    else:
        text = (
            "👑 <b>اطلاعات خالق</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 <b>نام:</b> {config.owner_name}\n"
            f"🆔 <b>شناسه:</b> <code>{config.owner_id}</code>\n"
            f"🎭 <b>نقش:</b> Creator & Developer\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"او کسیه که من رو به حیات آورد. 🤖✨"
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
        f"👤 <b>پروفایل شما</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>نام:</b> {user.first_name or 'N/A'} {user.last_name or ''}\n"
        f"🔗 <b>یوزرنیم:</b> @{user.username or 'N/A'}\n"
        f"🆔 <b>شناسه:</b> <code>{user.id}</code>\n"
        f"🌐 <b>زبان:</b> {user.language_code or 'N/A'}\n"
        f"⭐ <b>پرمیوم:</b> {'✅ بله' if user.is_premium else '❌ خیر'}\n"
        f"🎭 <b>نقش:</b> {', '.join(roles) if roles else '🙋 کاربر'}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:chat")
async def cb_chat(callback: CallbackQuery):
    await callback.message.edit_text(
        "💬 <b>شروع چت</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "یه پیام بفرست! من به طور طبیعی جواب می‌دم.\n\n"
        "💡 <b>نکات:</b>\n"
        "• سوال بپرس، توضیح بگیر\n"
        "• کد، متن، تحلیل بخواه\n"
        "• ادامه بده — من یادم میره\n"
        "• از <code>/clear</code> برای ریست استفاده کن\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "دارم گوش می‌کنم... 🤔",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:image")
async def cb_image(callback: CallbackQuery):
    await callback.message.edit_text(
        "🖼️ <b>تحلیل عکس</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "یه عکس بفرست و من:\n"
        "• توصیف می‌کنم چیه\n"
        "• متن استخراج می‌کنم (OCR) — بنویس \"متن رو بخون\"\n"
        "• چارت، دیاگرام، اسکرین‌شات تحلیل می‌کنم\n"
        "• متن عکس رو ترجمه می‌کنم\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "فقط عکس رو توی چت رها کن! 📸",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:secretary")
async def cb_secretary(callback: CallbackQuery):
    """Show secretary mode menu."""
    await callback.message.edit_text(
        "🤖 <b>حالت سکرتر هوشمند</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "من هم می‌تونم چت کنم و هم سکرتر شخصی‌ات باشم!\n\n"
        "📋 <b>دستورات:</b>\n"
        "• <code>/remind</code> — یادآوری\n"
        "• <code>/task</code> — تسک‌ها\n"
        "• <code>/note</code> — یادداشت\n"
        "• <code>/calendar</code> — تقویم\n"
        "• <code>/summary</code> — گزارش\n\n"
        "💬 <b>یا به زبان طبیعی بگو...</b>\n"
        "• \"یادآوری کن فردا ساعت ۹ جلسه دارم\"\n"
        "• \"تسک جدید: خرید شیر\"\n"
        "• \"یادداشت: تلفن علی ۰۹۱۲...\"\n"
        "• \"تقویم: جلسه با تیم هفته بعد ساعت ۱۰\"\n"
        "• \"خلاصه امروز رو بده\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "دیتا فقط برای تو (مالک) ذخیره میشه 🔒",
        parse_mode="HTML",
        reply_markup=get_secretary_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:tasks")
async def cb_tasks(callback: CallbackQuery, secretary: SecretaryManager):
    """Show tasks list from main menu."""
    tasks = await secretary.get_tasks(callback.message.chat.id)
    if not tasks:
        text = "📭 هیچ تسکی ثبت نشده.\nبا <code>/task add</code> یکی اضافه کن."
    else:
        lines = ["📋 <b>لیست تسک‌ها:</b>\n"]
        for t in tasks[:20]:
            p_icon = "🔴" if t.priority >= 3 else "🟡" if t.priority == 2 else "🟢"
            status_icon = "✅" if t.status == "done" else "⏳" if t.status == "in_progress" else "🔵"
            due = f" 📅 {t.due_date[:16]}" if t.due_date else ""
            lines.append(f"{status_icon} {p_icon} <code>{t.id[:8]}</code> {t.title}{due}")

        if len(tasks) > 20:
            lines.append(f"\n... و {len(tasks) - 20} تسک دیگر")
        text = "\n".join(lines)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_task_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:search")
async def cb_search(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 <b>جستجوی وب</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "اطلاعات تازه می‌خوای؟ از دستورات زیر استفاده کن:\n"
        "<code>/search جستجوی تو اینجا</code>\n\n"
        "یا مستقیم بپرس — خودم وقتی لازم باشه سرچ می‌کنم.\n\n"
        "🎯 <b>مناسب برای:</b>\n"
        "• اخبار، قیمت، آب‌وهوا\n"
        "• داکیومنت‌های جدید تکنولوژی\n"
        "• ورزش، کریپتو، بورس زنده\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "چی رو می‌خوای پیدا کنی؟ 🔎",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("help:"))
async def cb_help_detail(callback: CallbackQuery):
    topic = callback.data.split(":", 1)[1]
    texts = {
        "chat": (
            "💬 <b>نکات چت</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• دقیق بپرس — سوال بهتر = جواب بهتر\n"
            "• ادامه بده! من مکالمه رو یادم میره\n"
            "• کد، توضیح، نوشته خلاقه بخواه\n"
            "• از <code>/clear</code> برای عوض کردن موضوع استفاده کن\n"
            "• فارسی، انگلیسی، یا 섞ی کار می‌کنه\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "image": (
            "🖼️ <b>نکات عکس</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• هر عکسی بفرست — تحلیل می‌کنم\n"
            "• کپشن بذار برای سوال خاص\n"
            "• بنویس \"متن رو بخون\" یا \"read this\" برای OCR\n"
            "• اسکرین‌شات، داکیومنت، دست‌نویس هم جواب میده\n"
            "• متن عکس رو هم ترجمه می‌کنم\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "search": (
            "🔍 <b>نکات جستجو</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• از <code>/search جستجو</code> برای سرچ دستی استفاده کن\n"
            "• من خودم وقتی لازم باشه سرچ می‌کنم\n"
            "• بنویس \"بیشتر\" یا \"more results\" برای جستجوی عمیق\n"
            "• مناسب برای: اخبار، قیمت، داکیومنت‌های جدید\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "commands": (
            "⚙️ <b>تمام دستورات</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "/start — منوی اصلی\n"
            "/help — همین راهنما\n"
            "/clear — ریست حافظه چت\n"
            "/setmodel <نام> — تغییر مدل AI\n"
            "/search <جستجو> — جستجوی وب\n"
            "/owner — اطلاعات خالق\n"
            "/me — پروفایل شما\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
    }
    await callback.message.edit_text(
        texts.get(topic, "موضوع پیدا نشد"),
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
        await callback.answer("چیزی برای تولید مجدد نیست.", show_alert=True)
        return
    
    # Find last user message
    last_user_msg = None
    for msg in reversed(history):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break
    
    if not last_user_msg:
        await callback.answer("چیزی برای تولید مجدد نیست.", show_alert=True)
        return
    
    await callback.message.edit_text("🔄 <b>در حال تولید مجدد...</b>", parse_mode="HTML")
    
    messages = [{"role": "system", "content": system_prompt}]
    # Add history without the last assistant message
    for msg in history:
        if not (msg["role"] == "assistant" and msg == history[-1]):
            messages.append(msg)
    
    full_response = ""
    async for partial in ai_client.get_response(messages):
        full_response = partial
    
    if not full_response:
        full_response = "نتونستم جواب بدم."
    
    # Update history
    await history_manager.clear(callback.message.chat.id)
    for msg in history[:-1]:  # Exclude last assistant message
        await history_manager.add_message(callback.message.chat.id, msg["role"], msg["content"])
    await history_manager.add_message(callback.message.chat.id, "assistant", full_response)
    
    await callback.message.edit_text(full_response, parse_mode="Markdown", reply_markup=get_chat_followup_keyboard())
    await callback.answer("تولید مجدد شد!")


@router.callback_query(lambda c: c.data == "chat:search")
async def cb_chat_search(callback: CallbackQuery):
    """Trigger web search for the last topic."""
    await callback.message.edit_text(
        "🔍 <b>جستجوی وب</b>\n\n"
        "از <code>/search جستجوی تو</code> استفاده کن یا مستقیم بپرس!\n\n"
        "چی رو می‌خوای سرچ کنم؟ 🔎",
        parse_mode="HTML",
        reply_markup=get_chat_followup_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "chat:explain")
async def cb_chat_explain(callback: CallbackQuery, ai_client, history_manager, bot_username: str, system_prompt: str):
    """Ask AI to explain more about the last topic."""
    history = await history_manager.get_history(callback.message.chat.id)
    if not history:
        await callback.answer("موضوعی برای توضیح وجود نداره.", show_alert=True)
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
        await callback.answer("موضوعی برای توضیح وجود نداره.", show_alert=True)
        return
    
    await callback.message.edit_text("💡 <b>در حال توضیح بیشتر...</b>", parse_mode="HTML")
    
    messages = [
        {"role": "system", "content": system_prompt + "\n\nکاربر می‌خواد توضیح دقیق‌تری از جواب قبلی داشته باشه. با مثال، تشبیه، و جزئیات بیشتر توضیح بده."},
        {"role": "user", "content": last_user},
        {"role": "assistant", "content": last_assistant},
        {"role": "user", "content": "این رو با جزئیات بیشتر و مثال توضیح بده."}
    ]
    
    full_response = ""
    async for partial in ai_client.get_response(messages):
        full_response = partial
    
    if not full_response:
        full_response = "نتونستم توضیح دقیق بدم."
    
    await history_manager.add_message(callback.message.chat.id, "user", "توضیح بیشتر")
    await history_manager.add_message(callback.message.chat.id, "assistant", full_response)
    
    await callback.message.edit_text(full_response, parse_mode="Markdown", reply_markup=get_chat_followup_keyboard())
    await callback.answer("توضیح داده شد!")


@router.callback_query(lambda c: c.data == "chat:translate")
async def cb_chat_translate(callback: CallbackQuery, ai_client, history_manager, bot_username: str, system_prompt: str):
    """Translate the last response."""
    history = await history_manager.get_history(callback.message.chat.id)
    if not history:
        await callback.answer("چیزی برای ترجمه وجود نداره.", show_alert=True)
        return
    
    # Get last assistant message
    last_assistant = ""
    for msg in reversed(history):
        if msg["role"] == "assistant":
            last_assistant = msg["content"]
            break
    
    if not last_assistant:
        await callback.answer("چیزی برای ترجمه وجود نداره.", show_alert=True)
        return
    
    await callback.message.edit_text("🌐 <b>در حال ترجمه...</b>", parse_mode="HTML")
    
    messages = [
        {"role": "system", "content": system_prompt + "\n\nTranslate the following text to the user's language (detect from context). Keep formatting."},
        {"role": "user", "content": f"Translate this:\n\n{last_assistant}"}
    ]
    
    full_response = ""
    async for partial in ai_client.get_response(messages):
        full_response = partial
    
    if not full_response:
        full_response = "ترجمه شکست خورد."
    
    await history_manager.add_message(callback.message.chat.id, "user", "Translate last response")
    await history_manager.add_message(callback.message.chat.id, "assistant", full_response)
    
    await callback.message.edit_text(full_response, parse_mode="Markdown", reply_markup=get_chat_followup_keyboard())
    await callback.answer("ترجمه شد!")


@router.callback_query(lambda c: c.data == "chat:clear")
async def cb_chat_clear(callback: CallbackQuery, history_manager, bot_username: str):
    """Clear conversation history."""
    try:
        await history_manager.clear(callback.message.chat.id)
        await callback.message.edit_text(
            "🧹 <b>تموم شد!</b> حافظه چت کاملاً پاک شد. شروع تازه! 🌱",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error("Error in cb_chat_clear: %s", e, exc_info=True)
        await callback.answer("❌ خطا در پاک کردن حافظه", show_alert=True)
    else:
        await callback.answer("حافظه پاک شد!")


# Additional Secretary callbacks
@router.callback_query(lambda c: c.data == "sec:tasks")
async def cb_sec_tasks(callback: CallbackQuery, secretary: SecretaryManager):
    """Show tasks list from secretary menu."""
    tasks = await secretary.get_tasks(callback.message.chat.id)
    if not tasks:
        text = "📭 هیچ تسکی ثبت نشده.\nبا <code>/task add</code> یکی اضافه کن."
    else:
        lines = ["📋 <b>لیست تسک‌ها:</b>\n"]
        for t in tasks[:20]:
            p_icon = "🔴" if t.priority >= 3 else "🟡" if t.priority == 2 else "🟢"
            status_icon = "✅" if t.status == "done" else "⏳" if t.status == "in_progress" else "🔵"
            due = f" 📅 {t.due_date[:16]}" if t.due_date else ""
            lines.append(f"{status_icon} {p_icon} <code>{t.id[:8]}</code> {t.title}{due}")

        if len(tasks) > 20:
            lines.append(f"\n... و {len(tasks) - 20} تسک دیگر")
        text = "\n".join(lines)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_task_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:tasks_pending")
async def cb_sec_tasks_pending(callback: CallbackQuery, secretary: SecretaryManager):
    """Show pending tasks."""
    tasks = await secretary.get_tasks(callback.message.chat.id, status="pending")
    if not tasks:
        text = "📭 هیچ تسک در الانتظاری نیست."
    else:
        lines = ["⏳ <b>تسک‌های در انتظار:</b>\n"]
        for t in tasks[:20]:
            p_icon = "🔴" if t.priority >= 3 else "🟡" if t.priority == 2 else "🟢"
            due = f" 📅 {t.due_date[:16]}" if t.due_date else ""
            lines.append(f"{p_icon} <code>{t.id[:8]}</code> {t.title}{due}")
        text = "\n".join(lines)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_task_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:tasks_done")
async def cb_sec_tasks_done(callback: CallbackQuery, secretary: SecretaryManager):
    """Show completed tasks."""
    tasks = await secretary.get_tasks(callback.message.chat.id, status="done")
    if not tasks:
        text = "📭 هیچ تسک تکمیل شده‌ای نیست."
    else:
        lines = ["✅ <b>تسک‌های انجام شده:</b>\n"]
        for t in tasks[:20]:
            due = f" 📅 {t.due_date[:16]}" if t.due_date else ""
            lines.append(f"✅ <code>{t.id[:8]}</code> {t.title}{due}")
        text = "\n".join(lines)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_task_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:remind")
async def cb_sec_remind(callback: CallbackQuery):
    """Show reminder help."""
    text = (
        "⏰ <b>تنظیم یادآوری</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "از دستور زیر استفاده کن:\n"
        "<code>/remind [زمان] [متن]</code>\n\n"
        "<b>مثال‌ها:</b>\n"
        "• <code>/remind 14:30 جلسه تیم</code>\n"
        "• <code>/remind فردا ۰۹:۰۰ خرید شیر</code>\n"
        "• <code>/remind ۲۰۲۴-۱۲-۲۵ ۱۰:۰۰ کریسمس</code>\n\n"
        "یا به زبان طبیعی بنویس:\n"
        "• \"یادآوری کن فردا ساعت ۹ جلسه دارم\"\n"
        "• \"یادم بگو امروز ساعت ۵ عصر خرید کنم\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_remind_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:reminders")
async def cb_sec_reminders(callback: CallbackQuery, secretary: SecretaryManager):
    """Show active reminders."""
    reminders = await secretary.get_reminders(callback.message.chat.id, active_only=True)
    if not reminders:
        text = "📭 هیچ یادآوری فعالی نیست.\nبا <code>/remind</code> یکی بساز."
    else:
        lines = ["⏰ <b>یادآوری‌های فعال:</b>\n"]
        for r in reminders[:20]:
            lines.append(f"⏰ {r.remind_at[11:16]} — {r.title} (<code>{r.id[:8]}</code>)")
        text = "\n".join(lines)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_remind_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:note")
async def cb_sec_note(callback: CallbackQuery):
    """Show note help."""
    text = (
        "📝 <b>یادداشت سریع</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "از دستور زیر استفاده کن:\n"
        "<code>/note متن یادداشت</code>\n\n"
        "یا به زبان طبیعی بنویس:\n"
        "• \"یادداشت: تلفن علی ۰۹۱۲...\"\n"
        "• \"نوت: آدرس سایت مهم\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_note_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:notes")
async def cb_sec_notes(callback: CallbackQuery, secretary: SecretaryManager):
    """Show all notes."""
    notes = await secretary.get_notes(callback.message.chat.id)
    if not notes:
        text = "📭 هیچ یادداشتی نیست.\nبا <code>/note</code> یکی بساز."
    else:
        lines = ["📝 <b>یادداشت‌ها:</b>\n"]
        for n in notes[:15]:
            lines.append(f"📄 <code>{n.id[:8]}</code> {n.title}")
            if n.content != n.title:
                lines.append(f"   {n.content[:80]}{'...' if len(n.content) > 80 else ''}")
        text = "\n".join(lines)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_note_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:event")
async def cb_sec_event(callback: CallbackQuery):
    """Show event help."""
    text = (
        "📅 <b>افزودن رویداد تقویم</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "از دستور زیر استفاده کن:\n"
        "<code>/event [زمان] [عنوان]</code>\n\n"
        "<b>مثال‌ها:</b>\n"
        "• <code>/event 14:30 جلسه تیم</code>\n"
        "• <code>/event فردا ۱۰:۰۰ ملاقات دکتر</code>\n\n"
        "یا به زبان طبیعی:\n"
        "• \"تقویم: جلسه با تیم هفته بعد ساعت ۱۰\"\n"
        "• \"رویداد جدید: خرید عید فردا صبح\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_calendar_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:calendar")
async def cb_sec_calendar(callback: CallbackQuery, secretary: SecretaryManager):
    """Show today's calendar."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    events = await secretary.get_events(
        callback.message.chat.id,
        start_from=f"{today}T00:00:00",
        end_before=f"{today}T23:59:59"
    )

    if not events:
        text = f"📅 <b>تقویم امروز ({today})</b>\n\n📭 هیچ رویدادی ثبت نشده."
    else:
        lines = [f"📅 <b>تقویم امروز ({today}):</b>\n"]
        for e in events:
            loc = f" 📍 {e.location}" if e.location else ""
            lines.append(f"🕐 {e.start_time[11:16]} — {e.title}{loc}")
        text = "\n".join(lines)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_calendar_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:calendar_week")
async def cb_sec_calendar_week(callback: CallbackQuery, secretary: SecretaryManager):
    """Show this week's calendar."""
    now = datetime.now()
    start = now.strftime("%Y-%m-%d")
    end = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    events = await secretary.get_events(
        callback.message.chat.id,
        start_from=f"{start}T00:00:00",
        end_before=f"{end}T23:59:59"
    )

    if not events:
        text = f"📅 <b>تقویم این هفته ({start} تا {end})</b>\n\n📭 هیچ رویدادی ثبت نشده."
    else:
        lines = [f"📅 <b>تقویم این هفته ({start} تا {end}):</b>\n"]
        for e in events:
            loc = f" 📍 {e.location}" if e.location else ""
            lines.append(f"🕐 {e.start_time[:10]} {e.start_time[11:16]} — {e.title}{loc}")
        text = "\n".join(lines)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_calendar_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:summary")
async def cb_sec_summary(callback: CallbackQuery, secretary: SecretaryManager):
    """Show daily summary."""
    summary = await secretary.get_daily_summary(callback.message.chat.id)
    await callback.message.edit_text(summary, parse_mode="HTML", reply_markup=get_secretary_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:weekly")
async def cb_sec_weekly(callback: CallbackQuery, secretary: SecretaryManager):
    """Show weekly summary."""
    summary = await secretary.get_weekly_summary(callback.message.chat.id)
    await callback.message.edit_text(summary, parse_mode="HTML", reply_markup=get_secretary_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "sec:task")
async def cb_sec_task(callback: CallbackQuery):
    """Show task help."""
    text = (
        "📋 <b>مدیریت تسک‌ها</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "دستورات:\n"
        "• <code>/task add عنوان تسک</code> — تسک جدید\n"
        "• <code>/tasks</code> — لیست همه\n"
        "• <code>/task done آیدی</code> — تکمیل\n"
        "• <code>/task del آیدی</code> — حذف\n\n"
        "یا به زبان طبیعی:\n"
        "• \"تسک جدید: خرید شیر\"\n"
        "• \"کار جدید: تماس با علی فوری\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_secretary_task_keyboard())
    await callback.answer()