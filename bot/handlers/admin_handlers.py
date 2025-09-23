from aiogram import Router, Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile
from database.db import (
    add_channel, add_video, get_videos, 
    add_dekanat_to_department, get_users, 
    get_channels, get_departments, get_employees, 
    add_department, add_employee, delete_channel, 
    edit_channel, edit_video, delete_video, edit_department, 
    delete_department, edit_employee, delete_employee)
from utils.auth import is_admin
import os
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(BASE_DIR, "images", "sunny.jpg")
router = Router()  # Router yaratish

from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
TOKEN = "7577757347:AAHcnJTtIidThEN6GbnRZEFiieeKFWyThMk"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

ADMIN_ID = 2004004762
WEATHER_API_KEY = "e4016445b7fb35f0746afcc49c41a0ef"
CITY = "Samarqand"
API_URL = "https://student.samtuit.uz/rest/v1/data/employee-list?type=all"
API_TOKEN = "Y-R36P1BY-eLfuCwQbcbAlvt9GAMk-WP"

WEATHER_API_KEY_ONE = "65484c016bd4407dbff62042251009" 

async def admin_start(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await message.delete()
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
    buttons.append(
        [types.InlineKeyboardButton(text="🚮 O'chirish", callback_data="delete_channel"),
        types.InlineKeyboardButton(text="🔤 Taxrirlash", callback_data="edit_channel")])
    buttons.append(
        [types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="back_admin"), 
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
        f"Yangi kanal qo'shish uchun format:\n`/add_channel Yangi_nomi, Yangi_link`\n\n"
        f"Masalan:\n`add_channel YangiNom, https://newlink.com`",
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
            await message.reply(
                f"❌ Yangi kanal qo'shish uchun format:\n`/add_channel Yangi_nomi, Yangi_link`\n\n"
                f"Masalan:\n`add_channel YangiNom, https://newlink.com`", parse_mode="Markdown")
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
            f"❌ Yangi kanal qo'shish uchun format:\n`/add_channel Yangi_nomi, Yangi_link`\n\n"
            f"Masalan:\n`add_channel YangiNom, https://newlink.com`",
            parse_mode="Markdown")

async def delete_channel_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):  # Admin tekshiruvi
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    channels = await get_channels()
    if not channels:
        await callback.message.answer("❌ Hech qanday kanal mavjud emas")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"❌ {name}", callback_data=f"delete_{name}")]
        for name, link in channels
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_channels")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("O‘chiriladigan kanalni tanlang:", reply_markup=keyboard)
    await callback.message.delete()

async def confirm_delete_channel(callback: types.CallbackQuery):
    channel_name = callback.data.split("_", 1)[1]
    await delete_channel(channel_name)
    button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_channels")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer(f"✅ {channel_name} kanali o‘chirildi!", reply_markup=keyboard)

async def edit_channel_handler(callback: types.CallbackQuery):
    channels = await get_channels()
    if not channels:
        await callback.message.answer("❌ Hech qanday kanal mavjud emas")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"✏️ {name}", callback_data=f"edit_{name}")]
        for name, link in channels
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_channels")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Tahrir qilinadigan kanalni tanlang:", reply_markup=keyboard)
    await callback.message.delete()

async def prompt_edit_channel(callback: types.CallbackQuery):
    channel_name = callback.data.split("_", 1)[1]
    buttons = [
        [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
        types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_channels")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(
        f"Tahrirlash uchun format:\n`/edit_channel {channel_name}, Yangi_nomi, Yangi_link`\n\n"
        f"Masalan:\n`/edit_channel {channel_name}, YangiNom, https://newlink.com`",
        parse_mode="Markdown", reply_markup=keyboard
    )
    await callback.answer() 

async def confirm_edit_channel(message: types.Message, command: CommandObject):
    try:
        data = command.args.split(",")
        if len(data) < 3:
            await message.reply("❌ Format: `/edit_channel Old_nomi, Yangi_nomi, Yangi_link`")
            return

        old_name = data[0].strip()
        new_name = data[1].strip()
        new_link = data[2].strip()

        await edit_channel(old_name, new_name, new_link)
        buttons = [
            [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
            types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_channels")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(f"✅ Kanal yangilandi:\nEski nomi: {old_name}\nYangi nomi: {new_name}\nYangi link: {new_link}", reply_markup=keyboard)
    except ValueError:
        await message.reply("❌ Xato! Formatni tekshirib qaytadan urinib ko‘ring.")

async def department_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    departments = await get_departments()
    if not departments:
        button = [[
            types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin"),
            types.InlineKeyboardButton(text=f"➕ Bo'lim q'shish", callback_data="add_department")
            ]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.answer(text="❌ Hech qanday bo'lim mavjud emas", reply_markup=keyboard)
        await callback.message.delete()
        return
    buttons = [
        [types.InlineKeyboardButton(text=f"♻️ {department_name}", callback_data=f"department_{department_id}")]
        for department_id, department_name, _ in departments
    ]
    buttons.append(
        [types.InlineKeyboardButton(text="🚮 O'chirish", callback_data="deletedepart_department"),
        types.InlineKeyboardButton(text="🔤 Taxrirlash", callback_data="editdepart_department")])
    buttons.append(
        [types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="back_admin"), types.InlineKeyboardButton(text=f"➕ Bo'lim q'shish", callback_data="add_department")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Barcha bo'limlar", reply_markup=keyboard)
    await callback.message.delete()

async def add_department_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):  # Admin tekshiruvi
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return
    button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer(
        "Bo'lim nomi va bo'lim rasmini quyidagi formatda yuboring:\n"
        "Rasm yuklang, rasmga na'muna kabi izoh qoldiring:\n"
        "Na'muna: `/add_depart Bo'lim_nomi`",
        parse_mode="Markdown", reply_markup=keyboard
    )

async def add_department_save(message: types.Message,  command: CommandObject, bot: Bot):
    if not is_admin(message.from_user.id):  # Admin tekshiruvi
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await message.delete()
        return
    department_name = command.args
    if not message.photo:  # Rasm yuborilganligini tekshirish
        await message.reply("❌ Iltimos, rasm yuboring!")
        return
    photo_id = message.photo[-1].file_id
    try:
        await add_department(department_name, photo_id)
        button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await message.reply("✅ Muvafaqiyatli qo'shildi!", reply_markup=keyboard)
    except Exception as e:
        await message.reply(f"❌ Xatolik: {e}")

async def delete_department_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):  # Admin tekshiruvi
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    departments = await get_departments()
    if not departments:
        await callback.message.answer("❌ Hech qanday bo'lim mavjud emas")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"❌ {department_name}", callback_data=f"deletedepart_{department_name}")]
        for department_id, department_name, photo_id in departments
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("O‘chiriladigan bo'limni tanlang:", reply_markup=keyboard)
    await callback.message.delete()

async def confirm_delete_department(callback: types.CallbackQuery):
    department_name = callback.data.split("_", 1)[1]
    await delete_department(department_name)
    button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer(f"✅ {department_name} bo'limi o‘chirildi!", reply_markup=keyboard)

async def edit_department_handler(callback: types.CallbackQuery):
    departments = await get_departments()
    if not departments:
        await callback.message.answer("❌ Hech qanday bo'lim mavjud emas")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"✏️ {department_name}", callback_data=f"editdepart_{department_name}")]
        for department_id, department_name, photo_id in departments
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Tahrir qilinadigan bo'limni tanlang:", reply_markup=keyboard)
    await callback.message.delete()

async def prompt_edit_department(callback: types.CallbackQuery):
    department_name = callback.data.split("_", 1)[1]
    buttons = [
        [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
        types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(
        f"Tahrirlash uchun rasm yuklang, rasm yuklashda izoh qoldiring\n"
        f"Format:\n`/edit_department {department_name}, Yangi_nomi`\n\n"
        f"Masalan:\n`/edit_department {department_name}, YangiNom`",
        parse_mode="Markdown", reply_markup=keyboard
    )

    await callback.answer() 

async def confirm_edit_department(message: types.Message, command: CommandObject):
    try:
        data = command.args.split(",")
        if len(data) < 2:
            await message.reply("❌ Format: `/edit_department Old_nomi, Yangi_nomi`", parse_mode="Markdown")
            return

        old_name = data[0].strip()
        new_name = data[1].strip()
        photo_id = message.photo[-1].file_id

        await edit_department(old_name, new_name, photo_id)
        buttons = [
            [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
            types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(f"✅ Bo'lim yangilandi:\nEski nomi: {old_name}\nYangi nomi: {new_name}\nYangi rasm id: {photo_id}", reply_markup=keyboard)
    except ValueError:
        await message.reply("❌ Xato! Formatni tekshirib qaytadan urinib ko‘ring.")

async def employee_all(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    employees = await get_employees()
    if not employees:
        button = [[
            types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin"),
            types.InlineKeyboardButton(text=f"➕ Xodim/o'qituvchi q'shish", callback_data="add_employee")
            ]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.answer(text="❌ Hech qanday xodim mavjud emas", reply_markup=keyboard)
        await callback.message.delete()
        return
    buttons = [
        [types.InlineKeyboardButton(text=f"👤 {employee_name} \n 👍({likes}), 👎({dislikes})", callback_data=f"employe_{employee_id}")]
        for employee_id, employee_name, likes, dislikes, _ in employees
    ]
    buttons.append(
        [types.InlineKeyboardButton(text="🚮 O'chirish", callback_data="deleteemplye_employee"),
        types.InlineKeyboardButton(text="🔤 Taxrirlash", callback_data="editemplye_employee")])
    buttons.append(
        [types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin"), types.InlineKeyboardButton(text=f"➕ Xodim/o'qituvchi q'shish", callback_data="add_employee")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Barcha xodimlar/o'qituvchilar", reply_markup=keyboard)
    await callback.message.delete()

async def add_employee_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):  # Admin tekshiruvi
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return
    department = await get_departments()
    text = [f"{dep_name}-{dep_id}" for dep_id, dep_name, _ in department]
    button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_employee")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer(
        "Xodim nomi va bo'lim idsini quyidagi formatda yuboring:\n"
        f"Bolimlar ro'yxati: {text}\n"
        "Na'muna: `/add_empl employee_nomi, 1`",
        parse_mode="Markdown", reply_markup=keyboard
    )

async def add_employee_save(message: types.Message,  command: CommandObject, bot: Bot):
    if not is_admin(message.from_user.id):  # Admin tekshiruvi
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await message.delete()
        return
    data = command.args.split(',')
    employee_name = data[0].strip()
    depart_id = data[1].strip()
    try:
        await add_employee(employee_name, int(depart_id))
        button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_employee")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await message.reply("✅ Muvafaqiyatli qo'shildi!", reply_markup=keyboard)
    except Exception as e:
        await message.reply(f"❌ Xatolik: {e}")

async def delete_employee_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):  # Admin tekshiruvi
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    employees = await get_employees()
    if not employees:
        await callback.message.answer("❌ Hech qanday bo'lim mavjud emas")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"❌ {employee_name}", callback_data=f"deleteemplye_{employee_name}")]
        for employee_id, employee_name, _, _, department_id in employees
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_employee")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("O‘chiriladigan bo'limni tanlang:", reply_markup=keyboard)
    await callback.message.delete()

async def confirm_delete_employee(callback: types.CallbackQuery):
    employee_name = callback.data.split("_", 1)[1]
    await delete_employee(employee_name)
    button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_employee")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer(f"✅ {employee_name} bo'limi o‘chirildi!", reply_markup=keyboard)

async def edit_employee_handler(callback: types.CallbackQuery):
    employees = await get_employees()
    if not employees:
        await callback.message.answer("❌ Hech qanday bo'lim mavjud emas")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"✏️ {employee_name}", callback_data=f"editemplye_{employee_name}")]
        for employee_id, employee_name, _, _, department_id in employees
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_employee")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(f"Tahrir qilinadigan bo'limni tanlang:", reply_markup=keyboard)
    await callback.message.delete()

async def prompt_edit_employee(callback: types.CallbackQuery):
    employee_name = callback.data.split("_", 1)[1]
    buttons = [
        [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
        types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_employee")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    department = await get_departments()
    text = [f"{dep_name}-{dep_id}" for dep_id, dep_name, _ in department]
    await callback.message.answer(
        f"Tahrirlash uchun. Format:\n`/edit_employee {employee_name}, Yangi_nomi, Bo'lim_id`\n\n"
        f"Masalan:\n`/edit_employee {employee_name}, YangiNom, Bo'limID`\n\n"
        f"Bolimlar: `{text}`",
        parse_mode="Markdown", reply_markup=keyboard
    )

    await callback.answer() 

async def confirm_edit_employee(message: types.Message, command: CommandObject):
    try:
        data = command.args.split(",")
        if len(data) < 3:
            await message.reply("❌ Format: `/edit_employee Old_nomi, Yangi_nomi, Bo'lim_id`", parse_mode="Markdown")
            return

        old_name = data[0].strip()
        new_name = data[1].strip()
        department_id = data[2].strip()

        await edit_employee(old_name, new_name, int(department_id))
        buttons = [
            [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
            types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_employee")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(f"✅ Bo'lim yangilandi:\nEski nomi: {old_name}\nYangi nomi: {new_name}\nYangi bo'lim id: {department_id}", reply_markup=keyboard)
    except ValueError:
        await message.reply("❌ Xato! Formatni tekshirib qaytadan urinib ko‘ring.")

async def video_all(callback: types.CallbackQuery):
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
        [types.InlineKeyboardButton(text="🚮 O'chirish", callback_data="deletevideo_video"),
        types.InlineKeyboardButton(text="🔤 Taxrirlash", callback_data="editvideo_video")])
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

async def delete_video_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):  # Admin tekshiruvi
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    videos = await get_videos()
    if not videos:
        await callback.message.answer("❌ Hech qanday video mavjud emas")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"❌ {name}", callback_data=f"deletevideo_{name}")]
        for _, _, name, _, _, in videos
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_video")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("O‘chiriladigan Talabani tanlang:", reply_markup=keyboard)
    await callback.message.delete()

async def confirm_delete_video(callback: types.CallbackQuery):
    video_name = callback.data.split("_", 1)[1]
    await delete_video(video_name)
    button = [[types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_video")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
    await callback.message.answer(f"✅ {video_name} videosi o‘chirildi!", reply_markup=keyboard)

async def edit_video_handler(callback: types.CallbackQuery):
    videos = await get_videos()
    if not videos:
        await callback.message.answer("❌ Hech qanday bo'lim mavjud emas")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"✏️ {name}", callback_data=f"editvideo_{name}")]
        for _, _, name, _, _, in videos
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_video")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(f"Tahrir qilinadigan Talabani tanlang:", reply_markup=keyboard)
    await callback.message.delete()

async def prompt_edit_video(callback: types.CallbackQuery):
    video_name = callback.data.split("_", 1)[1]
    buttons = [
        [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
        types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_video")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    department = await get_departments()
    text = [f"{dep_name}-{dep_id}" for dep_id, dep_name, _ in department]
    await callback.message.answer(
        f"Tahrirlash uchun video yuklang, video yuklashda izoh qoldiring\n"
        f"Format:\n`/edit_video {video_name}, Yangi_nomi`\n\n"
        f"Masalan:\n`/edit_video {video_name}, YangiNom`\n\n"
        f"Bolimlar: `{text}`",
        parse_mode="Markdown", reply_markup=keyboard
    )

    await callback.answer() 

async def confirm_edit_video(message: types.Message, command: CommandObject):
    try:
        data = command.args.split(",")
        if len(data) < 3:
            await message.reply("❌ Format: `/edit_video Old_nomi, Yangi_nomi`", parse_mode="Markdown")
            return

        old_name = data[0].strip()
        new_name = data[1].strip()
        file_id = message.video.file_id

        await edit_video(old_name, new_name, file_id)
        buttons = [
            [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
            types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_video")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(f"✅ Video yangilandi:\nEski nomi: {old_name}\nYangi nomi: {new_name}\nYangi Video id: {file_id}", reply_markup=keyboard)
    except ValueError:
        await message.reply("❌ Xato! Formatni tekshirib qaytadan urinib ko‘ring.")

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



def fetch_employees():
    all_employees = []

    for i in range(1, 23):  # 22 ta sahifa bor
        API_URL = f"https://student.samtuit.uz/rest/v1/data/employee-list?type=all&page={i}"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        res = requests.get(API_URL, headers=headers).json()
        data = res.get("data", {})

        if isinstance(data, dict):
            items = data.get("items", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        all_employees.extend(items)
    return all_employees




def get_daily_average_weatherapi(city="Samarqand"):
    url = "http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": WEATHER_API_KEY_ONE,
        "q": city,
        "days": 1,
        "aqi": "no",
        "alerts": "no"
    }
    resp = requests.get(url, params=params, timeout=10).json()

    location = resp["location"]["name"]
    country = resp["location"]["country"]
    forecast = resp["forecast"]["forecastday"][0]["day"]

    avg_temp = forecast["avgtemp_c"]
    max_temp = forecast["maxtemp_c"]
    min_temp = forecast["mintemp_c"]
    condition = forecast["condition"]["text"]
    humidity = forecast["avghumidity"]

    # Inglizcha → O‘zbekcha tarjima
    condition_translations = {
        "Sunny": "Quyoshli",
        "Clear": "Ochiq osmon",
        "Partly cloudy": "Qisman bulutli",
        "Cloudy": "Bulutli",
        "Overcast": "Qorong‘u osmon",
        "Mist": "Tumanli",
        "Fog": "Tuman",
        "Rain": "Yomg‘ir",
        "Light rain": "Yengil yomg‘ir",
        "Moderate rain": "O‘rtacha yomg‘ir",
        "Heavy rain": "Kuchli yomg‘ir",
        "Snow": "Qor",
        "Light snow": "Yengil qor",
        "Heavy snow": "Kuchli qor",
        "Thunderstorm": "Momaqaldiroq",
        "Drizzle": "Mayda yomg‘ir"
    }

    condition_uz = condition_translations.get(condition, condition)

    # Ob-havo rasmlari mapping
    weather_images = {
        "Sunny": "https://storage.kun.uz/source/4/DPWlLu11G2SPAPOSmw9FCWO687nVy6NL.jpg",
        "Clear": "https://storage.kun.uz/source/4/DPWlLu11G2SPAPOSmw9FCWO687nVy6NL.jpg",
        "Partly cloudy": "https://files.modern.az/articles/2025/03/30/1743323387_ebd5d6e7-475f-3fd9-9260-783bf53486ea_850.jpg",
        "Cloudy": "https://files.modern.az/articles/2025/03/30/1743323387_ebd5d6e7-475f-3fd9-9260-783bf53486ea_850.jpg",
        "Overcast": "https://files.modern.az/articles/2025/03/30/1743323387_ebd5d6e7-475f-3fd9-9260-783bf53486ea_850.jpg",
        "Rain": "https://i.ytimg.com/vi/7brJCPOkfuQ/maxresdefault.jpg",
        "Light rain": "https://i.ytimg.com/vi/7brJCPOkfuQ/maxresdefault.jpg",
        "Moderate rain": "https://i.ytimg.com/vi/7brJCPOkfuQ/maxresdefault.jpg",
        "Snow": "https://pic.rutubelist.ru/video/2024-12-21/64/41/6441c162f6f67d0bb3a69ab136527cc0.jpg",
        "Thunderstorm": "https://www.wwlp.com/wp-content/uploads/sites/26/2025/06/Getty-Thunderstorm.jpg?w=1280",
    }

    # Agar condition mappingda bo‘lmasa → default rasm
    image_url = weather_images.get(condition, "https://files.modern.az/articles/2025/03/30/1743323387_ebd5d6e7-475f-3fd9-9260-783bf53486ea_850.jpg")

    # Chiroyli caption (uzbekcha holat bilan)
    caption = (
        "<b>OB➖HOVO</b>\n\n"
        "🌐 <b>TATU Samarqand filiali axborot xizmati</b>\n\n"
        f"📍 <b>{location}, {country}</b>\n"
        f"📅 <i>{datetime.now().strftime('%d-%m-%Y')}</i>\n\n"
        f"🌡️ <b>O'rtacha: {avg_temp}°C</b>\n"
        f"⬆️ Maks: {max_temp}°C   ⬇️ Min: {min_temp}°C\n"
        f"☁️ Holat: <b>{condition_uz}</b>\n"
        f"💧 Namlik: {humidity}%\n\n"
        "Bizni kuzating👇\n"
        "<a href='https://fb.com/sbtuit'>Facebook</a> | "
        "<a href='https://t.me/sbtuit2005'>Telegram</a> | "
        "<a href='https://instagram.com/sbtuit2005'>Instagram</a> | "
        "<a href='https://bit.ly/2yw9MS9'>YouTube</a>\n"
    )

    return caption, image_url



# 🎂 Tug‘ilgan kunlarni tekshirish (bugun va ertaga)
def get_birthdays():
    employees = fetch_employees()
    today = datetime.now().strftime("%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m-%d")

    birthdays_today, birthdays_tomorrow = [], []

    for emp in employees:
        try:
            # Tug‘ilgan sanani timestampdan datetime ga aylantiramiz
            timestamp = emp["birth_date"]
            if timestamp > 1e12:
                timestamp = timestamp/1000

            birth_date = datetime.fromtimestamp(timestamp)
            birth_md = birth_date.strftime("%m-%d")  # faqat oy-kun

            info = {
                    "full_name": emp["full_name"],
                    "department": emp["department"]["name"] if emp.get("department") else "",
                    "kafedra": emp["structureType"]["name"] if emp.get("kafedra") else "",
                    "birth_date": birth_date.strftime("%Y-%m-%d"),  # to‘liq sana
                    "image": emp.get("image")
            }

            if birth_md == today:
                birthdays_today.append(info)
            elif birth_md == tomorrow:
                birthdays_tomorrow.append(info)

        except Exception as e:
            pass

    return birthdays_today, birthdays_tomorrow

# 📤 Adminni tug‘ilgan kunlar bilan ogohlantirish
async def send_birthday_notifications():
    birthdays_today, birthdays_tomorrow = get_birthdays()
    
    if birthdays_today:
        for emp in birthdays_today:
            full_name = emp["full_name"]
            department = emp["department"]
            kafedra = emp["kafedra"]

            caption = f"""
            Bugun"{department}" {kafedra} xodimi <i>{full_name}</i>ning tavallud ayyomi.\n\n <i>Hurmatli {full_name}</i>\nSizga filial jamoasi nomidan sihat-salomatlik, oilaviy xotirjamlik, ishlaringizda ulkan muvaffaqiyatlar tilab qolamiz!\n\n🌐 <b>TATU Samarqand filiali axborot xizmati</b>\n\n\nBizni kuzating👇🏼\n <a href="https://fb.com/sbtuit">Facebook</a> | <a href="https://t.me/sbtuit2005">Telegram</a> | <a href="https://instagram.com/sbtuit2005">Instagram</a> | <a href="https://bit.ly/2yw9MS9">YouTube</a>"""

            if emp.get("image"):
                await bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=emp["image"],  # URL bo‘lsa to‘g‘ridan-to‘g‘ri
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=caption,
                    parse_mode="HTML"
                )

    if birthdays_tomorrow:
        msg = "📌 <b>Ertaga tug‘ilgan kunlar:</b>\n\n"
        for emp in birthdays_tomorrow:
            msg += f"👤 {emp['full_name']}\n🏢 {emp['department']}\n\n"
        await bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="HTML")

    if not birthdays_today and not birthdays_tomorrow:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text="❌ Bugun va ertaga tug‘ilgan kun yo‘q.",
            parse_mode="HTML"
        )

async def obhavo_command_telegram():
    caption, image_url = get_daily_average_weatherapi("Samarqand")
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=image_url,   # ob-havoga mos rasm
        caption=caption,
        parse_mode="HTML"
    )


@router.message(F.text == "/obhavo_api")
async def obhavo_command(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return
    caption, image_url = get_daily_average_weatherapi("Samarqand")
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=image_url,   # ob-havoga mos rasm
        caption=caption,
        parse_mode="HTML"
    )

# === /test komandasi ===
@router.message(F.text == "/test")
async def test_command(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return
    if str(message.from_user.id) != str(ADMIN_ID):
        return await message.answer("⛔ Bu buyruq faqat admin uchun!")

    await message.answer("⏳ Test boshlanmoqda...")
    await send_birthday_notifications()
    await message.answer("✅ Test tugadi, kanal va admin xabarlarni oldi.")

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
    delete_channel_handler,
    lambda c: c.data and c.data.startswith("delete_channel")
    )
    router.callback_query.register(
        confirm_delete_channel,
        lambda c: c.data and c.data.startswith("delete_")
    )
    router.callback_query.register(
        edit_channel_handler,
        lambda c: c.data and c.data.startswith("edit_channel")
    )
    router.callback_query.register(
        prompt_edit_channel,
        lambda c: c.data and c.data.startswith("edit_")
    )
    router.message.register(confirm_edit_channel, Command("edit_channel"))

    #department
    router.callback_query.register(
    delete_department_handler,
    lambda c: c.data and c.data.startswith("deletedepart_department")
    )
    router.callback_query.register(
        confirm_delete_department,
        lambda c: c.data and c.data.startswith("deletedepart_")
    )
    router.callback_query.register(
        edit_department_handler,
        lambda c: c.data and c.data.startswith("editdepart_department")
    )
    router.callback_query.register(
        prompt_edit_department,
        lambda c: c.data and c.data.startswith("editdepart_")
    )
    router.message.register(confirm_edit_department, Command("edit_department"))


    router.callback_query.register(
        department_all,
        lambda c: c.data and c.data.startswith("all_department")  # all users views
    )
    router.callback_query.register(
        add_department_handler,
        lambda c: c.data and c.data.startswith("add_department")
    )
    router.message.register(add_department_save, Command("add_depart"))


    router.callback_query.register(
        employee_all,
        lambda c: c.data and c.data.startswith("all_employee")  # all users views
    )
    router.callback_query.register(
        add_employee_handler,
        lambda c: c.data and c.data.startswith("add_employee")
    )
    router.message.register(add_employee_save, Command("add_empl"))
    #employee
    router.callback_query.register(
    delete_employee_handler,
    lambda c: c.data and c.data.startswith("deleteemplye_employee")
    )
    router.callback_query.register(
        confirm_delete_employee,
        lambda c: c.data and c.data.startswith("deleteemplye_")
    )
    router.callback_query.register(
        edit_employee_handler,
        lambda c: c.data and c.data.startswith("editemplye_employee")
    )
    router.callback_query.register(
        prompt_edit_employee,
        lambda c: c.data and c.data.startswith("editemplye_")
    )
    router.message.register(confirm_edit_employee, Command("edite_employee"))



    router.callback_query.register(
        video_all,
        lambda c: c.data and c.data.startswith('all_video')
    )
    router.callback_query.register(
        add_video_handler,
        lambda c: c.data and c.data.startswith('add_video')
    )
    router.message.register(add_video_save, Command("add_video"))

    #video
    router.callback_query.register(
    delete_video_handler,
    lambda c: c.data and c.data.startswith("deletevideo_video")
    )
    router.callback_query.register(
        confirm_delete_video,
        lambda c: c.data and c.data.startswith("deletevideo_")
    )
    router.callback_query.register(
        edit_video_handler,
        lambda c: c.data and c.data.startswith("editvideo_video")
    )
    router.callback_query.register(
        prompt_edit_video,
        lambda c: c.data and c.data.startswith("editvideo_")
    )
    router.message.register(confirm_edit_video, Command("edit_video"))


    router.message.register(add_department_employee, Command("add_dep_emp"))
