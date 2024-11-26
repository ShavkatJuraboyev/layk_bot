from aiogram import types
from aiogram import Router, Dispatcher
from aiogram.filters import Command
from database.db import get_channels, get_videos, like_video
from utils.membership import check_membership

router = Router()  # Router yaratish

async def start_handler(message: types.Message):
    channels = await get_channels()
    buttons = [types.InlineKeyboardButton(text=name, url=link) for name, link in channels]
    buttons.append(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_membership"))
    keyboard = types.InlineKeyboardMarkup(row_width=1).add(*buttons)
    await message.answer("Quyidagi kanallarga a'zo bo'ling va \"Tekshirish\" tugmasini bosing:", reply_markup=keyboard)

async def check_membership_handler(callback: types.CallbackQuery, bot):
    channels = await get_channels()
    user_id = callback.from_user.id
    is_member = all([await check_membership(bot, user_id, link.split("/")[-1]) for _, link in channels])

    if is_member:
        await callback.message.answer("✅ A'zo bo'ldingiz! Endi videolarni ko'rishingiz mumkin.")
        videos = await get_videos()
        for video_id, file_id, likes, dislikes in videos:
            buttons = [
                types.InlineKeyboardButton(text=f"👍 {likes}", callback_data=f"like_{video_id}"),
                types.InlineKeyboardButton(text=f"👎 {dislikes}", callback_data=f"dislike_{video_id}")
            ]
            keyboard = types.InlineKeyboardMarkup().add(*buttons)
            await callback.message.answer_video(video=file_id, reply_markup=keyboard)
    else:
        await callback.message.answer("❌ Hali kanallarga a'zo bo'lmadingiz!")

async def handle_likes(callback: types.CallbackQuery):
    data = callback.data.split("_")
    video_id = int(data[1])
    like = data[0] == "like"
    success = await like_video(callback.from_user.id, video_id, like)
    if success:
        await callback.answer("✅ Ovozingiz qabul qilindi!")
    else:
        await callback.answer("❌ Siz avval ovoz bergansiz!")

# Router yordamida handlerlarni ro'yxatga olish
def register_user_handlers(dp: Dispatcher):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(start_handler, Command("start"))  # Command filter used here
    router.callback_query.register(check_membership_handler, lambda c: c.data == "check_membership")
    router.callback_query.register(handle_likes, lambda c: c.data.startswith("like_") or c.data.startswith("dislike_"))
