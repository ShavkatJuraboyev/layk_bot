# utils/auth.py

def is_admin(user_id: int) -> bool:
    ADMINS = [1421622919, 2004004762]  # Adminlar Telegram IDlari ro'yxati
    return user_id in ADMINS
