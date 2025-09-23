import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from database.db import init_db
from handlers.admin_handlers import register_admin_handlers, send_birthday_notifications, obhavo_command_telegram
from handlers.user_handlers import register_user_handlers
import pytz
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Bot tokenini o'rnatish
BOT_TOKEN = "7577757347:AAHcnJTtIidThEN6GbnRZEFiieeKFWyThMk"

CHANNEL_ID = "@kompyuter_programmalar_dasturlar"     # ob-havo va tug‘ilgan kun xabarlari uchun kanal
ADMIN_ID = 2004004762           # Adminning Telegram ID si
WEATHER_API_KEY = "e4016445b7fb35f0746afcc49c41a0ef"
CITY = "Samarqand"
API_URL = "https://student.samtuit.uz/rest/v1/data/employee-list?type=all"
API_TOKEN = "Y-R36P1BY-eLfuCwQbcbAlvt9GAMk-WP"



async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    print("Initializing database...")
    await init_db()
    
    print("Registering handlers...")
    register_admin_handlers(dp, bot)
    register_user_handlers(dp, bot)

    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tashkent"))
    scheduler.add_job(send_birthday_notifications, trigger='cron', hour=8, minute=00, misfire_grace_time=20)
    scheduler.add_job(obhavo_command_telegram, trigger='cron', hour=6, minute=0, misfire_grace_time=30)
    scheduler.start()
    
    try:
        print("✅ Bot ishga tushdi...")
        await dp.start_polling(bot)
    except Exception as e:
        print(F"Shutting down bot...{e}")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

