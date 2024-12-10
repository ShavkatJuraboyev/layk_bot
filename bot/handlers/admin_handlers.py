from aiogram import types
from aiogram import Router, Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from database.db import add_channel, add_video, get_video_votes, get_videos, add_dekanat_to_department
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
async def add_video_handler(message: types.Message, command: CommandObject, bot: Bot):
    # Adminni tekshirish
    if not is_admin(message.from_user.id):  
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    # Komanda argumentlarini olish
    video_name = command.args  # /add_video <video nomi>

    if not video_name:
        await message.reply("❌ Videoga nom kiriting: /add_video <nom>")
        return

    if message.video:
        # Video va nomni bazaga qo'shish
        await add_video(file_id=message.video.file_id, name=video_name)
        await message.reply("✅ Video va nom qo'shildi!")
    else:
        await message.reply("❌ Iltimos, video yuboring!")

async def add_department_employee(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ Format: /add_dep_emp department_name, employee_name")
        return

    data = args[1].split(",", maxsplit=1)
    if len(data) < 2:
        await message.reply("❌ Format: /add_dep_emp department_name, employee_name")
        return

    department_name = data[0].strip()
    employee_name = data[1].strip()

    try:
        await add_dekanat_to_department(department_name, employee_name)
        await message.reply("✅ Muvafaqiyatli qo'shildi!")
    except Exception as e:
        await message.reply(f"❌ Xatolik: {e}")


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
    for video in videos:
        if len(video) == 5:
            video_id, file_id, name, likes, dislikes = video
            votes = await get_video_votes(video_id)
            # Video va uning ovozlari haqida ma'lumot yuborish
            text = f"Video ID: {video_id}\n"
            text += f"Video nomi: {name}\n"
            text += f"Likes: {votes['likes']}, Dislikes: {votes['dislikes']}"
            await message.reply(text)
        else:
            print(f"Noto'g'ri format: {video}")

# Router yordamida handlerlarni ro'yxatga olish
def register_admin_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(add_channel_handler, Command("add_channel"))  # /add_channel komandasini ro'yxatga olish
    router.message.register(add_video_handler, Command("add_video"))  # /add_video komandasini ro'yxatga olish
    router.message.register(add_department_employee, Command("add_dep_emp"))
    router.message.register(view_videos_handler, Command("view_videos"))  # /view_videos komandasini ro'yxatga olish
