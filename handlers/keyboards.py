from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu inline keyboard for /start."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Start Chat", callback_data="menu:chat"),
            InlineKeyboardButton(text="🔍 Web Search", callback_data="menu:search"),
        ],
        [
            InlineKeyboardButton(text="🖼️ Analyze Image", callback_data="menu:image"),
            InlineKeyboardButton(text="⚙️ Settings", callback_data="menu:settings"),
        ],
        [
            InlineKeyboardButton(text="👑 Owner Info", callback_data="menu:owner"),
            InlineKeyboardButton(text="👤 My Profile", callback_data="menu:profile"),
        ],
        [
            InlineKeyboardButton(text="❓ Help & Tips", callback_data="menu:help"),
        ]
    ])


def get_chat_followup_keyboard() -> InlineKeyboardMarkup:
    """Follow-up actions after AI response."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Regenerate", callback_data="chat:regenerate"),
            InlineKeyboardButton(text="🔍 Search Web", callback_data="chat:search"),
        ],
        [
            InlineKeyboardButton(text="💡 Explain More", callback_data="chat:explain"),
            InlineKeyboardButton(text="🌐 Translate", callback_data="chat:translate"),
        ],
        [
            InlineKeyboardButton(text="🗑️ Clear History", callback_data="chat:clear"),
        ]
    ])


def get_image_followup_keyboard() -> InlineKeyboardMarkup:
    """Follow-up actions after image analysis."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Extract Text (OCR)", callback_data="image:ocr"),
            InlineKeyboardButton(text="🔍 Analyze Deeper", callback_data="image:deeper"),
        ],
        [
            InlineKeyboardButton(text="🌐 Translate Text", callback_data="image:translate"),
            InlineKeyboardButton(text="💾 Save Result", callback_data="image:save"),
        ],
        [
            InlineKeyboardButton(text="🗑️ Clear History", callback_data="chat:clear"),
        ]
    ])


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Settings menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 Change Model", callback_data="settings:model"),
            InlineKeyboardButton(text="🎨 Toggle Markdown", callback_data="settings:markdown"),
        ],
        [
            InlineKeyboardButton(text="📝 History Length", callback_data="settings:history"),
            InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu:main"),
        ]
    ])


def get_model_selection_keyboard(current_model: str = "") -> InlineKeyboardMarkup:
    """Model selection keyboard."""
    models = [
        ("gpt-4o", "GPT-4o"),
        ("gpt-4o-mini", "GPT-4o Mini"),
        ("gpt-4-turbo", "GPT-4 Turbo"),
        ("gpt-3.5-turbo", "GPT-3.5 Turbo"),
        ("claude-3-5-sonnet", "Claude 3.5 Sonnet"),
        ("claude-3-haiku", "Claude 3 Haiku"),
        ("gemini-1.5-pro", "Gemini 1.5 Pro"),
        ("gemini-1.5-flash", "Gemini 1.5 Flash"),
    ]
    
    buttons = []
    row = []
    for model_id, model_name in models:
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
    
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="settings:model")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Help menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Chat Tips", callback_data="help:chat"),
            InlineKeyboardButton(text="🖼️ Image Tips", callback_data="help:image"),
        ],
        [
            InlineKeyboardButton(text="🔍 Search Tips", callback_data="help:search"),
            InlineKeyboardButton(text="⚙️ Commands", callback_data="help:commands"),
        ],
        [
            InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu:main"),
        ]
    ])