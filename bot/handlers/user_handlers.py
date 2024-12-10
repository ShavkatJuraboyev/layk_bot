from aiogram import types, Router, Dispatcher, Bot
from aiogram.filters import Command
from database.db import get_channels, get_videos, like_video, get_departments, get_employees_by_department, like_employee, get_employees
from utils.membership import check_membership

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

    if is_member:
        await message.answer("👋 Assalomu alaykum ovoz berish botiga xush kelibsiz.")
        departments = await get_departments()

        if not departments:  # Videolar mavjud bo'lmasa
            await message.answer("❌ Hozircha bo'limlar mavjud emas.")
            return

        # Inline tugmalar orqali deparmentlarni ro'yxatini ko'rsatish
        buttons = [
            types.InlineKeyboardButton(text=department_name, callback_data=f"department_{department_id}")
            for department_id, department_name in departments
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.answer("Quyidagi bo'limlardan birini tanlang:", reply_markup=keyboard)
    else:
        # Agar foydalanuvchi hali kanallarga a'zo bo'lmagan bo'lsa
        buttons = [types.InlineKeyboardButton(text=name, url=link) for name, link in channels]
        buttons.append(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_membership"))
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.answer("❌ Avval quyidagi kanallarga a'zo bo'ling va \"Tekshirish\" tugmasini bosing:", reply_markup=keyboard)

async def employee_like(callback: types.CallbackQuery):
    if not callback.data:  # Callback ma'lumotlari mavjudligini tekshirish
        await callback.answer("❌ Xato: noto'g'ri ma'lumot kiritildi!")
        return
    
    # Callback ma'lumotlarini ajratish
    data = callback.data.split("_")
    department_id = int(data[1])

    employees = await get_employees_by_department(department_id)

    if not employees:  # Videolar mavjud bo'lmasa
        await message.answer("❌ Hozircha bo'limlar mavjud emas.")
        return

        # Inline tugmalar orqali deparmentlarni ro'yxatini ko'rsatish
    buttons = [
        types.InlineKeyboardButton(text=employee_name, callback_data=f"employee_{employee_id}")
        for employee_id, employee_name, _, _, _ in employees
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
    await callback.message.answer("Quyidagilardan birini tanlang:", reply_markup=keyboard)

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

    _, employee_name, likes, dislikes, _ = employee
    buttons = [
        types.InlineKeyboardButton(text=f"👍 {likes}", callback_data=f"like_{employee_id}"),
        types.InlineKeyboardButton(text=f"👎 {dislikes}", callback_data=f"dislike_{employee_id}")
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
    await callback.message.answer(text=employee_name, reply_markup=keyboard)

# Like/dislike tugmalari uchun handler
async def employee_handle_likes(callback: types.CallbackQuery):
    if not callback.data:  # Callback ma'lumotlari mavjudligini tekshirish
        await callback.answer("❌ Xato: noto'g'ri ma'lumot kiritildi!")
        return

    # Callback ma'lumotlarini ajratish
    data = callback.data.split("_")
    employee_id = int(data[1])
    like = data[0] == "like"

    # Ovozni bazaga yozish
    success = await like_employee(callback.from_user.id, employee_id, like)
    if success:
        await callback.answer("✅ Ovozingiz qabul qilindi!")
    else:
        await callback.answer("❌ Siz avval ovoz bergansiz!")


async def like_videos(callback: types.CallbackQuery):
    videos = await get_videos()

    if not videos:  # Videolar mavjud bo'lmasa
        await message.answer("❌ Hozircha videolar mavjud emas.")
        return

    # Inline tugmalar orqali videolarni ro'yxatini ko'rsatish
    buttons = [
        types.InlineKeyboardButton(text=video_name, callback_data=f"video_{video_id}")
        for video_id, _, video_name, _, _ in videos
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.answer("Quyidagi videolardan birini tanlang:", reply_markup=keyboard)
    pass

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
        types.InlineKeyboardButton(text=f"👍 {likes}", callback_data=f"like_{video_id}"),
        types.InlineKeyboardButton(text=f"👎 {dislikes}", callback_data=f"dislike_{video_id}")
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
    like = data[0] == "like"

    # Ovozni bazaga yozish
    success = await like_video(callback.from_user.id, video_id, like)
    if success:
        await callback.answer("✅ Ovozingiz qabul qilindi!")
    else:
        await callback.answer("❌ Siz avval ovoz bergansiz!")

# Router yordamida handlerlarni ro'yxatga olish
def register_user_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(start_handler, Command("start"))  # /start komandasi uchun handler
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
        video_handler,
        lambda c: c.data and c.data.startswith("video_")  # Video tanlash uchun
    )
    router.callback_query.register(
        handle_likes,
        lambda c: c.data and (c.data.startswith("like_") or c.data.startswith("dislike_"))  # Like/dislike tugmalari
    )
