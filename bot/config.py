import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

DEFAULT_ADMIN_IDS = "1421622919,2004004762"
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", DEFAULT_ADMIN_IDS).split(",")
    if x.strip().isdigit()
}

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "data" / "bot.db"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")
DEFAULT_CHANNEL = os.getenv("DEFAULT_CHANNEL", "@tatusfyoshlarittifoqi")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylda ko'rsatilmagan!")

API_TOKEN = os.getenv("API_TOKEN", "").strip()
WEATHER_API_KEY_ONE = os.getenv("WEATHER_API_KEY_ONE", "").strip()
CITY = os.getenv("CITY", "Samarqand").strip()
HEMIS_EMPLOYEE_API_URL = os.getenv("HEMIS_EMPLOYEE_API_URL", "https://student.samtuit.uz/rest/v1/data/employee-list?type=all").strip()
BIRTHDAY_NOTIFY_TIME = os.getenv("BIRTHDAY_NOTIFY_TIME", "09:00").strip()
WEATHER_NOTIFY_TIME = os.getenv("WEATHER_NOTIFY_TIME", "08:00").strip()
AUTO_NOTIFY_ENABLED = os.getenv("AUTO_NOTIFY_ENABLED", "1").strip() == "1"