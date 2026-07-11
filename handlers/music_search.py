import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from utils.music_search_client import DeezerSearchClient, YouTubeMusicSearchClient, SoundCloudSearchClient

router = Router()
logger = logging.getLogger(__name__)


def get_music_clients():
    from config import config
    clients = []
    clients.append(("Deezer", DeezerSearchClient()))
    if config.youtube_api_key:
        clients.append(("YouTube Music", YouTubeMusicSearchClient(config.youtube_api_key)))
    if config.soundcloud_client_id:
        clients.append(("SoundCloud", SoundCloudSearchClient(config.soundcloud_client_id)))
    return clients


@router.message(Command("music", "song", "track", "search_music"))
async def cmd_music(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: <code>/music <query></code>\n"
            "Example: <code>/music imagine dragons believer</code>",
            parse_mode="HTML",
        )
        return

    query = args[1].strip()
    if not query:
        await message.answer("Please provide a search query. Example: <code>/music coldplay yellow</code>", parse_mode="HTML")
        return

    clients = get_music_clients()
    if not clients:
        await message.answer(
            "Music search is not configured. Please set YOUTUBE_API_KEY for YouTube Music search.",
            parse_mode="HTML",
        )
        return

    await message.answer(f"🎵 Searching for: <b>{query}</b>...", parse_mode="HTML")

    all_results = []
    for source_name, client in clients:
        try:
            results = await client.search(query, limit=5)
            for result in results:
                result["source"] = source_name
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Error searching {source_name}: {e}")

    if not all_results:
        await message.answer("No music found. Try a different search query.")
        return

    seen_links = set()
    unique_results = []
    for result in all_results:
        link = result.get("link", "")
        if link and link not in seen_links:
            seen_links.add(link)
            unique_results.append(result)

    for i, result in enumerate(unique_results[:8]):
        duration_str = ""
        if result.get("duration"):
            mins = result["duration"] // 60
            secs = result["duration"] % 60
            duration_str = f" ⏱ {mins}:{secs:02d}"

        caption = (
            f"🎵 <b>{result['title']}</b>\n"
            f"🎤 {result['artist']}{duration_str}\n"
            f"💿 {result.get('album', 'Unknown Album')}\n"
            f"📍 Source: {result['source']}"
        )

        buttons = []
        if result.get("preview_url"):
            buttons.append(InlineKeyboardButton(text="▶️ Preview", url=result["preview_url"]))
        if result.get("link"):
            buttons.append(InlineKeyboardButton(text="🔗 Open", url=result["link"]))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None

        if result.get("cover_url"):
            try:
                await message.answer_photo(
                    photo=result["cover_url"],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception as e:
                logger.error(f"Error sending music result: {e}")
                await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)