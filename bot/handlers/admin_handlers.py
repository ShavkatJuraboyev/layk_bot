from aiogram import types
from aiogram import Router
from aiogram.filters import Command
from database.db import add_channel, add_video
from utils.auth import is_admin

ADMINS = [123456789, 987654321]  # Adminlarning Telegram ID-lari

# Create a Router instance
router = Router()

async def add_channel_handler(message: types.Message):
    if not is_admin(message, ADMINS):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply("❌ Format: /add_channel Nomi Link")
        return
    name, link = args[1], args[2]
    await add_channel(name, link)
    await message.reply("✅ Kanal qo'shildi!")

async def add_video_handler(message: types.Message):
    if not is_admin(message, ADMINS):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    if message.video:
        await add_video(message.video.file_id)
        await message.reply("✅ Video qo'shildi!")

# Function to register the handlers with the router
def register_admin_handlers(dp):
    dp.include_router(router)  # Include the router into the Dispatcher
    # Register the handlers for commands and content types using proper filters
    router.message.register(add_channel_handler, Command("add_channel"))  # Correctly using Command filter
    # router.message.register(add_video_handler, content_types=["video"])
