from aiogram import Router, Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from database.db import add_channel, add_video, get_video_votes, get_videos, add_dekanat_to_department, get_users, get_channels, get_departments, get_employees
from utils.auth import is_admin

router = Router()  # Router yaratish

async def admin_start(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"👥 Foydalanuvchilar", callback_data=f"all_users"),
        types.InlineKeyboardButton(text=f"📢 Telgram kanallar", callback_data=f"all_channels")],
        [types.InlineKeyboardButton(text="🗣 Bo'limlar", callback_data=f"all_department"),
        types.InlineKeyboardButton(text="👬 Xodimlar", callback_data=f"all_employee")],
        [types.InlineKeyboardButton(text="🎥 Talaba videolari", callback_data=f"all_video")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text="Quydagilardan birini tanlang", reply_markup=keyboard)

async def users_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    users = await get_users()
    buttons = [
        [types.InlineKeyboardButton(text=f"🆔 {i} - {j}")]
        for i, j in users
    ]
    buttons.append([types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="ortga")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Telegram foydalanuvchilari", reply_markup=keyboard)

async def channels_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    channels = await get_channels()
    buttons = [
        [types.InlineKeyboardButton(text=f"📢 {i}", url=link)]
        for name, link in channels
    ]
    buttons.append([types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="ortga"), types.InlineKeyboardButton(text=f"➕ Kanal q'shish", callback_data="add_channel")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Barcha telegram kannallar", reply_markup=keyboard)

async def department_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    departments = await get_departments()
    buttons = [
        [types.InlineKeyboardButton(text=f"♻️ {department_name}", callback_data=f"department_{department_id}")]
        for department_id, department_name, _ in departments
    ]
    buttons.append([types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="ortga"), types.InlineKeyboardButton(text=f"➕ Bo'lim q'shish", callback_data="add_department")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Barcha bo'limlar", reply_markup=keyboard)

async def employee_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    employees = await get_employees()
    buttons = [
        [types.InlineKeyboardButton(text=f"👤 {employee_name} \n 👍({likes}), 👎({dislikes})", callback_data=f"employe_{employee_id}")]
        for employee_id, employee_name, likes, dislikes, _ in employees
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="ortga"), types.InlineKeyboardButton(text=f"➕ Xodim/o'qituvchi q'shish", callback_data="add_employee")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Barcha xodimlar/o'qituvchilar", reply_markup=keyboard)

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

async def add_department_employee(message: types.Message, command: CommandObject, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    data = command.args.split(",")
    if len(data) < 2:
        await message.reply("❌ Format: /add_dep_emp rasm department_name, employee_name")
        return
    department_name = data[0].strip()
    employee_name = data[1].strip()
    if not message.photo:  # Rasm yuborilganligini tekshirish
        await message.reply("❌ Iltimos, rasm yuboring!")
        return
    photo_id = message.photo[-1].file_id
    try:
        await add_dekanat_to_department(department_name, employee_name, photo_id)
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
    router.message.register(admin_start, Command('start_admin')) # /start_admin hamma malumotlarni chaqirish
    router.callback_query.register(
        users_all,
        lambda c: c.data and c.data.startswith("all_users")  # all users views
    )
    router.callback_query.register(
        channels_all,
        lambda c: c.data and c.data.startswith("all_channels")  # all users views
    )
    router.callback_query.register(
        department_all,
        lambda c: c.data and c.data.startswith("all_department")  # all users views
    )
    router.callback_query.register(
        employee_all,
        lambda c: c.data and c.data.startswith("all_employee")  # all users views
    )
    router.message.register(add_channel_handler, Command("add_channel"))  # /add_channel komandasini ro'yxatga olish
    router.message.register(add_video_handler, Command("add_video"))  # /add_video komandasini ro'yxatga olish
    router.message.register(add_department_employee, Command("add_dep_emp"))
    router.message.register(view_videos_handler, Command("view_videos"))  # /view_videos komandasini ro'yxatga olish
