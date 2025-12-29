from aiogram import types, Router, Dispatcher, Bot
from aiogram.filters import Command
from database.db import get_channels, get_videos, like_video, get_departments, get_employees_by_department, like_employee, get_employees
from utils.membership import check_membership
from aiogram.types import InputFile, FSInputFile
import os
from utils.auth import is_admin

router = Router()  # Router yaratish


# /start komanda handleri
async def start_handler(message: types.Message, bot: Bot):
    # Kanallarni bazadan olish
    channels = await get_channels()
    # Foydalanuvchini barcha kanallarga tekshirish
    user_id = message.from_user.id
    is_member = all(
        [await check_membership(bot, link.split("/")[-1], user_id) for _, link in channels]
    )

    if not is_member:
        buttons = [[types.InlineKeyboardButton(text=name, url=link)] for name, link in channels]
        buttons.append([types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_memberships")])
        return await message.answer("Quyidagi kanallarga a'zo bo'ling va tekshiring 👇", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    
    if is_member:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Hozirgi faylning joylashuvi
        photo_path = os.path.join(base_dir, "rasm", "rasm6.jpg")
        if os.path.exists(photo_path):  # Fayl mavjudligini tekshirish
            departments = await get_departments()

            if not departments:  
                await message.answer("❌ Hozircha ovozberish mavjud emas.")
                return

            # Inline tugmalar orqali deparmentlarni ro'yxatini ko'rsatish
            buttons = [[
                types.InlineKeyboardButton(text=department_name, callback_data=f"department_{department_id}")]
                for department_id, department_name, _ in departments
            ]
            # buttons.append([types.InlineKeyboardButton(text="Talabalar", callback_data="video_like_student")])
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
            photo = FSInputFile(photo_path)
            await message.answer_photo(photo=photo, caption="""🏛TATU SAMARQAND FILIALIDA "ENG NAMUNALI GURUH SARDORI" TANLOVIGA START BERILDI.

🏆 1-bosqich - fakultet kesimida.
🏆 2-bosqich - filial kesimida.
                                       
‼️ Eslatma: Ushbu so'rovnomada xolis fikr bildirishingizni iltimos qilib qolamiz. Natijalar rasmiy sahifalarda e'lon qilinadi.

✅ Eng koʻp ovoz toʻplagan guruh sardori diplom hamda qimmatbaho sovg‘alar bilan taqdirlanadi!


✅ Saralash bosqichi 30-dekabr 12:00ga qadar Telekommunikatsiya texnologiyalari va kasb-ta'limi fakulteti guruh sardorlari o'rtasida davom etadi. 250 tadan ko'p ovoz to'plagan guruh sardori FINAL bosqichiga chiqadi.""", reply_markup=keyboard)
        else:
            await message.answer("👋 Assalomu alaykum ovoz berish botiga xush kelibsiz.")
            return
        
    else:
        # Agar foydalanuvchi hali kanallarga a'zo bo'lmagan bo'lsa
        buttons = [[
            types.InlineKeyboardButton(text=name, url=link)] 
            for name, link in channels
            ]
        buttons.append([types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_memberships")])
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("👋 Assalomu alaykum ovoz berish botiga xush kelibsiz.\nBotdan foydalanish uchun avval quyidagi kanallarga a'zo bo'ling va \"Tekshirish\" tugmasini bosing:", reply_markup=keyboard)

async def check_memberships(callback: types.CallbackQuery, bot: Bot):
    channels = await get_channels()
    # Foydalanuvchini barcha kanallarga tekshirish
    user_id = callback.message.chat.id
    is_member = all(
        [await check_membership(bot, link.split("/")[-1], user_id) for _, link in channels]
    )
    if is_member:
        await callback.message.answer("Tabriklayman! Siz barcha kanallarga a'zo bo'ldingiz")
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Hozirgi faylning joylashuvi
        photo_path = os.path.join(base_dir, "rasm", "rasm6.jpg")
        if os.path.exists(photo_path):  # Fayl mavjudligini tekshirish
            departments = await get_departments()

            if not departments:  
                await callback.message.answer("❌ Hozircha ovozberish mavjud emas.")
                return

            # Inline tugmalar orqali deparmentlarni ro'yxatini ko'rsatish
            buttons = [[
                types.InlineKeyboardButton(text=department_name, callback_data=f"department_{department_id}")]
                for department_id, department_name, _ in departments
            ]
            # buttons.append([types.InlineKeyboardButton(text="Talabalar", callback_data="video_like_student")])
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
            photo = FSInputFile(photo_path)
            await callback.message.answer_photo(photo=photo, caption="""🏛TATU SAMARQAND FILIALIDA "ENG NAMUNALI GURUH SARDORI" TANLOVIGA START BERILDI.

🏆 1-bosqich - fakultet kesimida.
🏆 2-bosqich - filial kesimida.
                                       
‼️ Eslatma: Ushbu so'rovnomada xolis fikr bildirishingizni iltimos qilib qolamiz. Natijalar rasmiy sahifalarda e'lon qilinadi.

✅ Eng koʻp ovoz toʻplagan guruh sardori diplom hamda qimmatbaho sovg‘alar bilan taqdirlanadi!


✅ Saralash bosqichi 30-dekabr 12:00ga qadar Telekommunikatsiya texnologiyalari va kasb-ta'limi fakulteti guruh sardorlari o'rtasida davom etadi. 250 tadan ko'p ovoz to'plagan guruh sardori FINAL bosqichiga chiqadi.""", reply_markup=keyboard)
        else:
            await callback.message.answer("👋 Assalomu alaykum ovoz berish botiga xush kelibsiz.")
            return
        await callback.message.delete()
    else:
        # Agar foydalanuvchi hali kanallarga a'zo bo'lmagan bo'lsa
        buttons = [[
            types.InlineKeyboardButton(text=name, url=link)]
             for name, link in channels
             ]
        buttons.append([types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_memberships")])
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer("❌ Avval quyidagi kanallarga a'zo bo'ling va \"Tekshirish\" tugmasini bosing:", reply_markup=keyboard)
        await callback.message.delete()


async def employee_like(callback: types.CallbackQuery, bot: Bot):
    department_id = int(callback.data.split("_")[1])
    departments = await get_departments()
    department = next((d for d in departments if d[0] == department_id), None)
    if not department:
        return await callback.answer("Bo‘lim topilmadi!")

    _, _, photo_id = department
    employees = await get_employees_by_department(department_id)

    bot_info = await bot.get_me()
    bot_username = bot_info.username

    buttons = []

    for emp_id, emp_name, likes, _, _ in employees:
        buttons.append([
            types.InlineKeyboardButton(
                text=f"👤 {emp_name} ({likes})",
                callback_data=f"employee_{emp_id}"
            )
        ])

    if is_admin(callback.message.chat.id):
        buttons.append([
            types.InlineKeyboardButton(
                text="📤 Kanalga yuborish",
                callback_data=f"forward_department_{department_id}"
            )
    ])
    buttons.append([types.InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_departments")])

    caption = (
        """🏛TATU SAMARQAND FILIALIDA "ENG NAMUNALI GURUH SARDORI" TANLOVIGA START BERILDI.

🏆 1-bosqich - fakultet kesimida.
🏆 2-bosqich - filial kesimida.
                                       
‼️ Eslatma: Ushbu so'rovnomada xolis fikr bildirishingizni iltimos qilib qolamiz. Natijalar rasmiy sahifalarda e'lon qilinadi.

✅ Eng koʻp ovoz toʻplagan guruh sardori diplom hamda qimmatbaho sovg‘alar bilan taqdirlanadi!


✅ Saralash bosqichi 30-dekabr 12:00ga qadar Telekommunikatsiya texnologiyalari va kasb-ta'limi fakulteti guruh sardorlari o'rtasida davom etadi. 250 tadan ko'p ovoz to'plagan guruh sardori FINAL bosqichiga chiqadi."""
    )

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer_photo(photo=photo_id, caption=caption, reply_markup=keyboard)
    await callback.message.delete()

@router.callback_query(lambda c: c.data and c.data.startswith("forward_department_"))
async def forward_view(callback: types.CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Bu tugma faqat adminlar uchun!")
    
    department_id = int(callback.data.split("_")[-1])
    departments = await get_departments()
    department = next((d for d in departments if d[0] == department_id), None)
    if not department:
        return await callback.answer("Bo‘lim topilmadi!")

    _, _, photo_id = department
    employees = await get_employees_by_department(department_id)
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    bot_info = await bot.get_me()
    bot_username = bot_info.username

    buttons = []

    for emp_id, emp_name, like, _, _ in employees:
        url = f"https://t.me/{bot_username}?start=emp_{emp_id}"
        buttons.append([
            types.InlineKeyboardButton(text=f"👤 {emp_name}", url=url)
        ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    caption = (
        """🏛TATU SAMARQAND FILIALIDA "ENG NAMUNALI GURUH SARDORI" TANLOVIGA START BERILDI.

🏆 1-bosqich - fakultet kesimida.
🏆 2-bosqich - filial kesimida.
                                       
‼️ Eslatma: Ushbu so'rovnomada xolis fikr bildirishingizni iltimos qilib qolamiz. Natijalar rasmiy sahifalarda e'lon qilinadi.

✅ Eng koʻp ovoz toʻplagan guruh sardori diplom hamda qimmatbaho sovg‘alar bilan taqdirlanadi!


✅ Saralash bosqichi 30-dekabr 12:00ga qadar Telekommunikatsiya texnologiyalari va kasb-ta'limi fakulteti guruh sardorlari o'rtasida davom etadi. 250 tadan ko'p ovoz to'plagan guruh sardori FINAL bosqichiga chiqadi."""
    )

    # 1. Kanalga yuborish
    try:
        await bot.send_photo(
            chat_id='@sbtuit2005',  # o'zingizning kanal username'ini yozing (belgisiz!)
            photo=photo_id,
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.answer(f"❌ Kanalga yuborib bo‘lmadi: {e}")
        return

    # 2. Adminning o‘ziga yuborish
    await bot.send_photo(
        chat_id=callback.from_user.id,
        photo=photo_id,
        caption=caption,
        reply_markup=keyboard
    )

    await callback.answer("✅ Xabar kanalga va sizga yuborildi.")
    await callback.answer("✅ Forward uchun xabar tayyor!")


async def employee_handler(callback: types.CallbackQuery):
    if not callback.data:  # Callback ma'lumotlari mavjudligini tekshirish
        await callback.answer("❌ Xato: noto'g'ri ma'lumot kiritildi!")
        return
    
    # Callback ma'lumotlarini ajratish
    data = callback.data.split("_")
    employee_id = int(data[1])
    employees = await get_employees()
    employee = next((v for v in employees if v[0] == employee_id), None)
    if not employee:  # Agar video topilmasa
        await callback.answer("❌ ma'lumot topilmadi!")
        return

    _, employee_name, likes, dislikes, department_id = employee
    buttons = [
        [types.InlineKeyboardButton(text=f"Ovoz berish", callback_data=f"like_{employee_id}")],
        [types.InlineKeyboardButton(text="🔙 Ortga qaytish", callback_data=f"department_{department_id}")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text=employee_name, reply_markup=keyboard)
    await callback.message.delete()

# Like/dislike tugmalari uchun handler
async def employee_handle_likes(callback: types.CallbackQuery):
    if not callback.data:
        await callback.answer("❌ Xato: noto'g'ri ma'lumot kiritildi!")
        return

    data = callback.data.split("_")
    employee_id = int(data[1])
    like = data[0] == "like"

    employees = await get_employees()
    employee = next((v for v in employees if v[0] == employee_id), None)

    if not employee:
        await callback.answer("❌ Ma'lumot topilmadi!")
        return

    id_, employee_name, likes, dislikes, department_id = employee

    # ❗ To'g'ri ID yuborish: employee_id, department_id emas
    success = await like_employee(callback.from_user.id, employee_id, like)

    if success:
        await callback.answer("✅ Ovozingiz qabul qilindi!")
        buttons = [
            types.InlineKeyboardButton(text="🔝 Bosh saxifaga qaytish", callback_data="back_to_departments")
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
        await callback.message.answer("✅ Ovozingiz qabul qilindi!", reply_markup=keyboard)
    else:
        await callback.answer("❌ Siz avval ovoz bergansiz!")
        button = [
            types.InlineKeyboardButton(text="🔝 Bosh saxifaga qaytish", callback_data="back_to_departments")
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[button])
        await callback.message.answer("❌ Siz avval ovoz bergansiz!", reply_markup=keyboard)

    await callback.message.delete()


async def back_to_departmenys(callback: types.CallbackQuery):
    departments = await get_departments()
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Hozirgi faylning joylashuvi
    photo_path = os.path.join(base_dir, "rasm", "rasm6.jpg")
    photo = FSInputFile(photo_path)

    buttons = [
        [types.InlineKeyboardButton(text=department_name, callback_data=f"department_{department_id}")]
        for department_id, department_name, _ in departments
    ]
    # buttons.append([types.InlineKeyboardButton(text="Talabalar", callback_data="video_like_student")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer_photo(photo=photo, caption="""🏛TATU SAMARQAND FILIALIDA "ENG NAMUNALI GURUH SARDORI" TANLOVIGA START BERILDI.

🏆 1-bosqich - fakultet kesimida.
🏆 2-bosqich - filial kesimida.
                                       
‼️ Eslatma: Ushbu so'rovnomada xolis fikr bildirishingizni iltimos qilib qolamiz. Natijalar rasmiy sahifalarda e'lon qilinadi.

✅ Eng koʻp ovoz toʻplagan guruh sardori diplom hamda qimmatbaho sovg‘alar bilan taqdirlanadi!


✅ Saralash bosqichi 30-dekabr 12:00ga qadar Telekommunikatsiya texnologiyalari va kasb-ta'limi fakulteti guruh sardorlari o'rtasida davom etadi. 250 tadan ko'p ovoz to'plagan guruh sardori FINAL bosqichiga chiqadi.""", reply_markup=keyboard)
    await callback.message.delete()

async def like_videos(callback: types.CallbackQuery):
    videos = await get_videos()

    if not videos:  # Videolar mavjud bo'lmasa
        await callback.message.answer("❌ Hozircha videolar mavjud emas.")
        return

    # Inline tugmalar orqali videolarni ro'yxatini ko'rsatish
    buttons = [[
        types.InlineKeyboardButton(text=video_name, callback_data=f"video_{video_id}")]
        for video_id, _, video_name, _, _ in videos
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Quyidagi videolardan birini tanlang:", reply_markup=keyboard)
    await callback.message.delete()

# Video tugmasi uchun handler
async def video_handler(callback: types.CallbackQuery):
    if not callback.data:  # Callback ma'lumotlari mavjudligini tekshirish
        await callback.answer("❌ Xato: noto'g'ri ma'lumot kiritildi!")
        return

    # Callback ma'lumotlarini ajratish
    data = callback.data.split("_")
    video_id = int(data[1])

    # Videoni bazadan olish
    videos = await get_videos()
    video = next((v for v in videos if v[0] == video_id), None)

    if not video:  # Agar video topilmasa
        await callback.answer("❌ Video topilmadi!")
        return

    _, file_id, name, likes, dislikes = video
    buttons = [
        types.InlineKeyboardButton(text=f"👍 {likes}", callback_data=f"likes_{video_id}"),
        types.InlineKeyboardButton(text=f"👎 {dislikes}", callback_data=f"dislikes_{video_id}")
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
    await callback.message.answer_video(video=file_id, caption=name, reply_markup=keyboard)

# Like/dislike tugmalari uchun handler
async def handle_likes(callback: types.CallbackQuery):
    if not callback.data:  # Callback ma'lumotlari mavjudligini tekshirish
        await callback.answer("❌ Xato: noto'g'ri ma'lumot kiritildi!")
        return

    # Callback ma'lumotlarini ajratish
    data = callback.data.split("_")
    video_id = int(data[1])
    like = data[0] == "likes"

    # Ovozni bazaga yozish
    success = await like_video(callback.from_user.id, video_id, like)
    if success:
        await callback.answer("✅ Ovozingiz qabul qilindi!")
    else:
        await callback.answer("❌ Siz avval ovoz bergansiz!")

    await callback.message.delete()

# Router yordamida handlerlarni ro'yxatga olish
def register_user_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(start_handler, Command("start"))  # /start komandasi uchun handler
    router.callback_query.register(check_memberships, lambda c: c.data and c.data.startswith('check_memberships'))
    router.callback_query.register(
        employee_like,
        lambda c: c.data and c.data.startswith("department_")  # Video tanlash uchun
    )
    router.callback_query.register(
        employee_handler,
        lambda c: c.data and c.data.startswith("employee_")  # Video tanlash uchun
    )
    router.callback_query.register(
        employee_handle_likes,
        lambda c: c.data and (c.data.startswith("like_") or c.data.startswith("dislike_"))  # Like/dislike tugmalari
    )
    router.callback_query.register(
        like_videos,
        lambda c: c.data and c.data.startswith("video_like_student")  # Video tanlash uchun
    )
    router.callback_query.register(
        video_handler,
        lambda c: c.data and c.data.startswith("video_")  # Video tanlash uchun
    )
    router.callback_query.register(
        handle_likes,
        lambda c: c.data and (c.data.startswith("likes_") or c.data.startswith("dislikes_"))  # Like/dislike tugmalari
    )
    router.callback_query.register(
        back_to_departmenys, 
        lambda c: c.data and c.data == "back_to_departments"
    )
