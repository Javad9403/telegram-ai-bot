import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import config
from handlers import commands as commands_handler
from handlers import chat as chat_handler
from handlers import web_search as web_search_handler
from handlers import image as image_handler
from utils.ai_client import AIClient
from utils.history import HistoryManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, dispatcher: Dispatcher):
    bot_user = await bot.get_me()
    dispatcher["bot_username"] = bot_user.username
    dispatcher["bot_id"] = bot_user.id
    dispatcher["bot_name"] = bot_user.first_name.lower()

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start the bot"),
            BotCommand(command="help", description="Show help"),
            BotCommand(command="clear", description="Clear conversation history"),
            BotCommand(command="setmodel", description="Change AI model"),
            BotCommand(command="search", description="Search the web"),
            BotCommand(command="owner", description="Show owner information"),
            BotCommand(command="me", description="Show your user info"),
        ],
        scope=BotCommandScopeDefault(),
    )
    logger.info("Bot started as @%s", bot_user.username)


async def on_shutdown(bot: Bot, dispatcher: Dispatcher):
    history_manager: HistoryManager = dispatcher.get("history_manager")
    if history_manager:
        await history_manager.close()
    logger.info("Bot shut down")


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    ai_client = AIClient(
        base_url=config.openai_base_url,
        api_key=config.openai_api_key,
        model=config.ai_model,
        vision_base_url=config.vision_base_url,
        vision_api_key=config.vision_api_key,
        vision_model=config.vision_model,
    )
    history_manager = HistoryManager(redis_url=config.redis_url, ai_client=ai_client)

    dp["ai_client"] = ai_client
    dp["history_manager"] = history_manager
    dp["system_prompt"] = config.system_prompt
    dp["owner_id"] = config.owner_id
    dp["owner_name"] = config.owner_name
    dp["owner_roles"] = config.owner_roles

    dp.include_router(commands_handler.router)
    dp.include_router(web_search_handler.router)
    dp.include_router(chat_handler.router)
    dp.include_router(image_handler.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    return dp


async def main():
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = create_dispatcher()

    if config.use_webhook_enabled:
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=config.webhook_port)
        await site.start()
        logger.info("Webhook started on port %s", config.webhook_port)
        await asyncio.Event().wait()
    else:
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())