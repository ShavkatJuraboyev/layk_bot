import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database.db import init_db
from handlers.user_handlers import register_user_handlers
from handlers.admin_handlers import register_admin_handlers

API_TOKEN = "5131381239:AAHm0l1BmMt4nIpw3mKBfvOrtK_eZ2pooPc"
ADMINS = [1421622919]  # Adminlarning Telegram ID-lari

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()  # In-memory storage

# Creating Dispatcher with bot
dp = Dispatcher(storage=storage)  # Only storage is passed to Dispatcher now

# Manually assign bot to dispatcher
dp.bot = bot

async def on_startup():
    # Database and handler registrations
    await init_db()
    register_user_handlers(dp)
    register_admin_handlers(dp)

async def main():
    # Calling on_startup before polling
    await on_startup()
    # Starting polling
    await dp.start_polling()

if __name__ == "__main__":
    # Running the main function using asyncio
    asyncio.run(main())
