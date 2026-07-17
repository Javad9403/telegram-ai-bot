import logging
import base64
import re

from aiogram import Router, F
from aiogram.enums import ChatType, ChatAction
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from aiogram.filters import Filter

from utils.filters import ChatTypeFilter, MentionFilter, ReplyToBotFilter, BotNameFilter, PersianNameFilter, clean_persian_name
from handlers.keyboards import get_image_followup_keyboard, get_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


OCR_TRIGGERS = [
    "بخون", "متن", "نوشته", "خونده", "خواند", "استخراج", "متن عکس",
    "ocr", "extract text", "read text", "read image", "transcribe",
    "چی مینویسه", "چه نوشته", " متن ", "  متن"
]

VISION_PROMPT = (
    "You are a helpful AI assistant with vision capabilities. "
    "Analyze the image and answer the user's question or provide a detailed description. "
    "Respond in the user's language (Persian if they write in Persian, otherwise English). "
    "Be concise but thorough in your analysis."
)

OCR_PROMPT = (
    "You are an expert OCR engine with vision capabilities. "
    "Extract ALL text from this image with high accuracy. "
    "The image may contain: Persian/Arabic text, English text, mixed languages, "
    "screenshots, documents, receipts, handwritten notes, signs, or UI text. "
    "\n\n"
    "Guidelines:\n"
    "- Preserve the original language (Persian ↔ Persian, English ↔ English)\n"
    "- Maintain formatting: paragraphs, line breaks, lists, tables\n"
    "- For Persian: use proper Persian script, not transliteration\n"
    "- For handwritten: do your best, mark unclear parts with [?]\n"
    "- For tables/structured data: preserve structure\n"
    "- Do NOT add commentary, analysis, or descriptions\n"
    "- Output ONLY the extracted text\n"
    "- If no text found, say: \"No text detected in this image.\""
)

VISION_PROMPT_WITH_CAPTION = (
    "You are a helpful AI assistant with vision capabilities. "
    "The user sent an image with the following caption/question: '{caption}'. "
    "Analyze the image and answer their question or provide a detailed description. "
    "Respond in the user's language (Persian if they write in Persian, otherwise English). "
    "Be concise but thorough in your analysis."
)

OCR_PROMPT_WITH_CAPTION = (
    "You are an expert OCR engine with vision capabilities. "
    "The user wants you to extract text from this image. Their request: '{caption}'. "
    "Extract ALL text from this image with high accuracy. "
    "The image may contain: Persian/Arabic text, English text, mixed languages, "
    "screenshots, documents, receipts, handwritten notes, signs, or UI text. "
    "\n\n"
    "Guidelines:\n"
    "- Preserve the original language (Persian ↔ Persian, English ↔ English)\n"
    "- Maintain formatting: paragraphs, line breaks, lists, tables\n"
    "- For Persian: use proper Persian script, not transliteration\n"
    "- For handwritten: do your best, mark unclear parts with [?]\n"
    "- For tables/structured data: preserve structure\n"
    "- Do NOT add commentary, analysis, or descriptions\n"
    "- Output ONLY the extracted text\n"
    "- If no text found, say: \"No text detected in this image.\""
)


def _is_ocr_request(text: str | None) -> bool:
    """Check if the user is requesting OCR/text extraction."""
    if not text:
        return False
    text_lower = text.lower().strip()
    for trigger in OCR_TRIGGERS:
        if trigger in text_lower:
            return True
    return False


async def _get_image_bytes(message: Message, bot) -> bytes | None:
    """Extract image bytes from a message."""
    if message.photo:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        return file_bytes.read()
    return None


async def _get_image_bytes_from_file_id(file_id: str, bot) -> bytes | None:
    """Extract image bytes from a file_id."""
    try:
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        return file_bytes.read()
    except Exception as e:
        logger.error("Failed to download file: %s", e)
        return None


def _encode_image(image_bytes: bytes) -> str:
    """Encode image bytes to base64."""
    return base64.b64encode(image_bytes).decode("utf-8")


async def _process_image_message(
    message: Message,
    ai_client,
    history_manager,
    bot_username: str,
    system_prompt: str,
    caption: str | None = None,
    is_reply: bool = False,
):
    """Process an image message with optional caption."""
    bot = message.bot
    
    is_ocr = _is_ocr_request(caption)
    processing_msg = "📖 در حال خواندن عکس..." if is_ocr else "🔍 در حال بررسی عکس..."
    
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        try:
            image_bytes = await _get_image_bytes(message, bot)
            if not image_bytes:
                await message.answer("Could not download the image. Please try again.")
                return

            base64_image = _encode_image(image_bytes)
            
            prompt_text = caption or ("Extract all text from this image." if is_ocr else "What is in this image? Please describe it in detail.")
            
            if is_ocr:
                if caption:
                    system_content = OCR_PROMPT_WITH_CAPTION.format(caption=caption)
                else:
                    system_content = OCR_PROMPT
            else:
                if caption:
                    system_content = VISION_PROMPT_WITH_CAPTION.format(caption=caption)
                else:
                    system_content = VISION_PROMPT
            
            messages = [
                {"role": "system", "content": system_prompt + "\n\n" + system_content},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]

            await message.answer(processing_msg)

            full_response = ""
            async for partial in ai_client.get_response(messages, stream=True):
                full_response = partial

            if not full_response:
                full_response = "I couldn't analyze the image. Please try again."

            if caption:
                await history_manager.add_message(message.chat.id, "user", f"[Image] {caption}")
            else:
                await history_manager.add_message(message.chat.id, "user", "[Image]")
            await history_manager.add_message(message.chat.id, "assistant", full_response)

            for part in _split_long_message(full_response):
                # Add follow-up keyboard only to the last part
                if part == _split_long_message(full_response)[-1]:
                    await message.answer(part, parse_mode="Markdown", reply_markup=get_image_followup_keyboard())
                else:
                    await message.answer(part, parse_mode="Markdown")

        except Exception as e:
            logger.error("Error processing image in chat %s: %s", message.chat.id, e, exc_info=True)
            await message.answer("Sorry, something went wrong while processing the image.")


@router.callback_query(lambda c: c.data == "image:ocr")
async def cb_image_ocr(callback: CallbackQuery, ai_client, history_manager, bot_username: str, system_prompt: str):
    """Trigger OCR on the last image."""
    # Get the last image from history or ask user to send again
    await callback.message.edit_text(
        "📝 <b>OCR Mode</b>\n\nPlease send the image again with caption \"read this\" or \"متن رو بخون\" for text extraction.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "image:deeper")
async def cb_image_deeper(callback: CallbackQuery, ai_client, history_manager, bot_username: str, system_prompt: str):
    """Analyze the last image more deeply."""
    await callback.message.edit_text(
        "🔍 <b>Deeper Analysis</b>\n\nPlease send the image again with a specific question for detailed analysis.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "image:translate")
async def cb_image_translate(callback: CallbackQuery, ai_client, history_manager, bot_username: str, system_prompt: str):
    """Translate text in the last image."""
    await callback.message.edit_text(
        "🌐 <b>Translate Image Text</b>\n\nSend the image again and specify the target language (e.g., \"translate to English\").",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "image:save")
async def cb_image_save(callback: CallbackQuery):
    """Save image analysis result."""
    await callback.answer("💾 Saved! You can find it in your chat history.", show_alert=True)


def _split_long_message(text: str, max_length: int = 4096) -> list[str]:
    if len(text) <= max_length:
        return [text]

    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = text.rfind(" ", 0, max_length)
        if split_at == -1:
            split_at = max_length
        parts.append(text[:split_at])
        text = text[split_at:].strip()
    return parts


class ImageFilter(Filter):
    """Filter for detecting images sent to the bot."""
    
    def __init__(self, bot_id: int, bot_username: str, bot_name: str):
        self.bot_id = bot_id
        self.bot_username = bot_username.lower()
        self.bot_name = bot_name.lower()
        self.persian_name = "جاوید"

    async def __call__(self, message: Message) -> bool:
        if not message.photo:
            return False

        if message.chat.type == ChatType.PRIVATE:
            return True

        if message.caption:
            caption_lower = message.caption.lower()
            if f"@{self.bot_username}" in caption_lower:
                return True
            if self.bot_name in caption_lower:
                return True
            if caption_lower.strip().startswith(self.persian_name):
                return True

        if message.reply_to_message and message.reply_to_message.from_user:
            if message.reply_to_message.from_user.id == self.bot_id:
                return True

        return False


@router.message(
    ChatTypeFilter([ChatType.PRIVATE]),
    F.photo,
)
async def handle_private_image(message: Message, ai_client, history_manager, bot_username: str, system_prompt: str):
    await _process_image_message(message, ai_client, history_manager, bot_username, system_prompt, caption=message.caption)


@router.message(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),
    F.photo,
)
async def handle_group_image(
    message: Message,
    ai_client,
    history_manager,
    bot_username: str,
    system_prompt: str,
    bot_id: int,
    bot_name: str,
):
    image_filter = ImageFilter(bot_id, bot_username, bot_name)
    if not await image_filter(message):
        return

    caption = message.caption
    is_reply = message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot_id

    if caption:
        caption_lower = caption.lower()
        if f"@{bot_username.lower()}" in caption_lower:
            caption = caption.replace(f"@{bot_username}", "").strip()
        elif bot_name.lower() in caption_lower:
            caption = caption.replace(bot_name, "").strip()
        elif caption.strip().lower().startswith("جاوید"):
            caption = caption.strip()[len("جاوید"):].strip()
            if caption and caption[0] in "،.?!؛،":
                caption = caption[1:].strip()

    await _process_image_message(
        message, ai_client, history_manager, bot_username, system_prompt,
        caption=caption if caption else None, is_reply=is_reply
    )