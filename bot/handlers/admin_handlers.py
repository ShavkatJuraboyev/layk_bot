from aiogram import Router, Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from database.db import add_channel, add_video, get_video_votes, get_videos, add_dekanat_to_department, get_users, get_channels, get_departments, get_employees
from utils.auth import is_admin

router = Router()  # Router yaratish

async def admin_start(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
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

async def admin_start_back(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"👥 Foydalanuvchilar", callback_data=f"all_users"),
        types.InlineKeyboardButton(text=f"📢 Telgram kanallar", callback_data=f"all_channels")],
        [types.InlineKeyboardButton(text="🗣 Bo'limlar", callback_data=f"all_department"),
        types.InlineKeyboardButton(text="👬 Xodimlar", callback_data=f"all_employee")],
        [types.InlineKeyboardButton(text="🎥 Talaba videolari", callback_data=f"all_video")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Quydagilardan birini tanlang", reply_markup=keyboard)
    await callback.message.delete()

async def users_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    users = await get_users()
    if not users:
        button = [[types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.answer(text="❌ Hech qanday foydalanuvchi mavjud emas", reply_markup=keyboard)
        await callback.message.delete()
        return
    buttons = [
        [types.InlineKeyboardButton(text=f"🆔 {i} - {j}")]
        for i, j in users
    ]
    buttons.append([types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="back_admin")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Telegram foydalanuvchilari", reply_markup=keyboard)
    await callback.message.delete()

async def channels_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    channels = await get_channels()
    if not channels:
        button = [[
            types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin"), 
            types.InlineKeyboardButton(text=f"➕ Kanal qo'shish", callback_data="add_channel")
            ]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.answer(text="❌ Hech qanday Kanal mavjud emas", reply_markup=keyboard)
        await callback.message.delete()
        return
    buttons = [
        [types.InlineKeyboardButton(text=f"📢 {name}", url=link)]
        for name, link in channels
    ]
    buttons.append([
        types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="back_admin"), 
        types.InlineKeyboardButton(text=f"➕ Kanal qo'shish", callback_data="add_channel")
        ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Barcha telegram kannallar", reply_markup=keyboard)
    await callback.message.delete()

async def add_channel_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):  # Admin tekshiruvi
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return
    button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_channels")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer(
        "Kanal nomi va kanal linkini quyidagi formatda yuboring:\n"
        "Na'muna: `/add_channel Kanal_nomi, https://t.me/kanal_link`",
        parse_mode="Markdown", reply_markup=keyboard
    )

async def add_channel_save(message: types.Message,  command: CommandObject, bot: Bot):
    if not is_admin(message.from_user.id):  # Admin tekshiruvi
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await message.delete()
        return
    try:
        data = command.args.split(",")
        if len(data) < 2:
            await message.reply("❌ Format: `/add_channel Kanal_nomi, https://t.me/kanal_link`")
            return
        kanal_name = data[0].strip()
        kanal_link = data[1].strip()

        if not kanal_name or not kanal_link.startswith("http"):
            raise ValueError

        await add_channel(kanal_name, kanal_link)
        button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_channels")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await message.answer(f"✅ Kanal qo'shildi:\nNomi: {kanal_name}\nLink: {kanal_link}", reply_markup=keyboard)
    except ValueError:
        await message.answer(
            "❌ Xato! Formatni tekshiring va qaytadan yuboring:\n"
            "Na'muna: `/add_channel Kanal_nomi, https://t.me/kanal_link`",
            parse_mode="Markdown")

async def department_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    departments = await get_departments()
    if not departments:
        button = [[types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.answer(text="❌ Hech qanday bo'lim mavjud emas", reply_markup=keyboard)
        await callback.message.delete()
        return
    buttons = [
        [types.InlineKeyboardButton(text=f"♻️ {department_name}", callback_data=f"department_{department_id}")]
        for department_id, department_name, _ in departments
    ]
    buttons.append([types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="back_admin"), types.InlineKeyboardButton(text=f"➕ Bo'lim q'shish", callback_data="add_department")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Barcha bo'limlar", reply_markup=keyboard)
    await callback.message.delete()

async def employee_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    employees = await get_employees()
    if not employees:
        button = [[types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.answer(text="❌ Hech qanday xodim mavjud emas", reply_markup=keyboard)
        await callback.message.delete()
        return
    buttons = [
        [types.InlineKeyboardButton(text=f"👤 {employee_name} \n 👍({likes}), 👎({dislikes})", callback_data=f"employe_{employee_id}")]
        for employee_id, employee_name, likes, dislikes, _ in employees
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin"), types.InlineKeyboardButton(text=f"➕ Xodim/o'qituvchi q'shish", callback_data="add_employee")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Barcha xodimlar/o'qituvchilar", reply_markup=keyboard)
    await callback.message.delete()

async def view_videos_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    videos = await get_videos()
    if not videos:
        button = [[
            types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin"), 
            types.InlineKeyboardButton(text=f"➕ Video qo'shish", callback_data="add_video")
            ]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.answer(text="❌ Hech qanday video mavjud emas", reply_markup=keyboard)
        await callback.message.delete()
        return
    button = [
        [types.InlineKeyboardButton(text=f"👤 {name}, 🆔-{video_id}, 👍({likes})-👎({dislikes})", callback_data=f"talaba_{video_id}")]
        for video_id, _, name, likes, dislikes in videos
    ]
    button.append(
        [types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin"), 
        types.InlineKeyboardButton(text=f"➕ Video qo'shish", callback_data="add_video")
        ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer(text="Barcha talaba foydalanuvchilar", reply_markup=keyboard)
    await callback.message.delete()


async def add_video_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):  # Admin tekshiruvi
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return
    button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_video")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer(
        "Video va talab ismi va familiyasini quyidagi formatda yuboring:\n"
        "Na'muna: `/add_video Talaba ism familiyasi`",
        parse_mode="Markdown", reply_markup=keyboard
    )

async def add_video_save(message: types.Message, command: CommandObject, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await message.delete()
        return

    try:
        video_name = command.args  
        if not video_name:
            await message.reply("❌ Namuna: `/add_video Talaba ism familiyasi`")
            return ValueError

        if message.video:
            await add_video(file_id=message.video.file_id, name=video_name)
            button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_video")]]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
            await message.answer("✅ Video va nom qo'shildi!", reply_markup=keyboard)
        else:
            await message.reply("❌ Iltimos, video yuboring!")
            return ValueError

    except ValueError:
        await message.answer(
            "❌ Xato! Formatni tekshiring va qaytadan yuboring:\n"
            "Na'muna: `/add_video Talaba ism familiyasi``",
            parse_mode="Markdown")

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


# Router yordamida handlerlarni ro'yxatga olish
def register_admin_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(admin_start, Command('start_admin'))
    router.callback_query.register(
        admin_start_back,
        lambda c: c.data and c.data.startswith('back_admin')
    )
    router.callback_query.register(
        users_all,
        lambda c: c.data and c.data.startswith("all_users")  # all users views
    )

    # barcha kanallar ustida amallar
    router.callback_query.register(
        channels_all,
        lambda c: c.data and c.data.startswith("all_channels")  # all users views
    )
    router.callback_query.register(
        add_channel_handler, 
        lambda c: c.data and c.data.startswith("add_channel")
    )
    router.message.register(add_channel_save, Command("add_channel"))

    router.callback_query.register(
        department_all,
        lambda c: c.data and c.data.startswith("all_department")  # all users views
    )
    router.callback_query.register(
        employee_all,
        lambda c: c.data and c.data.startswith("all_employee")  # all users views
    )
    router.callback_query.register(
        view_videos_handler,
        lambda c: c.data and c.data.startswith('all_video')
    )
    router.callback_query.register(
        add_video_handler,
        lambda c: c.data and c.data.startswith('add_video')
    )
    router.message.register(add_video_save, Command("add_video"))


    router.message.register(add_department_employee, Command("add_dep_emp"))
