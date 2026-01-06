from aiogram import Router, F, Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import database.db as db
from utils.membership import check_membership
from handlers.admin_handlers import build_department_post

router = Router()

# ==========================
# /start
# ==========================
@router.message(Command("start"))
async def start(msg: Message, bot: Bot, state: FSMContext):
    user_id = msg.from_user.id
    await db.add_user(user_id)

    # Start page
    start_page = await db.get_start_page()
    if start_page:
        photo_id, caption = start_page
        if photo_id:
            await msg.answer_photo(photo_id, caption=caption)
        else:
            await msg.answer(caption or "Xush kelibsiz!")
    else:
        await msg.answer("Xush kelibsiz! Botga xush kelibsiz!")

    # Kanal tekshirish
    channels = await db.get_channels()
    if channels:
        all_membership = []
        for ch in channels:
            ch_id, chat_id, name, link = ch
            is_member = await check_membership(bot, link, user_id)
            all_membership.append(is_member)

        if all(all_membership):
            # Agar foydalanuvchi barcha kanallarga a'zo bo'lsa
            await show_departments(msg)
        else:
            # Agar foydalanuvchi hali hammasiga a'zo bo'lmasa
            buttons = [[InlineKeyboardButton(text=ch[2], url=ch[3])] for ch in channels]
            buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_membership")])
            await msg.answer(
                "Ovoz berishdan oldin quyidagi kanallarga a’zo bo‘ling va tekshirish tugmasini bosing 👇",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
    else:
        await show_departments(msg)

# ==========================
# Tekshirish tugmasi
# ==========================
@router.callback_query(lambda cb: cb.data == "check_membership")
async def check_cb(cb: CallbackQuery, bot: Bot):
    user_id = cb.from_user.id
    channels = await db.get_channels()
    if not channels:
        await cb.message.answer("⚠️ Majburiy kanallar mavjud emas.")
        await show_departments(cb.message)
        return

    all_membership = []
    for ch in channels:
        ch_id, chat_id, name, link = ch
        is_member = await check_membership(bot, link, user_id)
        all_membership.append(is_member)

    if all(all_membership):
        await cb.message.answer("✅ Siz barcha majburiy kanallarga a’zosiz! Endi ovoz berishingiz mumkin.")
        await show_departments(cb.message)
    else:
        await cb.message.answer("⚠️ Siz hali barcha kanallarga a’zo emassiz. Iltimos, qo‘shiling va qayta tekshiring.")

# ==========================
# Bo'limlarni ko'rsatish (faol va tugaganlarni ajratish)
# ==========================
async def show_departments(msg: Message):
    deps = await db.get_departments(include_closed=True)
    if not deps:
        await msg.answer("Hozircha ovoz berishlar mavjud emas.")
        return

    active_deps = []
    closed_deps = []

    for dep in deps:
        dep_id, dep_name, dep_photo_id, dep_is_active = dep
        if dep_is_active:  # ovoz berish muddati tugamagan bo'limlar
            active_deps.append((dep_id, dep_name))
        else:  # ovoz berish muddati tugagan bo'limlar
            closed_deps.append((dep_id, dep_name))

    # Faol bo'limlar tugmasi
    if active_deps:
        kb_active = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=name, callback_data=f"vote_dep:{dep_id}")] 
                for dep_id, name in active_deps
            ]
        )
        await msg.answer("🗣 Ovoz bering:", reply_markup=kb_active)
    
    # Tugagan bo'limlar natijalari tugmasi
    if closed_deps:
        kb_closed = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=name, callback_data=f"results_dep:{dep_id}")] 
                for dep_id, name in closed_deps
            ]
        )
        await msg.answer("📊 Ovoz berish muddati tugagan bo‘limlar natijalari:", reply_markup=kb_closed)


# ==========================
# Nomzodlarni ko'rsatish
# ==========================
@router.callback_query(F.data.startswith("vote_dep:"))
async def show_candidates(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[1])
    candidates = await db.get_candidates(dep_id)
    if not candidates:
        await cb.message.answer("Hozircha nomzodlar mavjud emas.")
        return

    stats = await db.department_statistics(dep_id)
    text = f"📌 Bo'lim nomzodlari:\n\n"
    buttons = []

    for c in candidates:
        candidate_id, _, name, photo_id, video_id, caption = c
        votes = next((v[1] for v in stats if v[0] == name), 0)
        buttons.append([InlineKeyboardButton(text=f"{name}-🗳️{votes}", callback_data=f"vote:{candidate_id}:{dep_id}")])

    await cb.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# ==========================
# Ovoz berish
# ==========================
@router.callback_query(F.data.startswith("vote:"))
async def vote_candidate(cb: CallbackQuery, bot: Bot):
    # 1️⃣ Callback data dan idlarni olish
    try:
        _, candidate_id, dep_id = cb.data.split(":")
        candidate_id = int(candidate_id)
        dep_id = int(dep_id)
    except Exception:
        return await cb.answer("❌ Xatolik: noto‘g‘ri callback data", show_alert=True)

    user_id = cb.from_user.id

    # 2️⃣ Foydalanuvchini kutish xabari
    # await cb.answer("⏳ Tekshirilmoqda...")

    # 3️⃣ Majburiy kanallarni tekshirish
    channels = await db.get_channels()
    not_joined = []

    for ch in channels:
        if not await check_membership(bot, ch[3], user_id):
            not_joined.append(ch)

    if not_joined:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=ch[2], url=ch[3])] for ch in not_joined
            ] + [
                [InlineKeyboardButton(
                    text="✅ A’zo bo‘ldim",
                    url=f"https://t.me/{(await bot.me()).username}?start=vote_{candidate_id}_{dep_id}"
                )]
            ]
        )
        return await cb.message.answer(
            "❌ Ovoz berish uchun quyidagi kanallarga a’zo bo‘ling 👇",
            reply_markup=kb
        )

    # 4️⃣ Ovoz berish (1 user = 1 ovoz)
    success = await db.vote(user_id, dep_id, candidate_id)
    if not success:
        return await cb.answer("⚠️ Siz allaqachon ovoz bergansiz", show_alert=True)

    # 5️⃣ Kandidatlarni va statistikani olish
    candidates = await db.get_candidates(dep_id)
    stats = await db.department_statistics(dep_id)
    votes_map = {name: votes for name, votes in stats}

    candidates_stats = [
        (c[0], c[2], votes_map.get(c[2], 0)) for c in candidates
    ]

    # 6️⃣ Start page caption
    start_page = await db.get_start_page()
    if not start_page:
        return await cb.answer("❌ Start page topilmadi", show_alert=True)
    _, base_caption = start_page

    # 7️⃣ Yangi caption va keyboard
    new_caption, new_keyboard = build_department_post(
        dep_id=dep_id,
        base_caption=base_caption,
        candidates_stats=candidates_stats
    )

    # 8️⃣ Xabarni yangilash (photo yoki text)
    try:
        if cb.message.photo:  # agar photo bo'lsa
            await cb.message.edit_caption(caption=new_caption, reply_markup=new_keyboard)
        else:  # oddiy text message bo'lsa
            await cb.message.edit_text(text=new_caption, reply_markup=new_keyboard)
    except Exception as e:
        if "message is not modified" not in str(e):
            print("EDIT ERROR:", e)

    # 9️⃣ Yakuniy javob
    await cb.answer("✅ Siz muvaffaqiyatli ovoz berdingiz!", show_alert=True)


# ==========================
# Natijalar
# ==========================
async def show_results_button(msg: Message):
    deps = await db.get_departments()
    if not deps:
        await msg.answer("Hozircha bo‘limlar mavjud emas.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=d[1], callback_data=f"results_dep:{d[0]}")] for d in deps]
    )
    await msg.answer("Bo‘lim natijalarini ko‘rish:", reply_markup=kb)

@router.callback_query(F.data.startswith("results_dep:"))
async def results_dep(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[1])
    stats = await db.get_results(dep_id)

    if not stats:
        await cb.message.answer("Bu bo‘limda hali natijalar mavjud emas.")
        return

    text = "📊 Bo‘lim natijalari:\n\n"
    for r in stats:
        # tuple elementlarini xavfsiz olish
        if len(r) < 5:
            continue  # yoki xatolik xabarini yozish: continue yoki pass
        place = r[2]          # 2 = place
        candidate_id = r[3]   # 3 = candidate_id
        custom_name = r[4]    # 4 = custom_name

        if candidate_id:
            candidate = await db.get_candidate_by_id(candidate_id)
            if candidate:
                name = candidate[2]  # c[2] = name
            else:
                name = "Nomzod topilmadi"
        else:
            name = custom_name or "—"

        text += f"{place}-o‘rin: {name}\n"

    await cb.message.answer(text)


# ==========================
# Routerga qo'shish
# ==========================
def register_user_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)
