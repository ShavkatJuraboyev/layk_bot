import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, AUTO_NOTIFY_ENABLED
from database.db import init_db
from handlers.admin_handlers import register_admin_handlers
from handlers.user_handlers import register_user_handlers
from services.notifications import daily_notifications_loop


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    await init_db()
    register_admin_handlers(dp, bot)
    register_user_handlers(dp, bot)

    notify_task = None
    if AUTO_NOTIFY_ENABLED:
        notify_task = asyncio.create_task(daily_notifications_loop(bot))

    try:
        await dp.start_polling(bot)
    finally:
        if notify_task:
            notify_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
