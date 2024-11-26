from aiogram import types, Router, Dispatcher, Bot
from aiogram.filters import Command
from database.db import get_channels, get_videos, like_video
from utils.membership import check_membership

router = Router()  # Router yaratish

# /start komanda handleri
async def start_handler(message: types.Message):
    # Kanallarni bazadan olish
    channels = await get_channels()
    if not channels:  # Hech qanday kanal mavjud bo'lmasa
        await message.answer("❌ Hozircha qo'shiladigan kanallar mavjud emas.")
        return

    # Tugmalarni yaratish
    buttons = [types.InlineKeyboardButton(text=name, url=link) for name, link in channels]
    buttons.append(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_membership"))

    # Klaviatura yaratish
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.answer("Quyidagi kanallarga a'zo bo'ling va \"Tekshirish\" tugmasini bosing:", reply_markup=keyboard)

# Tekshiruv tugmasi uchun handler
async def check_membership_handler(callback: types.CallbackQuery, bot: Bot):
    channels = await get_channels()
    user_id = callback.from_user.id

    # Foydalanuvchi barcha kanallarga a'zo ekanligini tekshirish
    is_member = all(
        [await check_membership(bot, link.split("/")[-1], user_id) for _, link in channels]
    )

    if is_member:
        await callback.message.answer("✅ A'zo bo'ldingiz! Endi videolarni ko'rishingiz mumkin.")

        # Videolarni bazadan olish va foydalanuvchiga yuborish
        videos = await get_videos()
        for video_id, file_id, likes, dislikes in videos:
            buttons = [
                types.InlineKeyboardButton(text=f"👍 {likes}", callback_data=f"like_{video_id}"),
                types.InlineKeyboardButton(text=f"👎 {dislikes}", callback_data=f"dislike_{video_id}")
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons])
            await callback.message.answer_video(video=file_id, reply_markup=keyboard)
    else:
        await callback.message.answer("❌ Hali kanallarga a'zo bo'lmadingiz!")

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
        check_membership_handler,
        lambda c: c.data == "check_membership"  # Tekshirish tugmasi uchun filter
    )
    router.callback_query.register(
        handle_likes,
        lambda c: c.data and (c.data.startswith("like_") or c.data.startswith("dislike_"))  # Like/dislike tugmalari
    )
