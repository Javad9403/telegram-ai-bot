import logging
import re

from aiogram import Router, F
from aiogram.enums import ChatType, ChatAction
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from utils.filters import ChatTypeFilter, MentionFilter, ReplyToBotFilter, BotNameFilter, PersianNameFilter, clean_persian_name, OwnerFilter
from config import config

router = Router()
logger = logging.getLogger(__name__)


def _clean_mention(text: str, bot_username: str) -> str:
    cleaned = re.sub(rf"@{re.escape(bot_username)}\b", "", text, flags=re.IGNORECASE).strip()
    return cleaned


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


@router.message(
    ChatTypeFilter([ChatType.PRIVATE]),
    F.text,
)
async def handle_private_message(message: Message, ai_client, history_manager, bot_username: str, system_prompt: str, owner_id: int, owner_name: str, owner_roles: list[str]):
    owner_filter = OwnerFilter(owner_id)
    is_owner = await owner_filter(message)
    
    if is_owner:
        owner_context = f"\n\n[Note: The user is the bot owner '{owner_name}' ({', '.join(owner_roles)}). Acknowledge this role appropriately.]"
        system_prompt = system_prompt + owner_context

    await _process_message(message, ai_client, history_manager, bot_username, system_prompt)


@router.message(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),
    F.text,
)
async def handle_group_message(
    message: Message,
    ai_client,
    history_manager,
    bot_username: str,
    system_prompt: str,
    bot_id: int,
    bot_name: str,
    owner_id: int,
    owner_name: str,
    owner_roles: list[str],
):
    mention_filter = MentionFilter(bot_username)
    reply_filter = ReplyToBotFilter(bot_id)
    name_filter = BotNameFilter(bot_name)
    persian_name_filter = PersianNameFilter()
    owner_filter = OwnerFilter(owner_id)

    is_mention = await mention_filter(message)
    is_reply = await reply_filter(message)
    is_name = await name_filter(message)
    is_persian_name = await persian_name_filter(message)
    is_owner = await owner_filter(message)

    if not is_mention and not is_reply and not is_name and not is_persian_name:
        return

    # Clean up the message based on what triggered it
    clean_mention = is_mention or is_name
    clean_persian = is_persian_name

    # Add owner context to system prompt if user is owner
    if is_owner:
        owner_context = f"\n\n[Note: The user is the bot owner '{owner_name}' ({', '.join(owner_roles)}). Acknowledge this role appropriately.]"
        system_prompt = system_prompt + owner_context

    await _process_message(
        message,
        ai_client,
        history_manager,
        bot_username,
        system_prompt,
        clean_mention=clean_mention,
        clean_persian=clean_persian,
    )


async def _process_message(
    message: Message,
    ai_client,
    history_manager,
    bot_username: str,
    system_prompt: str,
    clean_mention: bool = False,
    clean_persian: bool = False,
):
    text = message.text

    if clean_mention:
        text = _clean_mention(text, bot_username)
        if not text:
            text = "Hello"

    if clean_persian:
        text = clean_persian_name(text)
        if not text:
            text = "Hello"

    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
        try:
            await history_manager.add_message(message.chat.id, "user", text)

            messages = [{"role": "system", "content": system_prompt}]
            history = await history_manager.get_history(message.chat.id)
            messages.extend(history)

            full_response = ""
            async for partial in ai_client.get_response(messages):
                full_response = partial

            if not full_response:
                full_response = "I'm not sure how to respond to that."

            await history_manager.add_message(message.chat.id, "assistant", full_response)

            for part in _split_long_message(full_response):
                await message.answer(part, parse_mode="Markdown")

        except Exception as e:
            logger.error("Error processing message in chat %s: %s", message.chat.id, e, exc_info=True)
            await message.answer("Sorry, something went wrong while processing your message.")
