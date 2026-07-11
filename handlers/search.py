import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from utils.photo_search_client import PhotoSearchClient, PexelsPhotoClient
from utils.music_search_client import YouTubeMusicClient, SoundCloudClient

router = Router()
logger = logging.getLogger(__name__)


def get_photo_client():
    from config import config
    if config.unsplash_api_key:
        return PhotoSearchClient(config.unsplash_api_key)
    elif config.pexels_api_key:
        return PexelsPhotoClient(config.pexels_api_key)
    return None


def get_music_clients():
    from config import config
    clients = []
    if config.youtube_api_key:
        clients.append(("YouTube Music", YouTubeMusicClient(config.youtube_api_key)))
    if config.soundcloud_client_id:
        clients.append(("SoundCloud", SoundCloudClient(config.soundcloud_client_id)))
    return clients


@router.message(Command("photo", "photo_search", "img", "image"))
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
        await message.answer("Please provide a search query. Example: <code>/photo sunset</code>", parse_mode="HTML")
        return

    client = get_photo_client()
    if not client:
        await message.answer(
            "Photo search is not configured. Please set up Unsplash or Pexels API key.",
            parse_mode="HTML",
        )
        return

    await message.answer(f"🔍 Searching for photos: <b>{query}</b>...", parse_mode="HTML")

    results = await client.search(query, per_page=10)

    if not results:
        await message.answer("No photos found. Try a different search query.")
        return

    for i, photo in enumerate(results[:5]):
        caption = (
            f"📸 <b>{photo['description']}</b>\n"
            f"📷 By <a href='{photo['photographer_url']}'>{photo['photographer']}</a>\n"
            f"🔗 <a href='{photo['url']}'>View on source</a>"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔗 Open Photo", url=photo["url"])
        ]])

        try:
            await message.answer_photo(
                photo=photo["url"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(f"Failed to send photo {i}: {e}")
            await message.answer(f"📸 {photo['description']}\n🔗 {photo['url']}", parse_mode="HTML")


@router.message(Command("music", "music_search", "song", "song_search"))
async def cmd_music(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: <code>/music <query></code>\n"
            "Example: <code>/music Imagine Dragons Believer</code>",
            parse_mode="HTML",
        )
        return

    query = args[1].strip()
    if not query:
        await message.answer("Please provide a search query. Example: <code>/music Imagine Dragons</code>", parse_mode="HTML")
        return

    clients = get_music_clients()
    if not clients:
        await message.answer(
            "Music search is not configured. Please set up YouTube API or SoundCloud client ID.",
            parse_mode="HTML",
        )
        return

    await message.answer(f"🎵 Searching for music: <b>{query}</b>...", parse_mode="HTML")

    all_results = []
    for source_name, client in clients:
        try:
            results = await client.search(query, max_results=5)
            for result in results:
                result["source"] = source_name
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Error searching {source_name}: {e}")

    if not all_results:
        await message.answer("No music found. Try a different search query.")
        return

    for i, track in enumerate(all_results[:8]):
        duration = track.get("duration", "")
        dur_str = f" ⏱ {duration}" if duration else ""

        caption = (
            f"🎵 <b>{track['title']}</b>\n"
            f"🎤 {track['artist']}{dur_str}\n"
            f"🎧 Source: {track['source']}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="▶️ Play", url=track["url"])
        ]])

        thumbnail = track.get("thumbnail")
        if thumbnail:
            try:
                await message.answer_photo(
                    photo=thumbnail,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception:
                await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)