import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from utils.web_search_client import (
    SerperSearchClient,
    GoogleSearchClient,
    BingSearchClient,
    BraveSearchClient,
    DuckDuckGoClient,
)

router = Router()
logger = logging.getLogger(__name__)


def get_search_clients():
    from config import config
    clients = []
    if config.serper_api_key:
        clients.append(("Google (Serper)", SerperSearchClient(config.serper_api_key)))
    if config.google_api_key and config.google_cx:
        clients.append(("Google", GoogleSearchClient(config.google_api_key, config.google_cx)))
    if config.bing_api_key:
        clients.append(("Bing", BingSearchClient(config.bing_api_key)))
    if config.brave_api_key:
        clients.append(("Brave", BraveSearchClient(config.brave_api_key)))
    clients.append(("DuckDuckGo", DuckDuckGoClient()))
    return clients


@router.message(Command("search", "web", "web_search", "google"))
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

    clients = get_search_clients()
    if not clients:
        await message.answer(
            "Web search is not configured. Please set up at least one search API (Serper, Google, Bing, Brave) or use DuckDuckGo (no API key required).",
            parse_mode="HTML",
        )
        return

    await message.answer(f"🔍 Searching the web for: <b>{query}</b>...", parse_mode="HTML")

    all_results = []
    for source_name, client in clients:
        try:
            results = await client.search(query, num_results=5)
            for result in results:
                result["source"] = source_name
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Error searching {source_name}: {e}")

    if not all_results:
        await message.answer("No results found. Try a different search query.")
        return

    seen_urls = set()
    unique_results = []
    for result in all_results:
        url = result.get("link") or result.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)

    for result in unique_results[:8]:
        title = result.get("title", "No title")
        snippet = result.get("snippet", "No description available")
        link = result.get("link") or result.get("url", "")
        source = result.get("source", "Unknown")

        caption = (
            f"🔍 <b>{title}</b>\n"
            f"{snippet}\n"
            f"🌐 Source: {source}"
        )

        if link:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🌐 Open", url=link)
            ]])
        else:
            keyboard = None

        await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)