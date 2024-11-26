from aiogram import Bot

async def check_membership(bot: Bot, user_id: int, channel_username: str):
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking membership for {channel_username}: {e}")
        return False
