import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from utils.web_search_client import DuckDuckGoClient

router = Router()
logger = logging.getLogger(__name__)


def get_search_client():
    return DuckDuckGoClient()


@router.message(Command("search", "web", "web_search"))
async def cmd_web_search(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: <code>/search <query></code>\n"
            "Example: <code>/search python asyncio tutorial</code>",
            parse_mode="HTML",
        )
        return

    query = args[1].strip()
    if not query:
        await message.answer("Please provide a search query. Example: <code>/search python tutorial</code>", parse_mode="HTML")
        return

    client = get_search_client()

    await message.answer(f"🔍 Searching the web for: <b>{query}</b>...", parse_mode="HTML")

    try:
        results = await client.search(query, num_results=8)
    except Exception as e:
        logger.error(f"Error searching: {e}")
        await message.answer("Sorry, something went wrong while searching.")
        return

    if not results:
        await message.answer("No results found. Try a different search query.")
        return

    # Check for CAPTCHA/blocked result
    if len(results) == 1 and results[0].get("title") == "Search blocked":
        await message.answer(
            "🔒 <b>Search temporarily unavailable</b>\n\n"
            "DuckDuckGo is blocking automated requests from this IP.\n"
            "This is common on cloud hosting platforms like Railway.\n\n"
            "You can:\n"
            "• Try a different search query\n"
            "• Use a different search engine manually\n"
            "• Configure a proxy in bot settings (if available)",
            parse_mode="HTML",
        )
        return

    seen_urls = set()
    unique_results = []
    for result in results:
        url = result.get("link")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)

    for result in unique_results[:8]:
        title = result.get("title", "No title")
        snippet = result.get("snippet", "No description available")
        link = result.get("link", "")

        caption = (
            f"🔍 <b>{title}</b>\n"
            f"{snippet}\n"
            f"🌐 Source: DuckDuckGo"
        )

        if link:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🌐 Open", url=link)
            ]])
        else:
            keyboard = None

        await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)