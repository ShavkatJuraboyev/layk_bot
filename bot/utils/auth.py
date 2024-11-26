from aiogram.types import Message

def is_admin(message: Message, admins: list) -> bool:
    return message.from_user.id in admins
