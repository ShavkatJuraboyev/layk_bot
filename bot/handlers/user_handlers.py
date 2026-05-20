from aiogram import Router, F, Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

import database.db as db
from utils.membership import check_membership

router = Router()


def join_kb(channels):
    rows = [[InlineKeyboardButton(text=title, url=link)] for _id, _chat_id, title, link in channels]
    rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="user:check_membership")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def membership_ok(bot: Bot, user_id: int):
    channels = await db.get_channels()
    not_joined = []
    for ch in channels:
        if not await check_membership(bot, ch[3], user_id):
            not_joined.append(ch)
    return not_joined


async def send_start_page(msg: Message):
    start_page = await db.get_start_page()
    if start_page:
        photo_id, caption = start_page
        if photo_id:
            await msg.answer_photo(photo_id, caption=caption or "")
        else:
            await msg.answer(caption or "👋 Xush kelibsiz!")
    else:
        await msg.answer("👋 <b>Xush kelibsiz!</b>\nOvoz berish uchun bo‘limni tanlang.")


async def show_departments(msg: Message):
    deps = await db.get_departments(include_closed=True)
    if not deps:
        return await msg.answer("📭 Hozircha ovoz berishlar mavjud emas.")

    active_rows = []
    closed_rows = []
    for dep_id, name, _photo, is_active in deps:
        if is_active:
            active_rows.append([InlineKeyboardButton(text=f"🗳 {name}", callback_data=f"user:dep:{dep_id}")])
        else:
            closed_rows.append([InlineKeyboardButton(text=f"📊 {name}", callback_data=f"user:results:{dep_id}")])

    if active_rows:
        await msg.answer("🗳 <b>Faol ovoz berishlar</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=active_rows))
    if closed_rows:
        await msg.answer("📊 <b>Yakunlangan ovoz berishlar</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=closed_rows))


@router.message(CommandStart())
async def start(msg: Message, bot: Bot, state: FSMContext):
    await state.clear()
    await db.add_user(
        telegram_id=msg.from_user.id,
        full_name=msg.from_user.full_name or "",
        username=msg.from_user.username or "",
    )

    parts = (msg.text or "").split(maxsplit=1)
    payload = parts[1] if len(parts) > 1 else ""

    not_joined = await membership_ok(bot, msg.from_user.id)
    if not_joined:
        await send_start_page(msg)
        return await msg.answer(
            "❗ Ovoz berishdan oldin quyidagi kanallarga a’zo bo‘ling:",
            reply_markup=join_kb(not_joined)
        )

    if payload.startswith("vote_"):
        try:
            _, cand_id, dep_id = payload.split("_")
            return await process_vote(msg, bot, int(dep_id), int(cand_id))
        except Exception:
            pass

    await send_start_page(msg)
    await show_departments(msg)


@router.callback_query(F.data == "user:check_membership")
async def check_membership_cb(cb: CallbackQuery, bot: Bot):
    not_joined = await membership_ok(bot, cb.from_user.id)
    if not_joined:
        await cb.message.answer(
            "⚠️ Siz hali barcha kanallarga a’zo emassiz.",
            reply_markup=join_kb(not_joined)
        )
        return await cb.answer("A’zolik to‘liq emas", show_alert=True)

    await cb.message.answer("✅ A’zolik tasdiqlandi. Endi ovoz berishingiz mumkin.")
    await show_departments(cb.message)
    await cb.answer()


@router.callback_query(F.data.startswith("user:dep:"))
async def show_candidates(cb: CallbackQuery, bot: Bot):
    dep_id = int(cb.data.split(":")[-1])
    dep = await db.get_department(dep_id)
    if not dep:
        return await cb.message.answer("❌ Bo‘lim topilmadi.")
    if not dep[3]:
        return await cb.message.answer("🔒 Bu bo‘limda ovoz berish yakunlangan.")

    not_joined = await membership_ok(bot, cb.from_user.id)
    if not_joined:
        return await cb.message.answer(
            "❗ Ovoz berish uchun kanallarga a’zo bo‘ling:",
            reply_markup=join_kb(not_joined)
        )

    candidates = await db.get_candidates(dep_id, active_only=True)
    if not candidates:
        return await cb.message.answer("📭 Bu bo‘limda nomzodlar mavjud emas.")

    stats = await db.department_statistics(dep_id)
    votes = {cid: count for cid, _name, count in stats}
    user_vote = await db.user_vote(dep_id, cb.from_user.id)

    rows = []
    for cand_id, _dep, name, _photo, _video, _caption, _active in candidates:
        marker = "✅" if user_vote and user_vote[0] == cand_id else "🗳"
        rows.append([InlineKeyboardButton(text=f"{marker} {name} ({votes.get(cand_id, 0)})", callback_data=f"vote:{cand_id}:{dep_id}")])

    await cb.message.answer(
        f"🏷 <b>{dep[1]}</b>\nNomzodni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await cb.answer()


async def process_vote(msg_or_cb_message: Message, bot: Bot, dep_id: int, cand_id: int, user_id: int | None = None):
    user_id = user_id or msg_or_cb_message.chat.id
    not_joined = await membership_ok(bot, user_id)
    if not_joined:
        return await msg_or_cb_message.answer(
            "❗ Ovoz berish uchun quyidagi kanallarga a’zo bo‘ling:",
            reply_markup=join_kb(not_joined)
        )

    success = await db.vote(user_id, dep_id, cand_id)
    if not success:
        return await msg_or_cb_message.answer("⚠️ Siz ushbu bo‘limda allaqachon ovoz bergansiz yoki ovoz berish yopilgan.")

    cand = await db.get_candidate_by_id(cand_id)
    name = cand[2] if cand else "nomzod"
    await msg_or_cb_message.answer(f"✅ Ovozingiz qabul qilindi!\nSiz tanlagan nomzod: <b>{name}</b>")


@router.callback_query(F.data.startswith("vote:"))
async def vote_candidate(cb: CallbackQuery, bot: Bot):
    try:
        _, cand_id, dep_id = cb.data.split(":")
        cand_id = int(cand_id)
        dep_id = int(dep_id)
    except Exception:
        return await cb.answer("Noto‘g‘ri ma’lumot", show_alert=True)

    not_joined = await membership_ok(bot, cb.from_user.id)
    if not_joined:
        bot_info = await bot.me()
        rows = [[InlineKeyboardButton(text=title, url=link)] for _id, _chat_id, title, link in not_joined]
        rows.append([InlineKeyboardButton(text="✅ A’zo bo‘ldim", url=f"https://t.me/{bot_info.username}?start=vote_{cand_id}_{dep_id}")])
        await cb.message.answer("❗ Ovoz berish uchun kanallarga a’zo bo‘ling:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
        return await cb.answer()

    success = await db.vote(cb.from_user.id, dep_id, cand_id)
    if not success:
        return await cb.answer("⚠️ Siz allaqachon ovoz bergansiz yoki ovoz berish yopilgan.", show_alert=True)

    cand = await db.get_candidate_by_id(cand_id)
    await cb.answer("✅ Ovozingiz qabul qilindi!", show_alert=True)
    await cb.message.answer(f"✅ Rahmat! Siz <b>{cand[2] if cand else 'nomzod'}</b> uchun ovoz berdingiz.")


@router.callback_query(F.data.startswith("user:results:"))
async def user_results(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[-1])
    dep = await db.get_department(dep_id)
    results = await db.get_results(dep_id)
    if results:
        text = f"🏆 <b>{dep[1] if dep else 'Natijalar'}</b>\n\n"
        for _rid, _dep, place, _cand_id, custom_name, cand_name in results:
            text += f"{place}-o‘rin: <b>{cand_name or custom_name or '—'}</b>\n"
        return await cb.message.answer(text)

    stats = await db.department_statistics(dep_id)
    total = await db.count_all_votes(dep_id)
    if not stats:
        return await cb.message.answer("📭 Natijalar mavjud emas.")
    text = f"📊 <b>{dep[1] if dep else 'Natijalar'}</b>\nJami ovoz: <b>{total}</b>\n\n"
    for _cid, name, votes in stats:
        percent = round((votes / total) * 100, 1) if total else 0
        text += f"👤 {name}: <b>{votes}</b> ovoz — {percent}%\n"
    await cb.message.answer(text)
    await cb.answer()


@router.message(Command("results"))
async def results_command(msg: Message):
    await show_departments(msg)


def register_user_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)
