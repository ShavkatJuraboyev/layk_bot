from aiogram import Router, F, Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import database.db as db
from config import ADMIN_IDS, DEFAULT_CHANNEL
from utils.auth import is_admin
from utils.membership import normalize_chat_id
from services.notifications import admin_tools_keyboard, send_birthdays_to_chat, send_weather_to_chat, send_test_to_admin

router = Router()


class StartPageFSM(StatesGroup):
    photo = State()
    caption = State()


class ChannelFSM(StatesGroup):
    title = State()
    link = State()


class DepartmentFSM(StatesGroup):
    name = State()
    photo = State()
    edit_name = State()
    edit_photo = State()


class CandidateFSM(StatesGroup):
    name = State()
    media = State()
    caption = State()
    edit_name = State()
    edit_media = State()
    edit_caption = State()


class ResultFSM(StatesGroup):
    custom_name = State()


def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Start sahifa", callback_data="admin:start")],
        [InlineKeyboardButton(text="📢 Majburiy kanallar", callback_data="admin:channels")],
        [InlineKeyboardButton(text="🏷 Bo‘limlar / ovoz yig‘uvchilar", callback_data="admin:deps")],
        [InlineKeyboardButton(text="🎂 Tug‘ilgan kun / 🌤 Ob-havo", callback_data="admin:notifications")],
        [InlineKeyboardButton(text="🏆 Natijalar", callback_data="admin:results")],
        [InlineKeyboardButton(text="📊 Umumiy statistika", callback_data="admin:stats")],
    ])


def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Admin panel", callback_data="admin:back")]
    ])


def start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yaratish / yangilash", callback_data="start:create")],
        [InlineKeyboardButton(text="👁 Ko‘rish", callback_data="start:view")],
        [InlineKeyboardButton(text="🗑 O‘chirish", callback_data="start:delete")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")],
    ])


def channels_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo‘shish", callback_data="channel:add")],
        [InlineKeyboardButton(text="📋 Kanallar ro‘yxati", callback_data="channel:list")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")],
    ])


def deps_kb(deps):
    rows = [[InlineKeyboardButton(text="➕ Bo‘lim qo‘shish", callback_data="dep:add")]]
    for dep_id, name, _photo, is_active in deps:
        icon = "🟢" if is_active else "🔴"
        rows.append([InlineKeyboardButton(text=f"{icon} {name}", callback_data=f"dep:open:{dep_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dep_manage_kb(dep_id: int, is_active: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Nomzodlar", callback_data=f"cand:list:{dep_id}")],
        [InlineKeyboardButton(text="📤 Kanalga yuborish", callback_data=f"send:preview:{dep_id}")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data=f"stat:dep:{dep_id}")],
        [
            InlineKeyboardButton(text="✏️ Nomini tahrirlash", callback_data=f"dep:edit_name:{dep_id}"),
            InlineKeyboardButton(text="🖼 Rasmini tahrirlash", callback_data=f"dep:edit_photo:{dep_id}"),
        ],
        [
            InlineKeyboardButton(text="🔒 Yopish" if is_active else "🔓 Ochish", callback_data=f"dep:toggle:{dep_id}"),
            InlineKeyboardButton(text="♻️ Ovozlarni tozalash", callback_data=f"dep:reset_votes:{dep_id}"),
        ],
        [InlineKeyboardButton(text="🗑 Bo‘limni o‘chirish", callback_data=f"dep:delete_confirm:{dep_id}")],
        [InlineKeyboardButton(text="⬅️ Bo‘limlar", callback_data="admin:deps")],
    ])


def candidate_manage_kb(candidate_id: int, dep_id: int, is_active: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Ism", callback_data=f"cand:edit_name:{candidate_id}"),
            InlineKeyboardButton(text="🖼 Media", callback_data=f"cand:edit_media:{candidate_id}"),
            InlineKeyboardButton(text="📝 Izoh", callback_data=f"cand:edit_caption:{candidate_id}"),
        ],
        [
            InlineKeyboardButton(text="🙈 Yashirish" if is_active else "👁 Ko‘rsatish", callback_data=f"cand:toggle:{candidate_id}"),
            InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"cand:delete_confirm:{candidate_id}"),
        ],
        [InlineKeyboardButton(text="⬅️ Nomzodlar", callback_data=f"cand:list:{dep_id}")],
    ])


async def notify_admins(bot: Bot, text: str):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception as e:
            print(f"Admin xabar yuborilmadi {admin_id}: {e}")


def admin_only(func):
    async def wrapper(event, *args, **kwargs):
        user = event.from_user

        if not is_admin(user.id):
            if isinstance(event, Message):
                await event.answer("⛔ Siz admin emassiz.")
            else:
                await event.answer("⛔ Siz admin emassiz.", show_alert=True)
            return

        # Aiogram baʼzan handlerga dispatcher, event_router kabi
        # qoʻshimcha service argumentlarni yuboradi.
        # Hamma handlerlar ularni qabul qilmaydi, shuning uchun
        # faqat kerakli argumentlarni qoldiramiz.
        allowed_kwargs = {}
        func_vars = func.__code__.co_varnames[:func.__code__.co_argcount]

        for key, value in kwargs.items():
            if key in func_vars:
                allowed_kwargs[key] = value

        return await func(event, *args, **allowed_kwargs)

    return wrapper


@router.message(Command("admin"))
@admin_only
async def admin_menu(msg: Message):
    await msg.answer("🔐 <b>Admin panel</b>\nKerakli bo‘limni tanlang:", reply_markup=admin_kb())


@router.callback_query(F.data == "admin:back")
@admin_only
async def admin_back(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("🔐 <b>Admin panel</b>", reply_markup=admin_kb())
    await cb.answer()




@router.callback_query(F.data == "admin:notifications")
@admin_only
async def admin_notifications(cb: CallbackQuery):
    await cb.message.answer(
        "🎂 <b>Tug‘ilgan kun va ob-havo bo‘limi</b>\n\n"
        "Bu yerdan ma’lumotni qo‘lda tekshirishingiz mumkin. "
        "Tug‘ilgan kunlar va ob-havo ma’lumotlari har kuni avtomatik tekshiriladi va kerakli xabarlar yuboriladi, shuning uchun qo‘lda tekshirish shart emas, lekin istasangiz bu yerda ham tekshirishingiz mumkin.\n\n"
        "va bu bir necha daqiqagacha davom etishi mumkin.",
        reply_markup=admin_tools_keyboard()
    )
    await cb.answer()


@router.callback_query(F.data == "notify:birthdays_today")
@admin_only
async def notify_birthdays_today(cb: CallbackQuery, bot: Bot):
    await cb.answer("Tekshirilmoqda...")
    await send_birthdays_to_chat(bot, cb.from_user.id, days_ahead=0)


@router.callback_query(F.data == "notify:birthdays_tomorrow")
@admin_only
async def notify_birthdays_tomorrow(cb: CallbackQuery, bot: Bot):
    await cb.answer("Tekshirilmoqda...")
    await send_birthdays_to_chat(bot, cb.from_user.id, days_ahead=1)


@router.callback_query(F.data == "notify:weather")
@admin_only
async def notify_weather(cb: CallbackQuery, bot: Bot):
    await cb.answer("Ob-havo olinmoqda...")
    await send_weather_to_chat(bot, cb.from_user.id)


@router.callback_query(F.data == "notify:test")
@admin_only
async def notify_test(cb: CallbackQuery, bot: Bot):
    await cb.answer("Test yuborilmoqda...")
    await send_test_to_admin(bot, cb.from_user.id)


@router.message(Command("test"))
@admin_only
async def test_command(msg: Message, bot: Bot):
    await send_test_to_admin(bot, msg.from_user.id)


@router.message(Command("obhavo_api"))
@admin_only
async def obhavo_command(msg: Message, bot: Bot):
    await send_weather_to_chat(bot, msg.from_user.id)


@router.message(Command("birthday"))
@admin_only
async def birthday_command(msg: Message, bot: Bot):
    await send_birthdays_to_chat(bot, msg.from_user.id, days_ahead=0)


@router.callback_query(F.data == "admin:start")
@admin_only
async def admin_start(cb: CallbackQuery):
    await cb.message.answer("🖼 <b>Start sahifa sozlamalari</b>", reply_markup=start_kb())
    await cb.answer()


@router.callback_query(F.data == "start:create")
@admin_only
async def start_create(cb: CallbackQuery, state: FSMContext):
    await state.set_state(StartPageFSM.photo)
    await cb.message.answer("Start sahifa uchun rasm yuboring. Rasm kerak bo‘lmasa /skip yuboring.")
    await cb.answer()


@router.message(F.text == "/skip", StateFilter(StartPageFSM.photo))
@admin_only
async def start_skip_photo(msg: Message, state: FSMContext):
    await state.update_data(photo_id=None)
    await state.set_state(StartPageFSM.caption)
    await msg.answer("Start sahifa matnini kiriting:")


@router.message(StartPageFSM.photo)
@admin_only
async def start_photo(msg: Message, state: FSMContext):
    if not msg.photo:
        return await msg.answer("Iltimos, rasm yuboring yoki /skip bosing.")
    await state.update_data(photo_id=msg.photo[-1].file_id)
    await state.set_state(StartPageFSM.caption)
    await msg.answer("Start sahifa matnini kiriting:")


@router.message(StartPageFSM.caption)
@admin_only
async def start_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.create_start_page(data.get("photo_id"), msg.html_text)
    await state.clear()
    await msg.answer("✅ Start sahifa saqlandi.", reply_markup=back_kb())


@router.callback_query(F.data == "start:view")
@admin_only
async def start_view(cb: CallbackQuery):
    data = await db.get_start_page()
    if not data:
        await cb.message.answer("📭 Start sahifa hali yaratilmagan.")
    else:
        photo_id, caption = data
        if photo_id:
            await cb.message.answer_photo(photo_id, caption=caption or "")
        else:
            await cb.message.answer(caption or "Matn yo‘q")
    await cb.answer()


@router.callback_query(F.data == "start:delete")
@admin_only
async def start_delete(cb: CallbackQuery):
    await db.delete_start_page()
    await cb.message.answer("🗑 Start sahifa o‘chirildi.")
    await cb.answer()


@router.callback_query(F.data == "admin:channels")
@admin_only
async def admin_channels(cb: CallbackQuery):
    await cb.message.answer("📢 <b>Majburiy kanallar</b>", reply_markup=channels_kb())
    await cb.answer()


@router.callback_query(F.data == "channel:add")
@admin_only
async def channel_add(cb: CallbackQuery, state: FSMContext):
    await state.set_state(ChannelFSM.title)
    await cb.message.answer("Kanal nomini kiriting:")
    await cb.answer()


@router.message(ChannelFSM.title)
@admin_only
async def channel_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text.strip())
    await state.set_state(ChannelFSM.link)
    await msg.answer("Kanal linki yoki username kiriting. Masalan: @kanal yoki https://t.me/kanal")


@router.message(ChannelFSM.link)
@admin_only
async def channel_link(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    link = msg.text.strip()
    chat_id = normalize_chat_id(link)
    real_chat_id = chat_id
    try:
        if chat_id:
            chat = await bot.get_chat(chat_id)
            real_chat_id = chat.id
    except Exception:
        real_chat_id = None
    await db.add_channel(real_chat_id, data["title"], link)
    await state.clear()
    await msg.answer("✅ Kanal qo‘shildi. Eslatma: a’zolik tekshiruvi ishlashi uchun bot kanalda admin bo‘lishi kerak.", reply_markup=channels_kb())


@router.callback_query(F.data == "channel:list")
@admin_only
async def channel_list(cb: CallbackQuery):
    channels = await db.get_channels()
    if not channels:
        await cb.message.answer("📭 Kanal mavjud emas.")
    for ch_id, chat_id, title, link in channels:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"channel:delete:{ch_id}")]
        ])
        await cb.message.answer(f"📢 <b>{title}</b>\n🔗 {link}\n🆔 {chat_id or 'aniqlanmadi'}", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("channel:delete:"))
@admin_only
async def channel_delete(cb: CallbackQuery):
    channel_id = int(cb.data.split(":")[-1])
    await db.delete_channel(channel_id)
    await cb.message.answer("🗑 Kanal o‘chirildi.", reply_markup=channels_kb())
    await cb.answer()


@router.callback_query(F.data == "admin:deps")
@admin_only
async def admin_deps(cb: CallbackQuery):
    deps = await db.get_departments(True)
    await cb.message.answer("🏷 <b>Bo‘limlar / ovoz yig‘uvchilar</b>", reply_markup=deps_kb(deps))
    await cb.answer()


@router.callback_query(F.data == "dep:add")
@admin_only
async def dep_add(cb: CallbackQuery, state: FSMContext):
    await state.set_state(DepartmentFSM.name)
    await cb.message.answer("Bo‘lim yoki ovoz yig‘uvchi nomini kiriting:")
    await cb.answer()


@router.message(DepartmentFSM.name)
@admin_only
async def dep_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await state.set_state(DepartmentFSM.photo)
    await msg.answer("Bo‘lim rasmini yuboring. Rasm kerak bo‘lmasa /skip yuboring.")


@router.message(F.text == "/skip", StateFilter(DepartmentFSM.photo))
@admin_only
async def dep_skip_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    dep_id = await db.add_department(data["name"], None)
    await state.clear()
    await msg.answer("✅ Bo‘lim qo‘shildi.", reply_markup=dep_manage_kb(dep_id, 1))


@router.message(DepartmentFSM.photo)
@admin_only
async def dep_photo(msg: Message, state: FSMContext):
    if not msg.photo:
        return await msg.answer("Rasm yuboring yoki /skip bosing.")
    data = await state.get_data()
    dep_id = await db.add_department(data["name"], msg.photo[-1].file_id)
    await state.clear()
    await msg.answer("✅ Bo‘lim qo‘shildi.", reply_markup=dep_manage_kb(dep_id, 1))


@router.callback_query(F.data.startswith("dep:open:"))
@admin_only
async def dep_open(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    dep = await db.get_department(dep_id)
    if not dep:
        await cb.message.answer("❌ Bo‘lim topilmadi.")
    else:
        _id, name, photo, is_active = dep
        total_votes = await db.count_all_votes(dep_id)
        text = f"🏷 <b>{name}</b>\n📌 Holat: {'🟢 faol' if is_active else '🔴 yopiq'}\n🗳 Ovozlar: <b>{total_votes}</b>"
        if photo:
            await cb.message.answer_photo(photo, caption=text, reply_markup=dep_manage_kb(dep_id, is_active))
        else:
            await cb.message.answer(text, reply_markup=dep_manage_kb(dep_id, is_active))
    await cb.answer()


@router.callback_query(F.data.startswith("dep:edit_name:"))
@admin_only
async def dep_edit_name_start(cb: CallbackQuery, state: FSMContext):
    dep_id = int(cb.data.split(":")[-1])
    await state.update_data(dep_id=dep_id)
    await state.set_state(DepartmentFSM.edit_name)
    await cb.message.answer("Yangi nomni kiriting:")
    await cb.answer()


@router.message(DepartmentFSM.edit_name)
@admin_only
async def dep_edit_name(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_department(data["dep_id"], name=msg.text.strip())
    await state.clear()
    await msg.answer("✅ Bo‘lim nomi tahrirlandi.")


@router.callback_query(F.data.startswith("dep:edit_photo:"))
@admin_only
async def dep_edit_photo_start(cb: CallbackQuery, state: FSMContext):
    dep_id = int(cb.data.split(":")[-1])
    await state.update_data(dep_id=dep_id)
    await state.set_state(DepartmentFSM.edit_photo)
    await cb.message.answer("Yangi rasm yuboring:")
    await cb.answer()


@router.message(DepartmentFSM.edit_photo)
@admin_only
async def dep_edit_photo(msg: Message, state: FSMContext):
    if not msg.photo:
        return await msg.answer("Iltimos, rasm yuboring.")
    data = await state.get_data()
    await db.update_department(data["dep_id"], photo_id=msg.photo[-1].file_id)
    await state.clear()
    await msg.answer("✅ Bo‘lim rasmi tahrirlandi.")


@router.callback_query(F.data.startswith("dep:toggle:"))
@admin_only
async def dep_toggle(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    dep = await db.get_department(dep_id)
    if dep:
        await db.set_department_status(dep_id, not bool(dep[3]))
        await cb.message.answer("✅ Bo‘lim holati o‘zgartirildi.")
    await cb.answer()


@router.callback_query(F.data.startswith("dep:reset_votes:"))
@admin_only
async def dep_reset_votes(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    await db.reset_votes_by_department(dep_id)
    await cb.message.answer("♻️ Ushbu bo‘lim ovozlari tozalandi.")
    await cb.answer()


@router.callback_query(F.data.startswith("dep:delete_confirm:"))
@admin_only
async def dep_delete_confirm(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, o‘chirish", callback_data=f"dep:delete:{dep_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"dep:open:{dep_id}")],
    ])
    await cb.message.answer("⚠️ Bo‘lim o‘chirilsa, nomzodlar va ovozlar ham o‘chadi. Davom etasizmi?", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("dep:delete:"))
@admin_only
async def dep_delete(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    await db.delete_department(dep_id)
    await cb.message.answer("🗑 Bo‘lim o‘chirildi.")
    await cb.answer()


@router.callback_query(F.data.startswith("cand:list:"))
@admin_only
async def cand_list(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    candidates = await db.get_candidates(dep_id)
    rows = [[InlineKeyboardButton(text="➕ Nomzod qo‘shish", callback_data=f"cand:add:{dep_id}")]]
    stats = await db.department_statistics(dep_id)
    votes = {cid: count for cid, _name, count in stats}
    for cand_id, _dep, name, _photo, _video, _caption, active in candidates:
        icon = "🟢" if active else "🔴"
        rows.append([InlineKeyboardButton(text=f"{icon} {name} — {votes.get(cand_id, 0)} ovoz", callback_data=f"cand:open:{cand_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Bo‘lim", callback_data=f"dep:open:{dep_id}")])
    await cb.message.answer("👤 <b>Nomzodlar ro‘yxati</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()


@router.callback_query(F.data.startswith("cand:add:"))
@admin_only
async def cand_add_start(cb: CallbackQuery, state: FSMContext):
    dep_id = int(cb.data.split(":")[-1])
    await state.update_data(dep_id=dep_id)
    await state.set_state(CandidateFSM.name)
    await cb.message.answer("Nomzod ismini kiriting:")
    await cb.answer()


@router.message(CandidateFSM.name)
@admin_only
async def cand_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await state.set_state(CandidateFSM.media)
    await msg.answer("Nomzod rasmi yoki videosini yuboring. Kerak bo‘lmasa /skip yuboring.")


@router.message(F.text == "/skip", StateFilter(CandidateFSM.media))
@admin_only
async def cand_skip_media(msg: Message, state: FSMContext):
    await state.update_data(photo_id=None, video_id=None)
    await state.set_state(CandidateFSM.caption)
    await msg.answer("Nomzod haqida izoh kiriting. Kerak bo‘lmasa /skip yuboring.")


@router.message(CandidateFSM.media)
@admin_only
async def cand_media(msg: Message, state: FSMContext):
    photo_id = msg.photo[-1].file_id if msg.photo else None
    video_id = msg.video.file_id if msg.video else None
    if not photo_id and not video_id:
        return await msg.answer("Rasm yoki video yuboring. Kerak bo‘lmasa /skip yuboring.")
    await state.update_data(photo_id=photo_id, video_id=video_id)
    await state.set_state(CandidateFSM.caption)
    await msg.answer("Nomzod haqida izoh kiriting. Kerak bo‘lmasa /skip yuboring.")


@router.message(F.text == "/skip", StateFilter(CandidateFSM.caption))
@admin_only
async def cand_skip_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    cand_id = await db.add_candidate(data["dep_id"], data["name"], data.get("photo_id"), data.get("video_id"), None)
    await state.clear()
    await msg.answer("✅ Nomzod qo‘shildi.", reply_markup=candidate_manage_kb(cand_id, data["dep_id"], 1))


@router.message(CandidateFSM.caption)
@admin_only
async def cand_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    cand_id = await db.add_candidate(data["dep_id"], data["name"], data.get("photo_id"), data.get("video_id"), msg.html_text)
    await state.clear()
    await msg.answer("✅ Nomzod qo‘shildi.", reply_markup=candidate_manage_kb(cand_id, data["dep_id"], 1))


@router.callback_query(F.data.startswith("cand:open:"))
@admin_only
async def cand_open(cb: CallbackQuery):
    cand_id = int(cb.data.split(":")[-1])
    cand = await db.get_candidate_by_id(cand_id)
    if not cand:
        return await cb.message.answer("❌ Nomzod topilmadi.")
    _id, dep_id, name, photo_id, video_id, caption, active = cand
    votes = await db.department_statistics(dep_id)
    vote_count = next((v for cid, _n, v in votes if cid == cand_id), 0)
    text = f"👤 <b>{name}</b>\n📌 Holat: {'🟢 faol' if active else '🔴 yashirilgan'}\n🗳 Ovoz: <b>{vote_count}</b>\n\n{caption or ''}"
    if photo_id:
        await cb.message.answer_photo(photo_id, caption=text, reply_markup=candidate_manage_kb(cand_id, dep_id, active))
    elif video_id:
        await cb.message.answer_video(video_id, caption=text, reply_markup=candidate_manage_kb(cand_id, dep_id, active))
    else:
        await cb.message.answer(text, reply_markup=candidate_manage_kb(cand_id, dep_id, active))
    await cb.answer()


@router.callback_query(F.data.startswith("cand:edit_name:"))
@admin_only
async def cand_edit_name_start(cb: CallbackQuery, state: FSMContext):
    cand_id = int(cb.data.split(":")[-1])
    await state.update_data(cand_id=cand_id)
    await state.set_state(CandidateFSM.edit_name)
    await cb.message.answer("Yangi ismni kiriting:")
    await cb.answer()


@router.message(CandidateFSM.edit_name)
@admin_only
async def cand_edit_name(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_candidate(data["cand_id"], name=msg.text.strip())
    await state.clear()
    await msg.answer("✅ Nomzod ismi tahrirlandi.")


@router.callback_query(F.data.startswith("cand:edit_media:"))
@admin_only
async def cand_edit_media_start(cb: CallbackQuery, state: FSMContext):
    cand_id = int(cb.data.split(":")[-1])
    await state.update_data(cand_id=cand_id)
    await state.set_state(CandidateFSM.edit_media)
    await cb.message.answer("Yangi rasm/video yuboring. Medianı olib tashlash uchun /clear yuboring.")
    await cb.answer()


@router.message(F.text == "/clear", StateFilter(CandidateFSM.edit_media))
@admin_only
async def cand_clear_media(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.clear_candidate_media(data["cand_id"])
    await state.clear()
    await msg.answer("✅ Nomzod mediasi olib tashlandi.")


@router.message(CandidateFSM.edit_media)
@admin_only
async def cand_edit_media(msg: Message, state: FSMContext):
    photo_id = msg.photo[-1].file_id if msg.photo else None
    video_id = msg.video.file_id if msg.video else None
    if not photo_id and not video_id:
        return await msg.answer("Rasm/video yuboring yoki /clear bosing.")
    data = await state.get_data()
    await db.update_candidate(data["cand_id"], photo_id=photo_id, video_id=video_id)
    await state.clear()
    await msg.answer("✅ Nomzod mediasi tahrirlandi.")


@router.callback_query(F.data.startswith("cand:edit_caption:"))
@admin_only
async def cand_edit_caption_start(cb: CallbackQuery, state: FSMContext):
    cand_id = int(cb.data.split(":")[-1])
    await state.update_data(cand_id=cand_id)
    await state.set_state(CandidateFSM.edit_caption)
    await cb.message.answer("Yangi izohni kiriting:")
    await cb.answer()


@router.message(CandidateFSM.edit_caption)
@admin_only
async def cand_edit_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_candidate(data["cand_id"], caption=msg.html_text)
    await state.clear()
    await msg.answer("✅ Nomzod izohi tahrirlandi.")


@router.callback_query(F.data.startswith("cand:toggle:"))
@admin_only
async def cand_toggle(cb: CallbackQuery):
    cand_id = int(cb.data.split(":")[-1])
    cand = await db.get_candidate_by_id(cand_id)
    if cand:
        await db.set_candidate_status(cand_id, not bool(cand[6]))
        await cb.message.answer("✅ Nomzod holati o‘zgartirildi.")
    await cb.answer()


@router.callback_query(F.data.startswith("cand:delete_confirm:"))
@admin_only
async def cand_delete_confirm(cb: CallbackQuery):
    cand_id = int(cb.data.split(":")[-1])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, o‘chirish", callback_data=f"cand:delete:{cand_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cand:open:{cand_id}")],
    ])
    await cb.message.answer("⚠️ Nomzod o‘chirilsa, unga berilgan ovozlar ham o‘chadi. Davom etasizmi?", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("cand:delete:"))
@admin_only
async def cand_delete(cb: CallbackQuery):
    cand_id = int(cb.data.split(":")[-1])
    await db.delete_candidate(cand_id)
    await cb.message.answer("🗑 Nomzod o‘chirildi.")
    await cb.answer()


def build_department_post(dep_id: int, base_caption: str, candidates_stats):
    text = f"{base_caption or ''}\n\n<b>🗳 NOMZODLAR:</b>\n"
    keyboard = []
    for cand_id, name, votes in candidates_stats:
        keyboard.append([InlineKeyboardButton(text=f"🗳 {name} ({votes})", callback_data=f"vote:{cand_id}:{dep_id}")])
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data.startswith("send:preview:"))
@admin_only
async def send_preview(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    dep = await db.get_department(dep_id)
    if not dep:
        return await cb.message.answer("❌ Bo‘lim topilmadi.")
    start_page = await db.get_start_page()
    photo_id, base_caption = start_page if start_page else (dep[2], f"🏷 <b>{dep[1]}</b>")
    stats = await db.department_statistics(dep_id)
    caption, keyboard = build_department_post(dep_id, base_caption, stats)
    if photo_id:
        await cb.message.answer_photo(photo_id, caption=caption, reply_markup=keyboard)
    else:
        await cb.message.answer(caption, reply_markup=keyboard)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Kanalga yuborish", callback_data=f"send:channel:{dep_id}")],
        [InlineKeyboardButton(text="⬅️ Bo‘lim", callback_data=f"dep:open:{dep_id}")],
    ])
    await cb.message.answer("Postni kanalga yuborasizmi?", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("send:channel:"))
@admin_only
async def send_channel(cb: CallbackQuery, bot: Bot):
    dep_id = int(cb.data.split(":")[-1])
    dep = await db.get_department(dep_id)
    start_page = await db.get_start_page()
    photo_id, base_caption = start_page if start_page else (dep[2] if dep else None, f"🏷 <b>{dep[1] if dep else 'Ovoz berish'}</b>")
    stats = await db.department_statistics(dep_id)
    caption, keyboard = build_department_post(dep_id, base_caption, stats)
    try:
        if photo_id:
            await bot.send_photo(DEFAULT_CHANNEL, photo_id, caption=caption, reply_markup=keyboard)
        else:
            await bot.send_message(DEFAULT_CHANNEL, caption, reply_markup=keyboard)
        await cb.answer("✅ Kanalga yuborildi", show_alert=True)
    except Exception as e:
        await cb.message.answer(f"❌ Kanalga yuborishda xatolik: {e}")
        await cb.answer()


@router.callback_query(F.data == "admin:stats")
@admin_only
async def admin_stats(cb: CallbackQuery):
    deps = await db.get_departments(True)
    if not deps:
        await cb.message.answer("📭 Bo‘limlar mavjud emas.")
    for dep_id, name, _photo, is_active in deps:
        stats = await db.department_statistics(dep_id)
        total = await db.count_all_votes(dep_id)
        text = f"📊 <b>{name}</b> — jami {total} ovoz\n"
        for _cid, cand_name, votes in stats:
            text += f"• {cand_name}: {votes}\n"
        await cb.message.answer(text)
    await cb.answer()


@router.callback_query(F.data.startswith("stat:dep:"))
@admin_only
async def stat_dep(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    dep = await db.get_department(dep_id)
    stats = await db.department_statistics(dep_id)
    total = await db.count_all_votes(dep_id)
    text = f"📊 <b>{dep[1] if dep else 'Bo‘lim'}</b>\nJami ovoz: <b>{total}</b>\n\n"
    for _cid, name, votes in stats:
        percent = round((votes / total) * 100, 1) if total else 0
        text += f"👤 {name}: <b>{votes}</b> ovoz — {percent}%\n"
    await cb.message.answer(text or "Statistika yo‘q.")
    await cb.answer()


@router.callback_query(F.data == "admin:results")
@admin_only
async def admin_results(cb: CallbackQuery):
    deps = await db.get_departments(True)
    rows = [[InlineKeyboardButton(text=d[1], callback_data=f"result:dep:{d[0]}")] for d in deps]
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")])
    await cb.message.answer("🏆 Natija kiritish uchun bo‘lim tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()


@router.callback_query(F.data.startswith("result:dep:"))
@admin_only
async def result_dep(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    stats = await db.department_statistics(dep_id)
    rows = []
    for cand_id, name, votes in stats:
        rows.append([InlineKeyboardButton(text=f"{name} ({votes})", callback_data=f"result:cand:{dep_id}:{cand_id}")])
    rows.append([InlineKeyboardButton(text="✍️ Qo‘lda nom kiritish", callback_data=f"result:custom:{dep_id}")])
    rows.append([InlineKeyboardButton(text="👁 Natijalarni ko‘rish", callback_data=f"result:view:{dep_id}")])
    await cb.message.answer("Natija uchun nomzod tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()


@router.callback_query(F.data.startswith("result:cand:"))
@admin_only
async def result_cand(cb: CallbackQuery):
    _, _, dep_id, cand_id = cb.data.split(":")
    rows = [[InlineKeyboardButton(text=f"{i}-o‘rin", callback_data=f"result:place:{dep_id}:{cand_id}:{i}")] for i in range(1, 4)]
    await cb.message.answer("O‘rinni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()


@router.callback_query(F.data.startswith("result:place:"))
@admin_only
async def result_place(cb: CallbackQuery):
    _, _, dep_id, cand_id, place = cb.data.split(":")
    await db.add_result(int(dep_id), int(place), candidate_id=int(cand_id))
    await cb.message.answer(f"✅ {place}-o‘rin saqlandi.")
    await cb.answer()


@router.callback_query(F.data.startswith("result:custom:"))
@admin_only
async def result_custom_start(cb: CallbackQuery, state: FSMContext):
    dep_id = int(cb.data.split(":")[-1])
    await state.update_data(dep_id=dep_id)
    await state.set_state(ResultFSM.custom_name)
    await cb.message.answer("Natija uchun nomni qo‘lda kiriting. Format: <code>1; Ali Valiyev</code>")
    await cb.answer()


@router.message(ResultFSM.custom_name)
@admin_only
async def result_custom_save(msg: Message, state: FSMContext):
    data = await state.get_data()
    try:
        place_raw, name = msg.text.split(";", 1)
        place = int(place_raw.strip())
        await db.add_result(data["dep_id"], place, candidate_id=None, custom_name=name.strip())
        await state.clear()
        await msg.answer("✅ Qo‘lda natija saqlandi.")
    except Exception:
        await msg.answer("❌ Format noto‘g‘ri. Masalan: <code>1; Ali Valiyev</code>")


@router.callback_query(F.data.startswith("result:view:"))
@admin_only
async def result_view(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    results = await db.get_results(dep_id)
    if not results:
        await cb.message.answer("📭 Natijalar mavjud emas.")
    else:
        text = "🏆 <b>Natijalar</b>\n\n"
        for result_id, _dep, place, _cand_id, custom_name, cand_name in results:
            name = cand_name or custom_name or "—"
            text += f"{place}-o‘rin: <b>{name}</b> /del_result_{result_id}\n"
        await cb.message.answer(text)
    await cb.answer()


@router.message(F.text.startswith("/del_result_"))
@admin_only
async def delete_result_cmd(msg: Message):
    try:
        result_id = int(msg.text.replace("/del_result_", ""))
        await db.delete_result(result_id)
        await msg.answer("🗑 Natija o‘chirildi.")
    except Exception:
        await msg.answer("❌ Natija ID noto‘g‘ri.")


def register_admin_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)
