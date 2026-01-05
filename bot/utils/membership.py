from aiogram import Bot
from aiogram.types import ChatMember

async def check_membership(bot: Bot, channel_link: str, user_id: int):
    """
    channel_link -> kanallarni db da saqlanishi: 'https://t.me/example_channel' yoki 'example_channel'
    user_id -> telegram foydalanuvchi id
    """
    try:
        # username olish
        if channel_link.startswith("https://t.me/"):
            username = channel_link.split("https://t.me/")[-1].strip()
        else:
            username = channel_link.strip()

        # Telegram API orqali a'zo ekanligini tekshirish
        member: ChatMember = await bot.get_chat_member(chat_id=f"@{username}", user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        # Public kanalda bot kanalda bo'lmasa yoki private kanal bo'lsa, xatolik qaytadi
        print(f"Error checking membership for {channel_link}: {e}")
        return False