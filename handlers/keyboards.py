from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


# Model definitions - centralized for consistency
# Using NVIDIA NIM model IDs
AVAILABLE_MODELS = [
    ("z-ai/glm-5.2", "🧠 GLM-5.2"),
    ("minimax-m3", "⚡ MiniMax M3"),
    ("nvidia/nemotron-3-ultra-550b-a55b", "🚀 Nemotron 3 Ultra"),
    ("deepseek-ai/deepseek-v4-flash", "🔍 DeepSeek V4 Flash"),
    ("meta/llama-3.1-405b-instruct", "🦙 Llama 3.1 405B"),
    ("meta/llama-3.1-70b-instruct", "🦙 Llama 3.1 70B"),
    ("google/gemma-2-27b-it", "💎 Gemma 2 27B"),
    ("microsoft/phi-3.5-mini-instruct", "⚡ Phi-3.5 Mini"),
    ("qwen/qwen-2.5-72b-instruct", "🐉 Qwen 2.5 72B"),
]


def get_model_display_name(model_id: str) -> str:
    """Get display name for a model ID."""
    for mid, name in AVAILABLE_MODELS:
        if mid == model_id:
            return name
    return model_id


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu inline keyboard for /start - Premium & Organized."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬  شروع چت جدید", callback_data="menu:chat"),
            InlineKeyboardButton(text="🖼️  تحلیل عکس", callback_data="menu:image"),
        ],
        [
            InlineKeyboardButton(text="🤖  تغییر مدل AI", callback_data="menu:model"),
            InlineKeyboardButton(text="🗑️  پاک کردن حافظه", callback_data="chat:clear"),
        ],
        [
            InlineKeyboardButton(text="🤖  سکرتر هوشمند", callback_data="menu:secretary"),
            InlineKeyboardButton(text="📋  تسک‌ها و یادآوری", callback_data="menu:tasks"),
        ],
        [
            InlineKeyboardButton(text="👑  اطلاعات صاحب (Jadix)", callback_data="menu:owner"),
            InlineKeyboardButton(text="❓  راهنما / Help", callback_data="menu:help"),
        ],
    ])


def get_compact_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Compact main menu for callback returns - 2x3 grid."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 چت جدید", callback_data="menu:chat"),
            InlineKeyboardButton(text="🤖 مدل AI", callback_data="menu:model"),
            InlineKeyboardButton(text="🗑️ پاک کردن", callback_data="chat:clear"),
        ],
        [
            InlineKeyboardButton(text="🖼️ عکس", callback_data="menu:image"),
            InlineKeyboardButton(text="👑 صاحب", callback_data="menu:owner"),
            InlineKeyboardButton(text="❓ راهنما", callback_data="menu:help"),
        ],
    ])


def get_chat_followup_keyboard() -> InlineKeyboardMarkup:
    """Follow-up actions after AI response - Clean 2x2 + 1 layout."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄  تولید مجدد", callback_data="chat:regenerate"),
            InlineKeyboardButton(text="💡  توضیح بیشتر", callback_data="chat:explain"),
        ],
        [
            InlineKeyboardButton(text="🌐  ترجمه", callback_data="chat:translate"),
            InlineKeyboardButton(text="🔍  جستجوی وب", callback_data="chat:search"),
        ],
        [
            InlineKeyboardButton(text="🗑️  پاک کردن حافظه", callback_data="chat:clear"),
        ],
        [
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_image_followup_keyboard() -> InlineKeyboardMarkup:
    """Follow-up actions after image analysis - Clean layout."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝  استخراج متن (OCR)", callback_data="image:ocr"),
            InlineKeyboardButton(text="🔍  تحلیل عمیق‌تر", callback_data="image:deeper"),
        ],
        [
            InlineKeyboardButton(text="🌐  ترجمه متن", callback_data="image:translate"),
            InlineKeyboardButton(text="💾  ذخیره نتیجه", callback_data="image:save"),
        ],
        [
            InlineKeyboardButton(text="🗑️  پاک کردن حافظه", callback_data="chat:clear"),
        ],
        [
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Settings menu keyboard - Clean 2x2 layout."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖  تغییر مدل AI", callback_data="settings:model"),
            InlineKeyboardButton(text="🎨  فرمت‌دهی مارک‌داون", callback_data="settings:markdown"),
        ],
        [
            InlineKeyboardButton(text="📝  طول حافظه", callback_data="settings:history"),
            InlineKeyboardButton(text="🗑️  پاک کردن حافظه", callback_data="chat:clear"),
        ],
        [
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_model_selection_keyboard(current_model: str = "") -> InlineKeyboardMarkup:
    """Model selection keyboard - 2 per row with checkmark for current."""
    buttons = []
    row = []
    for model_id, model_name in AVAILABLE_MODELS:
        marker = " ✅" if model_id == current_model else ""
        row.append(InlineKeyboardButton(
            text=f"{model_name}{marker}",
            callback_data=f"model:{model_id}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_model_keyboard(current_model: str = "") -> InlineKeyboardMarkup:
    """Compact model keyboard for /model command - 2 per row."""
    buttons = []
    row = []
    for model_id, model_name in AVAILABLE_MODELS:
        marker = " ✅" if model_id == current_model else ""
        row.append(InlineKeyboardButton(
            text=f"{model_name}{marker}",
            callback_data=f"model:{model_id}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Help menu keyboard - Clean 2x2 + 1 layout."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬  نکات چت", callback_data="help:chat"),
            InlineKeyboardButton(text="🖼️  نکات عکس", callback_data="help:image"),
        ],
        [
            InlineKeyboardButton(text="🔍  نکات جستجو", callback_data="help:search"),
            InlineKeyboardButton(text="⚙️  دستورات", callback_data="help:commands"),
        ],
        [
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_owner_keyboard() -> InlineKeyboardMarkup:
    """Owner info keyboard with back to main."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main")],
    ])


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Profile keyboard with back to main."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main")],
    ])


def get_model_changed_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown after model change."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
            InlineKeyboardButton(text="🤖  انتخاب مدل دیگر", callback_data="settings:model"),
        ],
    ])


def get_clear_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard for clearing history."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅  بله، پاک کن", callback_data="chat:clear_confirm"),
            InlineKeyboardButton(text="❌  انصراف", callback_data="menu:main"),
        ],
    ])


def get_search_keyboard() -> InlineKeyboardMarkup:
    """Search follow-up keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍  جستجوی عمیق‌تر", callback_data="search:deeper"),
            InlineKeyboardButton(text="🌐  ترجمه نتایج", callback_data="search:translate"),
        ],
        [
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_image_help_keyboard() -> InlineKeyboardMarkup:
    """Image analysis help keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸  امتحان کن", callback_data="menu:image"),
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_secretary_keyboard() -> InlineKeyboardMarkup:
    """Secretary mode main keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰  یادآوری جدید", callback_data="sec:remind"),
            InlineKeyboardButton(text="📋  تسک جدید", callback_data="sec:task"),
        ],
        [
            InlineKeyboardButton(text="📝  یادداشت", callback_data="sec:note"),
            InlineKeyboardButton(text="📅  رویداد تقویم", callback_data="sec:event"),
        ],
        [
            InlineKeyboardButton(text="📋  لیست تسک‌ها", callback_data="sec:tasks"),
            InlineKeyboardButton(text="📅  تقویم امروز", callback_data="sec:calendar"),
        ],
        [
            InlineKeyboardButton(text="📊  خلاصه روز", callback_data="sec:summary"),
            InlineKeyboardButton(text="📈  خلاصه هفته", callback_data="sec:weekly"),
        ],
        [
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_secretary_task_keyboard() -> InlineKeyboardMarkup:
    """Task management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕  تسک جدید", callback_data="sec:task"),
            InlineKeyboardButton(text="📋  همه تسک‌ها", callback_data="sec:tasks"),
        ],
        [
            InlineKeyboardButton(text="⏳  در انتظار", callback_data="sec:tasks_pending"),
            InlineKeyboardButton(text="✅  انجام شده", callback_data="sec:tasks_done"),
        ],
        [
            InlineKeyboardButton(text="🔙  سکرتر", callback_data="menu:secretary"),
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_secretary_remind_keyboard() -> InlineKeyboardMarkup:
    """Reminder management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰  یادآوری جدید", callback_data="sec:remind"),
            InlineKeyboardButton(text="📋  یادآوری‌های فعال", callback_data="sec:reminders"),
        ],
        [
            InlineKeyboardButton(text="🔙  سکرتر", callback_data="menu:secretary"),
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_secretary_note_keyboard() -> InlineKeyboardMarkup:
    """Note management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝  یادداشت جدید", callback_data="sec:note"),
            InlineKeyboardButton(text="📋  همه یادداشت‌ها", callback_data="sec:notes"),
        ],
        [
            InlineKeyboardButton(text="🔙  سکرتر", callback_data="menu:secretary"),
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])


def get_secretary_calendar_keyboard() -> InlineKeyboardMarkup:
    """Calendar management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅  رویداد جدید", callback_data="sec:event"),
            InlineKeyboardButton(text="📅  امروز", callback_data="sec:calendar"),
        ],
        [
            InlineKeyboardButton(text="📆  این هفته", callback_data="sec:calendar_week"),
            InlineKeyboardButton(text="📋  همه رویدادها", callback_data="sec:events"),
        ],
        [
            InlineKeyboardButton(text="🔙  سکرتر", callback_data="menu:secretary"),
            InlineKeyboardButton(text="🏠  منوی اصلی", callback_data="menu:main"),
        ],
    ])