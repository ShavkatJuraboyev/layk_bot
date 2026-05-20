from config import ADMIN_IDS


def is_admin(user_id: int | None) -> bool:
    if user_id is None:
        return False
    return int(user_id) in ADMIN_IDS
