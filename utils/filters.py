from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import Message


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[ChatType]):
        self.chat_types = chat_types

    async def __call__(self, message: Message) -> bool:
        return message.chat.type in self.chat_types


class MentionFilter(Filter):
    def __init__(self, bot_username: str):
        self.bot_username = bot_username.lower()

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        text_lower = message.text.lower()
        if f"@{self.bot_username}" in text_lower:
            return True
        if message.entities:
            for entity in message.entities:
                if entity.type == "mention":
                    mention = message.text[entity.offset : entity.offset + entity.length]
                    if mention.lower() == f"@{self.bot_username}":
                        return True
        return False


class ReplyToBotFilter(Filter):
    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def __call__(self, message: Message) -> bool:
        if message.reply_to_message and message.reply_to_message.from_user:
            return message.reply_to_message.from_user.id == self.bot_id
        return False
