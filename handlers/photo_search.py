import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from utils.photos_search_client import PhotoSearchClient

router = Router()
logger = logging.getLogger(__name__)


def get_photo_client():
    from config import config
    if config.unsplash_access_key:
        return PhotoSearchClient(config.unsplash_access_key)
    return None


@router.message(Command("photo", "image", "img", "search_photo"))
async def cmd_photo(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: <code>/photo <query></code>\n"
            "Example: <code>/photo sunset beach</code>",
            parse_mode="HTML",
        )
        return

    query = args[1].strip()
    if not query:
        await message.answer("Please provide a search query. Example: <code>/photo cats</code>", parse_mode="HTML")
        return

    client = get_photo_client()
    if not client:
        await message.answer(
            "Photo search is not configured. Please set UNSPLASH_ACCESS_KEY in environment variables.",
            parse_mode="HTML",
        )
        return

    await message.answer(f"🔍 Searching photos for: <b>{query}</b>...", parse_mode="HTML")

    try:
        photos = await client.search(query, per_page=10)
    except Exception as e:
        logger.error(f"Error searching photos: {e}")
        await message.answer("Sorry, something went wrong while searching photos.")
        return

    if not photos:
        await message.answer("No photos found. Try a different search query.")
        return

    for photo in photos[:5]:
        caption = (
            f"📸 <b>{photo['description']}</b>\n"
            f"👤 By: <a href='{photo['photographer_url']}'>{photo['photographer']}</a>\n"
            f"🔗 <a href='{photo['url']}'>View on Unsplash</a>"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 View on Unsplash", url=photo["url"])],
            [InlineKeyboardButton(text="👤 Photographer", url=photo["photographer_url"])],
        ])

        try:
            await message.answer_photo(
                photo=photo["url"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)