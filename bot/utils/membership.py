from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError


def normalize_chat_id(link_or_username: str):
    value = (link_or_username or "").strip()
    if not value:
        return None
    if value.startswith("-100") or value.lstrip("-").isdigit():
        return int(value)
    value = value.replace("https://t.me/", "").replace("http://t.me/", "")
    value = value.split("?")[0].strip("/")
    if value.startswith("+") or value.startswith("joinchat/"):
        return None
    if not value.startswith("@"):
        value = "@" + value
    return value


async def check_membership(bot: Bot, channel_link: str, user_id: int) -> bool:
    chat_id = normalize_chat_id(channel_link)
    if chat_id is None:
        return False
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in {"member", "administrator", "creator"}
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        print(f"Kanal a'zoligini tekshirishda xatolik: {channel_link} | {e}")
        return False
    except Exception as e:
        print(f"Noma'lum xatolik: {channel_link} | {e}")
        return False
