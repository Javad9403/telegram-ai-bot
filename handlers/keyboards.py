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
    """Main menu inline keyboard for /start."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 چت جدید", callback_data="menu:chat"),
            InlineKeyboardButton(text="🔍 جستجوی وب", callback_data="menu:search"),
        ],
        [
            InlineKeyboardButton(text="🖼️ تحلیل عکس", callback_data="menu:image"),
            InlineKeyboardButton(text="🤖 تغییر مدل", callback_data="menu:model"),
        ],
        [
            InlineKeyboardButton(text="👑 اطلاعات سازنده", callback_data="menu:owner"),
            InlineKeyboardButton(text="👤 پروفایل من", callback_data="menu:profile"),
        ],
        [
            InlineKeyboardButton(text="❓ راهنما", callback_data="menu:help"),
        ]
    ])


def get_chat_followup_keyboard() -> InlineKeyboardMarkup:
    """Follow-up actions after AI response."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 تولید مجدد", callback_data="chat:regenerate"),
            InlineKeyboardButton(text="🔍 جستجوی وب", callback_data="chat:search"),
        ],
        [
            InlineKeyboardButton(text="💡 توضیح بیشتر", callback_data="chat:explain"),
            InlineKeyboardButton(text="🌐 ترجمه", callback_data="chat:translate"),
        ],
        [
            InlineKeyboardButton(text="🗑️ پاک کردن حافظه", callback_data="chat:clear"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu:main"),
        ]
    ])


def get_image_followup_keyboard() -> InlineKeyboardMarkup:
    """Follow-up actions after image analysis."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 استخراج متن (OCR)", callback_data="image:ocr"),
            InlineKeyboardButton(text="🔍 تحلیل عمیق‌تر", callback_data="image:deeper"),
        ],
        [
            InlineKeyboardButton(text="🌐 ترجمه متن", callback_data="image:translate"),
            InlineKeyboardButton(text="💾 ذخیره نتیجه", callback_data="image:save"),
        ],
        [
            InlineKeyboardButton(text="🗑️ پاک کردن حافظه", callback_data="chat:clear"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu:main"),
        ]
    ])


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Settings menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 تغییر مدل", callback_data="settings:model"),
            InlineKeyboardButton(text="🎨 فرمت‌دهی", callback_data="settings:markdown"),
        ],
        [
            InlineKeyboardButton(text="📝 طول حافظه", callback_data="settings:history"),
            InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main"),
        ]
    ])


def get_model_selection_keyboard(current_model: str = "") -> InlineKeyboardMarkup:
    """Model selection keyboard."""
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
    
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_model_keyboard(current_model: str = "") -> InlineKeyboardMarkup:
    """Compact model keyboard for /model command."""
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
    
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Help menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 نکات چت", callback_data="help:chat"),
            InlineKeyboardButton(text="🖼️ نکات عکس", callback_data="help:image"),
        ],
        [
            InlineKeyboardButton(text="🔍 نکات جستجو", callback_data="help:search"),
            InlineKeyboardButton(text="⚙️ دستورات", callback_data="help:commands"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="menu:main"),
        ]
    ])