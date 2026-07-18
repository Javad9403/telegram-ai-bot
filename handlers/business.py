import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, 
    BusinessConnection, 
    BusinessMessagesDeleted,
)
from aiogram.utils.chat_action import ChatActionSender

from utils.filters import ChatTypeFilter, OwnerFilter
from utils.secretary import SecretaryManager
from handlers.keyboards import get_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


# ========== BUSINESS CONNECTION HANDLERS ==========

@router.business_connection()
async def handle_business_connection(business_connection: BusinessConnection):
    """Handle when a user connects/disconnects the bot as chat automation."""
    user_id = business_connection.user.id
    is_connected = business_connection.is_enabled
    
    logger.info(
        "Business connection %s for user %s (connection_id: %s)",
        "enabled" if is_connected else "disabled",
        user_id,
        business_connection.id
    )
    
    if is_connected:
        logger.info(
            "User %s connected bot as chat automation. "
            "Rights: can_reply=%s, can_transfer=%s",
            user_id,
            business_connection.rights.can_reply if business_connection.rights else "N/A",
            business_connection.rights.can_transfer if business_connection.rights else "N/A"
        )
        
        # Send confirmation message to the user
        try:
            bot = business_connection.bot
            if not bot:
                # Try to get bot from dispatcher context
                from aiogram import Bot
                bot = Bot.get_current()
            if bot:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        "✅ <b>اتوماسیون چت فعال شد!</b>\n\n"
                        "جاوید الان به عنوان دستیار اتوماتیک شما در تلگرام فعال است.\n\n"
                        "🤖 <b>قابلیت‌ها:</b>\n"
                        "• پاسخ خودکار به پیام‌های دریافتی\n"
                        "• مدیریت تسک‌ها، یادآوری‌ها، یادداشت‌ها\n"
                        "• تقویم و گزارش‌های روزانه/هفتگی\n\n"
                        "📋 <b>دستورات سکرتر:</b>\n"
                        "• <code>/remind [زمان] [متن]</code> - تنظیم یادآوری\n"
                        "• <code>/task add [متن]</code> - افزودن تسک\n"
                        "• <code>/tasks</code> - مشاهده تسک‌ها\n"
                        "• <code>/note [متن]</code> - یادداشت سریع\n"
                        "• <code>/calendar</code> - تقویم\n"
                        "• <code>/summary</code> - گزارش روزانه/هفتگی\n\n"
                        "💡 <b>یا به زبان طبیعی بنویسید:</b>\n"
                        "• \"یادآوری کن فردا ساعت ۹ جلسه دارم\"\n"
                        "• \"تسک جدید: خرید شیر\"\n"
                        "• \"یادداشت: تلفن علی ۰۹۱۲...\"\n"
                        "• \"خلاصه امروز رو بده\"\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "دیتا فقط برای شما ذخیره می‌شود 🔒"
                    ),
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.warning("Could not send business connection confirmation: %s", e)
    else:
        logger.info("User %s disconnected bot from chat automation", user_id)


# ========== CATCH-ALL BUSINESS MESSAGE HANDLER (DEBUG) ==========

@router.business_message()
async def handle_any_business_message(message: Message):
    """Catch-all handler to log all business messages."""
    logger.info(
        "Business message received: chat_id=%s, user_id=%s, text=%s, connection_id=%s",
        message.chat.id,
        message.from_user.id if message.from_user else "N/A",
        (message.text or message.caption or "")[:50],
        message.business_connection_id
    )
    # Don't return - let other handlers process


# ========== BUSINESS MESSAGE HANDLERS ==========

async def _process_business_message(
    message: Message,
    ai_client,
    history_manager,
    secretary: SecretaryManager,
    system_prompt: str,
    owner_id: int,
    owner_name: str,
    owner_roles: list[str],
):
    """Process a business message (automated chat)."""
    business_connection_id = message.business_connection_id
    
    if not business_connection_id:
        logger.warning("No business_connection_id in message, skipping")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0
    
    logger.info(
        "Processing business message: chat=%s, from_user=%s, is_owner=%s",
        chat_id, user_id, user_id == owner_id
    )
    
    # Check if user is the owner (for secretary features)
    is_owner = user_id == owner_id
    
    if is_owner:
        owner_context = f"\n\n[Note: The user is the bot owner '{owner_name}' ({', '.join(owner_roles)}). Acknowledge this role appropriately.]"
        system_prompt = system_prompt + owner_context
    
    text = message.text or message.caption or ""
    
    if not text:
        logger.info("Empty business message, skipping")
        return
    
    # First check for secretary commands (natural language)
    from handlers.secretary import _process_secretary_message
    processed = await _process_secretary_message(message, secretary, text, chat_id)
    if processed:
        logger.info("Secretary command processed")
        return
    
    # If not a secretary command, process as normal AI chat
    async with ChatActionSender.typing(bot=message.bot, chat_id=chat_id, business_connection_id=business_connection_id):
        try:
            await history_manager.add_message(chat_id, "user", text)
            
            messages = [{"role": "system", "content": system_prompt}]
            history = await history_manager.get_history(chat_id)
            messages.extend(history)
            
            full_response = ""
            async for partial in ai_client.get_response(messages):
                full_response = partial
            
            if not full_response:
                full_response = "متأسفم، نتونستم جواب بدم. دوباره امتحان کن."
            
            await history_manager.add_message(chat_id, "assistant", full_response)
            
            # Send reply as business account using business_connection_id
            logger.info("Sending business reply to chat %s with connection_id %s", chat_id, business_connection_id)
            await message.bot.send_message(
                chat_id=chat_id,
                text=full_response,
                parse_mode="Markdown",
                business_connection_id=business_connection_id
            )
            logger.info("Business reply sent successfully")
            
        except Exception as e:
            logger.error("Error processing business message in chat %s: %s", chat_id, e, exc_info=True)
            try:
                await message.bot.send_message(
                    chat_id=chat_id,
                    text="متأسفم، خطایی پیش اومد. بعدا امتحان کن.",
                    business_connection_id=business_connection_id
                )
            except Exception as e2:
                logger.error("Failed to send error message: %s", e2)


@router.business_message(
    ChatTypeFilter([ChatType.PRIVATE]),
    F.text,
)
async def handle_private_business_message(
    message: Message,
    ai_client,
    history_manager,
    secretary: SecretaryManager,
    system_prompt: str,
    owner_id: int,
    owner_name: str,
    owner_roles: list[str],
):
    """Handle private business messages (automation mode)."""
    await _process_business_message(
        message, ai_client, history_manager, secretary,
        system_prompt, owner_id, owner_name, owner_roles
    )


@router.business_message(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),
    F.text,
)
async def handle_group_business_message(
    message: Message,
    ai_client,
    history_manager,
    secretary: SecretaryManager,
    system_prompt: str,
    owner_id: int,
    owner_name: str,
    owner_roles: list[str],
    bot_username: str,
    bot_id: int,
    bot_name: str,
):
    """Handle group business messages (automation mode)."""
    # In groups, only respond if mentioned or replied to
    from utils.filters import MentionFilter, ReplyToBotFilter, BotNameFilter, PersianNameFilter
    
    mention_filter = MentionFilter(bot_username)
    reply_filter = ReplyToBotFilter(bot_id)
    name_filter = BotNameFilter(bot_name)
    persian_name_filter = PersianNameFilter()
    
    is_mention = await mention_filter(message)
    is_reply = await reply_filter(message)
    is_name = await name_filter(message)
    is_persian_name = await persian_name_filter(message)
    
    if not is_mention and not is_reply and not is_name and not is_persian_name:
        return
    
    # Clean up message
    from handlers.chat import _clean_mention
    from utils.filters import clean_persian_name
    
    text = message.text
    if is_mention or is_name:
        text = _clean_mention(text, bot_username)
        if not text:
            text = "سلام"
    if is_persian_name:
        text = clean_persian_name(text)
        if not text:
            text = "سلام"
    
    message.text = text
    await _process_business_message(
        message, ai_client, history_manager, secretary,
        system_prompt, owner_id, owner_name, owner_roles
    )


@router.business_message(F.photo)
async def handle_business_photo(message: Message, ai_client, history_manager, system_prompt: str, owner_id: int):
    """Handle photo messages in business mode."""
    # Similar to image handler but with business_connection_id
    from handlers.image import _process_image_message
    await _process_image_message(
        message, ai_client, history_manager, 
        message.bot.get("bot_username", ""), 
        system_prompt,
        caption=message.caption,
        is_business=True
    )


@router.edited_business_message()
async def handle_edited_business_message(message: Message):
    """Handle edited business messages."""
    logger.info("Edited business message in chat %s", message.chat.id)
    # Re-process the edited message
    # For now, just log - could re-process if needed


@router.deleted_business_messages()
async def handle_deleted_business_messages(event: BusinessMessagesDeleted):
    """Handle deleted business messages."""
    logger.info(
        "Deleted business messages in chat %s: %s",
        event.chat_id,
        event.message_ids
    )


# ========== COMMAND HANDLERS FOR BUSINESS MODE ==========

@router.business_message(CommandStart())
async def cmd_business_start(message: Message):
    """Handle /start in business/automation mode."""
    user_id = message.from_user.id if message.from_user else 0
    is_owner = user_id == (message.bot.get("owner_id", 0))
    
    if is_owner:
        text = (
            "🤖 <b>جاوید - حالت اتوماسیون چت فعال شد</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "من الان به عنوان دستیار اتوماتیک تو در تلگرام فعال هستم.\n"
            "میتونم:\n"
            "• به پیام‌های ورودی پاسخ بدم\n"
            "• تسک، یادآوری، یادداشت مدیریت کنم\n"
            "• تقویم و خلاصه روزانه/هفتگی بدم\n\n"
            "دستورات:\n"
            "• <code>/remind</code> - یادآوری\n"
            "• <code>/task</code> - تسک‌ها\n"
            "• <code>/note</code> - یادداشت\n"
            "• <code>/calendar</code> - تقویم\n"
            "• <code>/summary</code> - گزارش\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        text = (
            "👋 <b>سلام! من جاوید هستم، دستیار هوشمند این اکانت.</b>\n\n"
            "میتونم به سوالاتتون جواب بدم، کمکتون کنم، و در خدمتم.\n\n"
            "چطور میتونم کمکتون کنم؟ 😊"
        )
    
    await message.answer(text, parse_mode="HTML", business_connection_id=message.business_connection_id)


@router.business_message(Command("help"))
async def cmd_business_help(message: Message):
    """Handle /help in business mode."""
    text = (
        "📖 <b>راهنمای جاوید (حالت اتوماسیون)</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 <b>چت:</b> مستقیم پیام بفرست، جواب میدم\n"
        "🤖 <b>سکرتر:</b> دستورات زیر:\n"
        "  • <code>/remind [زمان] [متن]</code> - یادآوری\n"
        "  • <code>/task add [متن]</code> - تسک جدید\n"
        "  • <code>/tasks</code> - لیست تسک‌ها\n"
        "  • <code>/note [متن]</code> - یادداشت\n"
        "  • <code>/calendar [today|week]</code> - تقویم\n"
        "  • <code>/summary [today|week]</code> - گزارش\n\n"
        "💡 <b>یا به زبان طبیعی بنویس:</b>\n"
        "  • \"یادآوری کن فردا ساعت ۹ جلسه دارم\"\n"
        "  • \"تسک جدید: خرید شیر\"\n"
        "  • \"یادداشت: تلفن علی ۰۹۱۲...\"\n"
        "  • \"تقویم: جلسه تیم هفته بعد ساعت ۱۰\"\n"
        "  • \"خلاصه امروز رو بده\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, parse_mode="HTML", business_connection_id=message.business_connection_id)


@router.business_message(Command("secretary"))
async def cmd_business_secretary(message: Message):
    """Show secretary mode help in business mode."""
    text = (
        "🤖 <b>حالت سکرتر جاوید</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "من هم می‌تونم چت کنم و هم سکرتر شخصی‌ات باشم!\n\n"
        "📋 <b>دستورات:</b>\n"
        "• <code>/remind</code> [زمان] [متن] — یادآوری\n"
        "• <code>/task add</code> [متن] — تسک جدید\n"
        "• <code>/tasks</code> — لیست تسک‌ها\n"
        "• <code>/note</code> [متن] — یادداشت\n"
        "• <code>/notes</code> — همه یادداشت‌ها\n"
        "• <code>/event</code> [زمان] [عنوان] — رویداد تقویم\n"
        "• <code>/calendar</code> [today|week] — نمایش تقویم\n"
        "• <code>/summary</code> [today|week] — گزارش روزانه/هفتگی\n\n"
        "💬 <b>یا به زبان طبیعی بگو...</b>\n"
        "• \"یادآوری کن فردا ساعت ۹ جلسه دارم\"\n"
        "• \"تسک جدید: خرید شیر\"\n"
        "• \"یادداشت: تلفن علی ۰۹۱۲...\"\n"
        "• \"تقویم: جلسه با تیم هفته بعد ساعت ۱۰\"\n"
        "• \"خلاصه امروز رو بده\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "دیتا فقط برای تو (مالک) ذخیره میشه 🔒"
    )
    await message.answer(text, parse_mode="HTML", business_connection_id=message.business_connection_id)