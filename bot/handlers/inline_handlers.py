from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultPhoto, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import get_departments
from aiogram import Bot

router = Router()

@router.inline_query()
async def inline_share(query: InlineQuery, bot: Bot):
    if query.query.startswith("like_"):
        department_id = int(query.query.split("_")[1])
        departments = await get_departments()
        department = next((d for d in departments if d[0] == department_id), None)

        if not department:
            return

        _, _, photo_id = department

        caption = (
            """🏛TATU SAMARQAND FILIALIDA ⚡️"ENG NA'MUNALI GURUH SARDORI"  TANLOVIGA START BERILDI.


⭐️ "ENG NA'MUNALI GURUH SARDORI"  aniqlang!

🔴  Mazkur so‘rovnomada g'olib bo'lganlarga diplom va esdalik sovg'alar topshiriladi."""
        )

        file_url = f"https://api.telegram.org/file/bot{bot.token}/{photo_id}"

        result = InlineQueryResultPhoto(
            id="1",
            photo_url=file_url,
            thumb_url=file_url,
            title="ENG NA'MUNALI GURUH SARDORI aniqlang!",
            description="Ushbu postni do‘stlaringiz bilan ulashing",
            caption=caption,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="Botni ochish", url=f"https://t.me/{(await bot.me()).username}?start")
                ]]
            ),
            input_message_content=InputTextMessageContent(message_text=caption)
        )

        await query.answer(results=[result], cache_time=1)
