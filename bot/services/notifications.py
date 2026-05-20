import asyncio
from datetime import datetime, timedelta
from html import escape
from typing import Any

import requests
import pytz
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import (
    ADMIN_IDS,
    API_TOKEN,
    BIRTHDAY_NOTIFY_TIME,
    CITY,
    HEMIS_EMPLOYEE_API_URL,
    TIMEZONE,
    WEATHER_API_KEY_ONE,
    WEATHER_NOTIFY_TIME,
)


def now_tashkent() -> datetime:
    return datetime.now(pytz.timezone(TIMEZONE))


def admin_tools_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎂 Bugungi tug‘ilgan kunlar", callback_data="notify:birthdays_today")],
        [InlineKeyboardButton(text="📌 Ertangi tug‘ilgan kunlar", callback_data="notify:birthdays_tomorrow")],
        [InlineKeyboardButton(text="🌤 Bugungi ob-havo", callback_data="notify:weather")],
        [InlineKeyboardButton(text="🧪 Test: tug‘ilgan kun + ob-havo", callback_data="notify:test")],
        [InlineKeyboardButton(text="⬅️ Admin panel", callback_data="admin:back")],
    ])


async def send_text_safe(bot: Bot, chat_id: int, text: str, reply_markup=None):
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Xabar yuborilmadi: {chat_id} | {e}")


async def send_photo_safe(bot: Bot, chat_id: int, photo: str, caption: str, reply_markup=None):
    try:
        await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=reply_markup)
    except Exception as e:
        print(f"Rasm yuborilmadi: {chat_id} | {e}")
        await send_text_safe(bot, chat_id, caption, reply_markup=reply_markup)


async def broadcast_text(bot: Bot, text: str, reply_markup=None):
    for admin_id in ADMIN_IDS:
        await send_text_safe(bot, admin_id, text, reply_markup=reply_markup)


async def broadcast_photo(bot: Bot, photo: str, caption: str, reply_markup=None):
    for admin_id in ADMIN_IDS:
        await send_photo_safe(bot, admin_id, photo, caption, reply_markup=reply_markup)


def _get_json(url: str, *, params: dict | None = None, headers: dict | None = None, timeout: int = 15) -> dict[str, Any]:
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else {}


async def fetch_employees() -> list[dict[str, Any]]:
    if not API_TOKEN:
        return []

    def worker() -> list[dict[str, Any]]:
        employees: list[dict[str, Any]] = []
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        for page in range(1, 80):
            url = f"{HEMIS_EMPLOYEE_API_URL}&page={page}"
            try:
                data = _get_json(url, headers=headers)
            except Exception as e:
                print(f"HEMIS API xatolik, page={page}: {e}")
                break

            payload = data.get("data", {})
            if isinstance(payload, dict):
                items = payload.get("items", [])
            elif isinstance(payload, list):
                items = payload
            else:
                items = []

            if not items:
                break
            employees.extend(items)
        return employees

    return await asyncio.to_thread(worker)


def _parse_birth_date(value) -> datetime | None:
    try:
        if value in (None, ""):
            return None
        if isinstance(value, str) and "-" in value:
            return datetime.fromisoformat(value[:10])
        timestamp = float(value)
        if timestamp > 1e12:
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp, pytz.timezone(TIMEZONE))
    except Exception:
        return None


def _employee_unique_key(emp: dict[str, Any]) -> str:
    """
    HEMIS baʼzan bitta xodimni bir nechta bo‘lim/stavka bo‘yicha qaytaradi.
    Shuning uchun avval eng ishonchli maydonlar bilan bitta xodimni bitta qilib olamiz.
    """
    employee_id_number = emp.get("employee_id_number")
    if employee_id_number:
        return f"employee_id_number:{employee_id_number}"

    meta_id = emp.get("meta_id")
    if meta_id:
        return f"meta_id:{meta_id}"

    hemis_id = emp.get("id")
    full_name = str(emp.get("full_name") or "").strip().upper()
    birth_date = str(emp.get("birth_date") or "").strip()

    if full_name and birth_date:
        return f"full_name_birth:{full_name}:{birth_date}"

    return f"id:{hemis_id}:{full_name}:{birth_date}"


def _employee_info(emp: dict[str, Any], birth_date: datetime) -> dict[str, str]:
    department = emp.get("department") or {}
    department_type = department.get("structureType") or {}
    staff_position = emp.get("staffPosition") or {}
    employment_form = emp.get("employmentForm") or {}

    position = staff_position.get("name") or department_type.get("name") or "Lavozim ko‘rsatilmagan"

    return {
        "full_name": str(emp.get("full_name") or emp.get("name") or "Noma’lum xodim"),
        "short_name": str(emp.get("short_name") or ""),
        "department": str(department.get("name") or "Bo‘lim ko‘rsatilmagan"),
        "department_type": str(department_type.get("name") or ""),
        "position": str(position),
        "employment_form": str(employment_form.get("name") or ""),
        "employee_id_number": str(emp.get("employee_id_number") or ""),
        "birth_date": birth_date.strftime("%d.%m.%Y"),
        "image": str(emp.get("image_full") or emp.get("image") or ""),
    }


async def get_birthdays(days_ahead: int = 0) -> list[dict[str, str]]:
    employees = await fetch_employees()
    target = now_tashkent() + timedelta(days=days_ahead)
    target_md = target.strftime("%m-%d")
    result: list[dict[str, str]] = []
    seen: set[str] = set()

    for emp in employees:
        birth_date = _parse_birth_date(emp.get("birth_date"))
        if not birth_date:
            continue

        if birth_date.strftime("%m-%d") != target_md:
            continue

        unique_key = _employee_unique_key(emp)
        if unique_key in seen:
            continue

        seen.add(unique_key)
        result.append(_employee_info(emp, birth_date))

    result.sort(key=lambda x: x["full_name"])
    return result


def birthday_caption(emp: dict[str, str], today: bool = True) -> str:
    day_text = "Bugun" if today else "Ertaga"
    full_name = escape(emp["full_name"])
    department = escape(emp["department"])
    position = escape(emp["position"])
    birth_date = escape(emp["birth_date"])
    return (
        f"🎂 <b>{day_text} tavallud kuni</b>\n\n"
        f"👤 <b>{full_name}</b>\n"
        f"🏢 Bo‘lim: <b>{department}</b>\n"
        f"💼 Lavozim: <b>{position}</b>\n"
        f"📅 Tug‘ilgan sana: <b>{birth_date}</b>\n\n"
        f"<i>Hurmatli {full_name}, sizga sihat-salomatlik, oilaviy xotirjamlik, "
        f"ishlaringizda ulkan muvaffaqiyatlar tilaymiz!</i>\n\n"
        "🌐 <b>TATU Samarqand filiali axborot xizmati</b>"
    )


async def send_birthdays_to_chat(bot: Bot, chat_id: int, days_ahead: int = 0):
    birthdays = await get_birthdays(days_ahead)
    today = days_ahead == 0
    title = "bugun" if today else "ertaga"

    if not birthdays:
        return await send_text_safe(
            bot,
            chat_id,
            f"📭 <b>{title.capitalize()} tug‘ilgan kunlar topilmadi.</b>\n\n"
            "Agar ma’lumot chiqmasa, <code>API_TOKEN</code> va HEMIS ulanishini tekshiring."
        )

    await send_text_safe(bot, chat_id, f"🎂 <b>{title.capitalize()} tug‘ilgan kunlar:</b> {len(birthdays)} ta")
    for emp in birthdays:
        caption = birthday_caption(emp, today=today)
        if emp.get("image"):
            await send_photo_safe(bot, chat_id, emp["image"], caption)
        else:
            await send_text_safe(bot, chat_id, caption)


async def broadcast_birthdays(bot: Bot, days_ahead: int = 0):
    for admin_id in ADMIN_IDS:
        await send_birthdays_to_chat(bot, admin_id, days_ahead)


def weather_icon(condition: str) -> str:
    text = condition.lower()
    if "rain" in text or "drizzle" in text:
        return "🌧"
    if "snow" in text:
        return "❄️"
    if "thunder" in text:
        return "⛈"
    if "cloud" in text or "overcast" in text:
        return "☁️"
    if "fog" in text or "mist" in text:
        return "🌫"
    return "☀️"


def weather_uz(condition: str) -> str:
    translations = {
        "Sunny": "Quyoshli",
        "Clear": "Ochiq osmon",
        "Partly cloudy": "Qisman bulutli",
        "Cloudy": "Bulutli",
        "Overcast": "Qorong‘i bulutli",
        "Mist": "Tumanli",
        "Fog": "Tuman",
        "Patchy rain nearby": "Yaqin hududlarda yomg‘ir",
        "Light rain": "Yengil yomg‘ir",
        "Moderate rain": "O‘rtacha yomg‘ir",
        "Heavy rain": "Kuchli yomg‘ir",
        "Light snow": "Yengil qor",
        "Moderate snow": "O‘rtacha qor",
        "Heavy snow": "Kuchli qor",
        "Thunderstorm": "Momaqaldiroq",
    }
    return translations.get(condition, condition)


async def get_weather_caption(city: str = CITY) -> tuple[str, str | None]:
    if not WEATHER_API_KEY_ONE:
        return "❌ WEATHER_API_KEY_ONE .env faylda ko‘rsatilmagan.", None

    def worker():
        data = _get_json(
            "http://api.weatherapi.com/v1/forecast.json",
            params={"key": WEATHER_API_KEY_ONE, "q": city, "days": 1, "aqi": "no", "alerts": "no"},
        )
        location = data.get("location", {})
        day = data.get("forecast", {}).get("forecastday", [{}])[0].get("day", {})
        condition = day.get("condition", {}).get("text", "Noma’lum")
        icon_url = day.get("condition", {}).get("icon")
        icon_url = f"https:{icon_url}" if icon_url and icon_url.startswith("//") else icon_url
        caption = (
            f"{weather_icon(condition)} <b>Bugungi ob-havo</b>\n\n"
            f"📍 <b>{escape(str(location.get('name', city)))}, {escape(str(location.get('country', '')))}</b>\n"
            f"📅 {now_tashkent().strftime('%d.%m.%Y')}\n\n"
            f"🌡 O‘rtacha: <b>{day.get('avgtemp_c', '—')}°C</b>\n"
            f"⬆️ Maksimum: <b>{day.get('maxtemp_c', '—')}°C</b>\n"
            f"⬇️ Minimum: <b>{day.get('mintemp_c', '—')}°C</b>\n"
            f"☁️ Holat: <b>{escape(weather_uz(condition))}</b>\n"
            f"💧 Namlik: <b>{day.get('avghumidity', '—')}%</b>\n"
            f"💨 Shamol: <b>{day.get('maxwind_kph', '—')} km/soat</b>\n\n"
            "🌐 <b>TATU Samarqand filiali axborot xizmati</b>"
        )
        return caption, icon_url

    try:
        return await asyncio.to_thread(worker)
    except Exception as e:
        return f"❌ Ob-havo ma’lumotini olishda xatolik: <code>{escape(str(e))}</code>", None


async def send_weather_to_chat(bot: Bot, chat_id: int):
    caption, photo = await get_weather_caption(CITY)
    if photo:
        await send_photo_safe(bot, chat_id, photo, caption)
    else:
        await send_text_safe(bot, chat_id, caption)


async def broadcast_weather(bot: Bot):
    for admin_id in ADMIN_IDS:
        await send_weather_to_chat(bot, admin_id)


async def send_test_to_admin(bot: Bot, admin_id: int):
    await send_text_safe(bot, admin_id, "🧪 <b>Test boshlandi.</b>\nBugungi tug‘ilgan kunlar va ob-havo faqat sizga yuboriladi.")
    await send_birthdays_to_chat(bot, admin_id, days_ahead=0)
    await send_weather_to_chat(bot, admin_id)
    await send_text_safe(bot, admin_id, "✅ <b>Test tugadi.</b>")


async def daily_notifications_loop(bot: Bot):
    """Bot ishga tushganda avtomatik ogohlantirishlar: tug‘ilgan kun va ob-havo."""
    sent_keys: set[str] = set()
    while True:
        try:
            current = now_tashkent()
            hm = current.strftime("%H:%M")
            day = current.strftime("%Y-%m-%d")

            birthday_key = f"birthday:{day}"
            weather_key = f"weather:{day}"

            if hm == BIRTHDAY_NOTIFY_TIME and birthday_key not in sent_keys:
                await broadcast_birthdays(bot, days_ahead=0)
                await broadcast_birthdays(bot, days_ahead=1)
                sent_keys.add(birthday_key)

            if hm == WEATHER_NOTIFY_TIME and weather_key not in sent_keys:
                await broadcast_weather(bot)
                sent_keys.add(weather_key)

            # Kechagi kalitlarni tozalab turamiz.
            if len(sent_keys) > 10:
                sent_keys = {k for k in sent_keys if k.endswith(day)}
        except Exception as e:
            print(f"daily_notifications_loop xatolik: {e}")

        await asyncio.sleep(30)
