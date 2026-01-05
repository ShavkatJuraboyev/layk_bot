import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from database.db import init_db
from handlers.admin_handlers import register_admin_handlers
from handlers.user_handlers import register_user_handlers
import pytz
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Bot tokenini o'rnatish
BOT_TOKEN = "7577757347:AAHcnJTtIidThEN6GbnRZEFiieeKFWyThMk"

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    await init_db()
    register_admin_handlers(dp, bot)
    register_user_handlers(dp, bot)

    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tashkent"))
    # scheduler.add_job(send_birthday_notifications, trigger='cron', hour=8, minute=00, misfire_grace_time=20)
    # scheduler.add_job(obhavo_command_telegram, trigger='cron', hour=6, minute=0, misfire_grace_time=30)
    scheduler.start()
    try:
        await dp.start_polling(bot)
    except Exception as e:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
