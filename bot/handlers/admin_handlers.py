from aiogram import types
from aiogram import Router, Bot, Dispatcher
from aiogram.filters import Command
from database.db import add_channel, add_video, get_video_votes, get_videos
from utils.auth import is_admin

router = Router()  # Router yaratish

# /add_channel komandasi handleri
async def add_channel_handler(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):  # Admin tekshiruvi
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply("❌ Format: /add_channel Nomi Link")
        return
    name, link = args[1], args[2]
    await add_channel(name, link)
    await message.reply("✅ Kanal qo'shildi!")

# /add_video komandasi handleri
async def add_video_handler(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):  # Admin tekshiruvi
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    if message.video:
        await add_video(message.video.file_id)
        await message.reply("✅ Video qo'shildi!")
    else:
        await message.reply("❌ Video yuboring!")

async def view_videos_handler(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):  # Admin tekshiruvi
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    # Videolarni bazadan olish
    videos = await get_videos()
    if not videos:
        await message.reply("❌ Hech qanday video mavjud emas.")
        return

    # Har bir video uchun ovozlar sonini olish
    for video_id, file_id, likes, dislikes in videos:
        votes = await get_video_votes(video_id)
        # Video va uning ovozlari haqida ma'lumot yuborish
        text = f"Video ID: {video_id}\n"
        text += f"Likes: {votes['likes']}, Dislikes: {votes['dislikes']}"
        
        await message.reply(text)

# Router yordamida handlerlarni ro'yxatga olish
def register_admin_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(add_channel_handler, Command("add_channel"))  # /add_channel komandasini ro'yxatga olish
    router.message.register(add_video_handler, Command("add_video"))  # /add_video komandasini ro'yxatga olish
    router.message.register(view_videos_handler, Command("view_videos"))  # /view_videos komandasini ro'yxatga olish
