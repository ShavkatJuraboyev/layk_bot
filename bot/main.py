# import asyncio
# from aiogram import Bot, Dispatcher
# from aiogram.fsm.storage.memory import MemoryStorage
# from database.db import init_db
# from handlers.user_handlers import register_user_handlers
# from handlers.admin_handlers import register_admin_handlers

# API_TOKEN = "5131381239:AAHm0l1BmMt4nIpw3mKBfvOrtK_eZ2pooPc"
# ADMINS = [1421622919]  # Adminlarning Telegram ID-lari

# bot = Bot(token=API_TOKEN)
# storage = MemoryStorage()

# # Creating Dispatcher with bot
# dp = Dispatcher(storage=storage)  # Only storage is passed to Dispatcher now

# async def on_startup():
#     # Database and handler registrations
#     await init_db()
#     register_user_handlers(dp, bot)  # Registering handlers with bot
#     register_admin_handlers(dp, bot)  # Registering handlers with bot

# async def main():
#     await on_startup()
#     await dp.start_polling()

# if __name__ == "__main__":
#     asyncio.run(main()

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database.db import init_db
from handlers.admin_handlers import register_admin_handlers
from handlers.user_handlers import register_user_handlers
from utils.auth import is_admin

# Bot tokenini o'rnatish
BOT_TOKEN = "5131381239:AAHm0l1BmMt4nIpw3mKBfvOrtK_eZ2pooPc"

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
    
    # Botni ishga tushirish
    try:
        print("Bot is starting...")
        await dp.start_polling(bot)
    finally:
        # Botni to'xtatishda resurslarni tozalash
        print("Shutting down bot...")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
