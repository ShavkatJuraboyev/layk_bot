import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from database.db import init_db
from handlers.admin_handlers import register_admin_handlers, morning_job, send_birthday_notifications
from handlers.user_handlers import register_user_handlers
import pytz
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.enums import ParseMode

# Bot tokenini o'rnatish
BOT_TOKEN = "6239778268:AAFmIdsNKmjzMFRbVodT74TU0Dl1boR5ivE"

CHANNEL_ID = "@kompyuter_programmalar_dasturlar"     # ob-havo va tug‘ilgan kun xabarlari uchun kanal
ADMIN_ID = 1421622919           # Adminning Telegram ID si
WEATHER_API_KEY = "e4016445b7fb35f0746afcc49c41a0ef"
CITY = "Samarqand"
API_URL = "https://student.samtuit.uz/rest/v1/data/employee-list?type=all"
API_TOKEN = "Y-R36P1BY-eLfuCwQbcbAlvt9GAMk-WP"



async def main():
    # Bot va Dispatcher obyektlarini yaratish
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Ma'lumotlar bazasini ishga tushirish
    print("Initializing database...")
    await init_db()
    
    # Handlerlarni ro'yxatga olish
    print("Registering handlers...")
    register_admin_handlers(dp, bot)
    register_user_handlers(dp, bot)

    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tashkent"))
    scheduler.add_job(morning_job, "cron", hour=9, minute=10)  # har kuni 07:00 da ishga tushadi
    scheduler.add_job(send_birthday_notifications, trigger='cron', hour=9, minute=10, misfire_grace_time=30)
  # har kuni 09:00 da ishga tushadi
    scheduler.start()
    
    # Botni ishga tushirish
    try:
        print("✅ Bot ishga tushdi...")
        await dp.start_polling(bot)
    finally:
        # Botni to'xtatishda resurslarni tozalash
        print("Shutting down bot...")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
