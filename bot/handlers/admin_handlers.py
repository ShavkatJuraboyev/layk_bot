import os
import requests
from aiogram import Router, F, types, Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
import database.db as db
from utils.auth import is_admin
from utils.membership import check_membership


router = Router()
TOKEN = "8393268918:AAG-b_DqY7AJnDVOhQIEL77wUp53n8vzldQ"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(BASE_DIR, "images", "sunny.jpg")
ADMIN_ID = 2004004762 
WEATHER_API_KEY = "e4016445b7fb35f0746afcc49c41a0ef"
CITY = "Samarqand"
API_URL = "https://student.samtuit.uz/rest/v1/data/employee-list?type=all"
API_TOKEN = "Y-R36P1BY-eLfuCwQbcbAlvt9GAMk-WP"
WEATHER_API_KEY_ONE = "65484c016bd4407dbff62042251009" 


class StartPageFSM(StatesGroup):
    photo = State()
    caption = State()

class ChannelFSM(StatesGroup):
    title = State()
    link = State()

class DepartmentFSM(StatesGroup):
    name = State()
    photo = State()

class CandidateFSM(StatesGroup):
    department = State()
    name = State()
    media = State()
    caption = State()
    edit_choice = State()
    edit_name = State()
    edit_media = State()
    edit_caption = State()

class ResultFSM(StatesGroup):
    department = State()
    place = State()
    custom = State()


# =====================================================
# ADMIN MENU
# =====================================================
@router.message(Command("admin"))
async def admin_menu(msg: Message):
    if not is_admin(msg.from_user.id):
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Start page", callback_data="admin_start")],
        [InlineKeyboardButton(text="📢 Kanallar", callback_data="admin_channels")],
        [InlineKeyboardButton(text="🏷 Bo‘limlar", callback_data="admin_departments")],
        [InlineKeyboardButton(text="👤 Nomzodlar", callback_data="admin_candidates")],
        [InlineKeyboardButton(text="🏆 Natijalar", callback_data="admin_results")],
    ])
    await msg.answer("🔐 Admin panel", reply_markup=kb)

# =====================================================
# START PAGE CRUD
# =====================================================
@router.callback_query(F.data == "admin_start")
async def start_page_menu(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Create / Update", callback_data="start_create")],
        [InlineKeyboardButton(text="👁 View", callback_data="start_view")],
        [InlineKeyboardButton(text="❌ Delete", callback_data="start_delete")],
    ])
    await cb.message.answer("Start page CRUD", reply_markup=kb)


@router.callback_query(F.data == "start_create")
async def start_create(cb: CallbackQuery, state: FSMContext):
    await state.set_state(StartPageFSM.photo)
    await cb.message.answer("Start uchun rasm yuboring:")


@router.message(StartPageFSM.photo)
async def start_photo(msg: Message, state: FSMContext):
    await state.update_data(photo=msg.photo[-1].file_id)
    await state.set_state(StartPageFSM.caption)
    await msg.answer("Caption yuboring:")


@router.message(StartPageFSM.caption)
async def start_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.create_start_page(data["photo"], msg.text)
    await state.clear()
    await msg.answer("✅ Start page saqlandi")


@router.callback_query(F.data == "start_view")
async def start_view(cb: CallbackQuery):
    data = await db.get_start_page()
    if not data:
        await cb.message.answer("Start page yo‘q")
        return
    await cb.message.answer_photo(data[0], caption=data[1])


@router.callback_query(F.data == "start_delete")
async def start_delete(cb: CallbackQuery):
    await db.delete_start_page()
    await cb.message.answer("🗑 O‘chirildi")


# =====================================================
# CHANNELS CRUD
# =====================================================
@router.callback_query(F.data == "admin_channels")
async def channels_menu(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add", callback_data="channel_add")],
        [InlineKeyboardButton(text="📋 List", callback_data="channel_list")],
    ])
    await cb.message.answer("Kanallar CRUD", reply_markup=kb)


@router.callback_query(F.data == "channel_add")
async def channel_add(cb: CallbackQuery, state: FSMContext):
    await state.set_state(ChannelFSM.title)
    await cb.message.answer("Kanal nomini yuboring:")


@router.message(ChannelFSM.title)
async def channel_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await state.set_state(ChannelFSM.link)
    await msg.answer("Kanal linkini yuboring:")


@router.message(ChannelFSM.link)
async def channel_link(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    link = msg.text.strip()
    
    chat_id = None  # default

    # Faqat public kanallar uchun chat_id olishga harakat qilamiz
    if link.startswith("https://t.me/"):
        username = link.split("https://t.me/")[-1].strip()
        try:
            chat = await bot.get_chat(username)
            chat_id = chat.id
        except Exception:
            chat_id = None  # private channel yoki bot kanalda emas

    # DB ga saqlaymiz, chat_id None bo‘lsa ham link orqali saqlaymiz
    await db.add_channel(chat_id, data["title"], link)

    if chat_id:
        await msg.answer(f"✅ Kanal qo‘shildi! Chat ID: `{chat_id}`", parse_mode="Markdown")
    else:
        await msg.answer(f"✅ Kanal qo‘shildi, lekin bot kanalga qo‘shilmagan yoki private kanal. Tekshirish ishlamaydi.", parse_mode="Markdown")

    await state.clear()


@router.callback_query(F.data == "channel_list")
async def channel_list(cb: CallbackQuery):
    channels = await db.get_channels()
    if not channels:
        await cb.message.answer("Kanal yo‘q")
        return

    for c in channels:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Delete", callback_data=f"channel_del:{c[0]}")]
        ])
        await cb.message.answer(f"{c[2]}\n{c[3]}", reply_markup=kb)


@router.callback_query(F.data.startswith("channel_del:"))
async def channel_delete(cb: CallbackQuery):
    cid = int(cb.data.split(":")[1])
    await db.delete_channel(cid)
    await cb.message.answer("🗑 Kanal o‘chirildi")


# =====================================================
# DEPARTMENTS CRUD
# =====================================================
@router.callback_query(F.data == "admin_departments")
async def department_menu(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add", callback_data="dep_add")],
        [InlineKeyboardButton(text="📋 List", callback_data="dep_list")],
    ])
    await cb.message.answer("Bo‘limlar CRUD", reply_markup=kb)


@router.callback_query(F.data == "dep_add")
async def dep_add(cb: CallbackQuery, state: FSMContext):
    await state.set_state(DepartmentFSM.name)
    await cb.message.answer("Bo‘lim nomi:")


@router.message(DepartmentFSM.name)
async def dep_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(DepartmentFSM.photo)
    await msg.answer("Bo‘lim rasmi yuboring:")


@router.message(DepartmentFSM.photo)
async def dep_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_department(data["name"], msg.photo[-1].file_id)
    await state.clear()
    await msg.answer("✅ Bo‘lim qo‘shildi")


@router.callback_query(F.data == "dep_list")
async def dep_list(cb: CallbackQuery):
    deps = await db.get_departments()
    for d in deps:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔒 Close" if d[3] else "🔓 Open",
                    callback_data=f"dep_toggle:{d[0]}:{d[3]}"
                ),
                InlineKeyboardButton(text="❌ Delete", callback_data=f"dep_del:{d[0]}")
            ]
        ])
        await cb.message.answer(f"{d[1]}", reply_markup=kb)


@router.callback_query(F.data.startswith("dep_toggle:"))
async def dep_toggle(cb: CallbackQuery):
    _, dep_id, status = cb.data.split(":")
    await db.set_department_status(int(dep_id), not bool(int(status)))
    await cb.message.answer("Status o‘zgartirildi")


@router.callback_query(F.data.startswith("dep_del:"))
async def dep_delete(cb: CallbackQuery):
    dep_id = int(cb.data.split(":")[1])
    await db.delete_department(dep_id)
    await cb.message.answer("🗑 Bo‘lim o‘chirildi")


# ======================================================
# SHOW DEPARTMENTS
# ======================================================
@router.callback_query(F.data == "admin_candidates")
async def candidates_menu(cb: CallbackQuery):
    deps = await db.get_departments(False)
    if not deps:
        await cb.message.answer("Bo‘limlar mavjud emas.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=d[1], callback_data=f"cand_dep:{d[0]}")] for d in deps]
    )
    await cb.message.answer("Bo‘lim tanlang:", reply_markup=kb)


# ======================================================
# SHOW CANDIDATES IN DEPARTMENT
# ======================================================
@router.callback_query(F.data.startswith("cand_dep:"))
async def cand_dep(cb: CallbackQuery, state: FSMContext):
    dep_id = int(cb.data.split(":")[1])
    await state.update_data(dep_id=dep_id)

    candidates = await db.get_candidates(dep_id)
    btn = [[InlineKeyboardButton(
            text="➕ Yangi Nomzod qo‘shish",
            callback_data="cand_add"
        )]]
    if not candidates:
        await cb.message.answer("⚠️ Bu bo‘limda nomzodlar mavjud emas.", reply_markup=InlineKeyboardMarkup(inline_keyboard=btn))
        return

    stats = await db.department_statistics(dep_id)
    votes_map = {name: votes for name, votes in stats}

    buttons = []
    for c in candidates:
        candidate_id = c[0]
        name = c[2]

        votes = votes_map.get(name, 0)

        buttons.append([
            InlineKeyboardButton(
                text=f"{name} ({votes} ovoz)",
                callback_data=f"vote:{candidate_id}:{dep_id}"
            )
        ])

    buttons.append([InlineKeyboardButton(
        text="➕ Yangi Nomzod qo‘shish",
        callback_data="cand_add"
    )])

    buttons.append([InlineKeyboardButton(
        text="📤 Nomzodlarni yuborish",
        callback_data=f"send_dep:{dep_id}"
    )])

    await cb.message.answer(
        "Nomzodlar ro‘yxati:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


# ======================================================
# ADD NEW CANDIDATE
# ======================================================
@router.callback_query(F.data == "cand_add")
async def add_candidate_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CandidateFSM.name)
    await cb.message.answer("Nomzod ismi:")


@router.message(CandidateFSM.name)
async def cand_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(CandidateFSM.media)
    await msg.answer("Rasm yoki video yuboring (ixtiyoriy, o‘tkazib yuborish uchun /skip):")


@router.message(CandidateFSM.media)
async def cand_media(msg: Message, state: FSMContext):
    data = await state.get_data()
    photo = msg.photo[-1].file_id if msg.photo else None
    video = msg.video.file_id if msg.video else None
    await state.update_data(photo=photo, video=video)
    await state.set_state(CandidateFSM.caption)
    await msg.answer("Caption kiriting (ixtiyoriy, o‘tkazib yuborish uchun /skip):")


# Skip media handler
@router.message(F.text == "/skip", StateFilter(CandidateFSM.media))
async def skip_media(msg: Message, state: FSMContext):
    await state.update_data(photo=None, video=None)
    await state.set_state(CandidateFSM.caption)
    await msg.answer("Caption kiriting (ixtiyoriy, o‘tkazib yuborish uchun /skip):")

# Skip caption handler
@router.message(F.text == "/skip", StateFilter(CandidateFSM.caption))
async def skip_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_candidate(data["dep_id"], data["name"], data.get("photo"), data.get("video"), None)
    await state.clear()
    await msg.answer("✅ Nomzod qo‘shildi")



@router.message(CandidateFSM.caption)
async def add_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_candidate(data["dep_id"], data["name"], data.get("photo"), data.get("video"), msg.text)
    await state.clear()
    await msg.answer("✅ Nomzod qo‘shildi")


# ======================================================
# VIEW / EDIT / DELETE CANDIDATE
# ======================================================
@router.callback_query(F.data.startswith("cand_view:"))
async def view_candidate(cb: CallbackQuery, state: FSMContext):
    cand_id = int(cb.data.split(":")[1])
    candidate = await db.get_candidate_by_id(cand_id)

    if not candidate:
        await cb.message.answer("Nomzod topilmadi.")
        return

    # Media yuborish (ixtiyoriy)
    if candidate[3]:  # photo_id
        await cb.message.answer_photo(candidate[3], caption=candidate[5] or candidate[2])
    elif candidate[4]:  # video_id
        await cb.message.answer_video(candidate[4], caption=candidate[5] or candidate[2])
    else:
        # Hech qanday media yo'q bo'lsa, faqat caption yoki ismni yuboramiz
        await cb.message.answer(candidate[5] or candidate[2])

    # Edit / Delete tugmalari
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[  # list ichida list bo'lishi shart
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"cand_edit:{cand_id}"),
            InlineKeyboardButton(text="🗑️ O‘chirish", callback_data=f"cand_delete:{cand_id}")
        ]]
    )
    await cb.message.answer("Tanlang:", reply_markup=kb)



# ======================================================
# DELETE CANDIDATE
# ======================================================
@router.callback_query(F.data.startswith("cand_delete:"))
async def delete_candidate_cb(cb: CallbackQuery):
    cand_id = int(cb.data.split(":")[1])
    await db.delete_candidate(cand_id)
    await cb.message.answer("✅ Nomzod o‘chirildi")


# ======================================================
# EDIT CANDIDATE MENU
# ======================================================
@router.callback_query(F.data.startswith("cand_edit:"))
async def edit_candidate_start(cb: CallbackQuery, state: FSMContext):
    cand_id = int(cb.data.split(":")[1])
    await state.update_data(cand_id=cand_id)
    await state.set_state(CandidateFSM.edit_choice)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ismni tahrirlash", callback_data="edit_name")],
            [InlineKeyboardButton(text="Media tahrirlash", callback_data="edit_media")],
            [InlineKeyboardButton(text="Caption tahrirlash", callback_data="edit_caption")]
        ]
    )
    await cb.message.answer("Nimani tahrirlashni xohlaysiz?", reply_markup=kb)


@router.callback_query(F.data.startswith("edit_"))
async def edit_choice(cb: CallbackQuery, state: FSMContext):
    choice = cb.data.split("_")[1]
    await state.update_data(edit_field=choice)

    if choice == "name":
        await state.set_state(CandidateFSM.edit_name)
        await cb.message.answer("Yangi ismni kiriting:")
    elif choice == "media":
        await state.set_state(CandidateFSM.edit_media)
        await cb.message.answer("Yangi rasm yoki video yuboring (ixtiyoriy, /skip):")
    elif choice == "caption":
        await state.set_state(CandidateFSM.edit_caption)
        await cb.message.answer("Yangi caption kiriting (ixtiyoriy, /skip):")


# ================== EDIT HANDLERS ==================
@router.message(CandidateFSM.edit_name)
async def edit_name(msg: Message, state: FSMContext):
    data = await state.get_data()
    # faqat ism o'zgartirish, media va caption eski qoladi
    await db.update_candidate(data["cand_id"], msg.text, None, None, None, update_only_name=True)
    await state.clear()
    await msg.answer("✅ Ism tahrirlandi")


@router.message(CandidateFSM.edit_media)
async def edit_media(msg: Message, state: FSMContext):
    data = await state.get_data()
    photo = msg.photo[-1].file_id if msg.photo else None
    video = msg.video.file_id if msg.video else None
    await db.update_candidate(data["cand_id"], None, photo, video, None, update_only_media=True)
    await state.clear()
    await msg.answer("✅ Media tahrirlandi")


@router.message(CandidateFSM.edit_caption)
async def edit_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_candidate(data["cand_id"], None, None, None, msg.text, update_only_caption=True)
    await state.clear()
    await msg.answer("✅ Caption tahrirlandi")


# ================== SKIP HANDLERS ==================
@router.message(F.text == "/skip", StateFilter(CandidateFSM.edit_media))
async def skip_edit_media(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("✅ Media tahrirlandi (o‘zgarmadi)")

@router.message(F.text == "/skip", StateFilter(CandidateFSM.edit_caption))
async def skip_edit_caption(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("✅ Caption tahrirlandi (o‘zgarmadi)")



# =====================================================
# RESULTS CRUD (QO‘LDA)
# =====================================================
@router.callback_query(F.data == "admin_results")
async def admin_results_menu(cb: CallbackQuery):
    deps = await db.get_departments()
    if not deps:
        await cb.message.answer("⚠️ Hozircha bo‘limlar mavjud emas.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d[1], callback_data=f"admin_dep:{d[0]}")] 
            for d in deps
        ]
    )
    await cb.message.answer("Bo‘lim tanlang:", reply_markup=kb)


@router.callback_query(F.data.startswith("admin_dep:"))
async def admin_dep(cb: CallbackQuery, state: FSMContext):
    dep_id = int(cb.data.split(":")[1])
    await state.update_data(dep_id=dep_id)

    # Shu bo‘limdagi nomzodlar
    candidates = await db.get_candidates(dep_id)
    if not candidates:
        await cb.message.answer("Bu bo‘limda nomzodlar mavjud emas.")
        return

    # Bo‘lim statistikasini olish
    stats = await db.department_statistics(dep_id)
    votes_dict = {name: votes for name, votes in stats}  # {nomzod_nomi: ovoz_soni}

    kb_buttons = []
    text_lines = []

    for c in candidates:
        candidate_id = c[0]
        name = c[2]
        votes = votes_dict.get(name, 0)
        text_lines.append(f"👤 {name} - 🗳️ {votes} ovoz")
        kb_buttons.append([InlineKeyboardButton(text=f"{name} ({votes} ovoz)", callback_data=f"admin_candidate:{candidate_id}")])

    await cb.message.answer(
        "Nomzod tanlang:\n\n" + "\n".join(text_lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    )



@router.callback_query(F.data.startswith("admin_candidate:"))
async def admin_candidate(cb: CallbackQuery, state: FSMContext):
    candidate_id = int(cb.data.split(":")[1])
    await state.update_data(candidate_id=candidate_id)

    # 1 / 2 / 3 o‘rin tugmalari
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1️⃣", callback_data="set_place:1"),
                InlineKeyboardButton(text="2️⃣", callback_data="set_place:2"),
                InlineKeyboardButton(text="3️⃣", callback_data="set_place:3")
            ]
        ]
    )
    await cb.message.answer("O‘rin tanlang:", reply_markup=kb)

@router.callback_query(F.data.startswith("set_place:"))
async def set_place(cb: CallbackQuery, state: FSMContext):
    place = int(cb.data.split(":")[1])
    data = await state.get_data()
    dep_id = data.get("dep_id")
    candidate_id = data.get("candidate_id")

    if not dep_id or not candidate_id:
        await cb.message.answer("⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko‘ring.")
        await state.clear()
        return

    # Natijani saqlash
    await db.add_result(dep_id, place, candidate_id=candidate_id, custom_name=None)

    # Nomzod ismini olish
    candidate = await db.get_candidate_by_id(candidate_id)
    candidate_name = candidate[2] if candidate else "Nomzod topilmadi"

    await state.clear()
    await cb.message.answer(f"🏆 Natija saqlandi: {place}-o‘rin → {candidate_name}")




# -------------------------
# 2️⃣ Admin botga yuboradi (preview)
# -------------------------
def build_department_post(dep_id, base_caption, candidates_stats):
    """
    candidates_stats: [(candidate_id, name, votes), ...]
    """

    text = base_caption + "\n\n<b>🗳 NOMZODLAR:</b>\n"

    keyboard = []

    for i, (candidate_id, name, votes) in enumerate(candidates_stats, start=1):
        keyboard.append([
            InlineKeyboardButton(
                text=f"🗳 {name} ({votes})",
                callback_data=f"vote:{candidate_id}:{dep_id}"
            )
        ])

    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data.startswith("send_dep:"))
async def send_dep_preview(cb: CallbackQuery, bot: Bot):
    dep_id = int(cb.data.split(":")[1])

    candidates = await db.get_candidates(dep_id)
    if not candidates:
        return await cb.message.answer("⚠️ Bu bo‘limda nomzodlar mavjud emas.")

    # 1️⃣ Start page dan rasm va caption
    start_page = await db.get_start_page()
    if not start_page:
        return await cb.message.answer("❌ Start page topilmadi")

    photo_id, base_caption = start_page

    # 2️⃣ Ovozlar statistikasi
    stats = await db.department_statistics(dep_id)
    votes_map = {name: votes for name, votes in stats}

    # 3️⃣ Nomzodlarni yig‘amiz
    candidates_stats = []
    for c in candidates:
        candidate_id = c[0]
        name = c[2]
        votes = votes_map.get(name, 0)
        candidates_stats.append((candidate_id, name, votes))

    # 4️⃣ Bitta post yasaymiz
    caption, keyboard = build_department_post(
        dep_id=dep_id,
        base_caption=base_caption,
        candidates_stats=candidates_stats
    )

    # 5️⃣ Preview yuboramiz (BITTA POST)
    await cb.message.answer_photo(
        photo=photo_id,
        caption=caption,
        reply_markup=keyboard
    )

    # 6️⃣ Kanalga yuborish tugmasi
    await cb.message.answer(
        "Nomzodlarni kanalga yuborasizmi?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="📢 Kanalga yuborish",
                    callback_data=f"send_channel:{dep_id}"
                )]
            ]
        )
    )


@router.callback_query(F.data.startswith("send_channel:"))
async def send_channel(cb: CallbackQuery, bot: Bot):
    dep_id = int(cb.data.split(":")[1])

    candidates = await db.get_candidates(dep_id)
    if not candidates:
        return await cb.answer("❌ Nomzodlar yo‘q", show_alert=True)

    # 1️⃣ Start page (rasm + umumiy caption)
    start_page = await db.get_start_page()
    if not start_page:
        return await cb.answer("❌ Start page topilmadi", show_alert=True)

    photo_id, base_caption = start_page

    # 2️⃣ Ovozlar statistikasi
    stats = await db.department_statistics(dep_id)
    votes_map = {name: votes for name, votes in stats}

    # 3️⃣ Nomzodlarni yig‘amiz
    candidates_stats = []
    for c in candidates:
        candidate_id = c[0]
        name = c[2]
        votes = votes_map.get(name, 0)
        candidates_stats.append((candidate_id, name, votes))

    # 4️⃣ Bitta post yasaymiz (OLDINGI FUNKSIYA)
    caption, keyboard = build_department_post(
        dep_id=dep_id,
        base_caption=base_caption,
        candidates_stats=candidates_stats
    )

    # 5️⃣ HAR BIR KANALGA BITTA POST
    
    chat_id = '@tatusfyoshlarittifoqi'

    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo_id,
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"❌ Kanalga yuborilmadi ({chat_id}):", e)

    await cb.answer("✅ Nomzodlar kanalga yuborildi", show_alert=True)


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



def fetch_employees():
    all_employees = []

    for i in range(1, 23):  # 22 ta sahifa bor
        API_URL = f"https://student.samtuit.uz/rest/v1/data/employee-list?type=all&page={i}"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        res = requests.get(API_URL, headers=headers).json()
        data = res.get("data", {})

        if isinstance(data, dict):
            items = data.get("items", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        all_employees.extend(items)
    return all_employees

def get_daily_average_weatherapi(city="Samarqand"):
    url = "http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": WEATHER_API_KEY_ONE,
        "q": city,
        "days": 1,
        "aqi": "no",
        "alerts": "no"
    }
    resp = requests.get(url, params=params, timeout=10).json()

    location = resp["location"]["name"]
    country = resp["location"]["country"]
    forecast = resp["forecast"]["forecastday"][0]["day"]

    avg_temp = forecast["avgtemp_c"]
    max_temp = forecast["maxtemp_c"]
    min_temp = forecast["mintemp_c"]
    condition = forecast["condition"]["text"]
    humidity = forecast["avghumidity"]

    # Inglizcha → O‘zbekcha tarjima
    condition_translations = {
        "Sunny": "Quyoshli",
        "Clear": "Ochiq osmon",
        "Partly cloudy": "Qisman bulutli",
        "Cloudy": "Bulutli",
        "Overcast": "Qorong‘u osmon",
        "Mist": "Tumanli",
        "Fog": "Tuman",
        "Rain": "Yomg‘ir",
        "Light rain": "Yengil yomg‘ir",
        "Moderate rain": "O‘rtacha yomg‘ir",
        "Heavy rain": "Kuchli yomg‘ir",
        "Snow": "Qor",
        "Light snow": "Yengil qor",
        "Heavy snow": "Kuchli qor",
        "Thunderstorm": "Momaqaldiroq",
        "Drizzle": "Mayda yomg‘ir"
    }

    condition_uz = condition_translations.get(condition, condition)

    # Ob-havo rasmlari mapping
    weather_images = {
        "Sunny": "https://storage.kun.uz/source/4/DPWlLu11G2SPAPOSmw9FCWO687nVy6NL.jpg",
        "Clear": "https://storage.kun.uz/source/4/DPWlLu11G2SPAPOSmw9FCWO687nVy6NL.jpg",
        "Partly cloudy": "https://files.modern.az/articles/2025/03/30/1743323387_ebd5d6e7-475f-3fd9-9260-783bf53486ea_850.jpg",
        "Cloudy": "https://files.modern.az/articles/2025/03/30/1743323387_ebd5d6e7-475f-3fd9-9260-783bf53486ea_850.jpg",
        "Overcast": "https://files.modern.az/articles/2025/03/30/1743323387_ebd5d6e7-475f-3fd9-9260-783bf53486ea_850.jpg",
        "Rain": "https://i.ytimg.com/vi/7brJCPOkfuQ/maxresdefault.jpg",
        "Light rain": "https://i.ytimg.com/vi/7brJCPOkfuQ/maxresdefault.jpg",
        "Moderate rain": "https://i.ytimg.com/vi/7brJCPOkfuQ/maxresdefault.jpg",
        "Snow": "https://pic.rutubelist.ru/video/2024-12-21/64/41/6441c162f6f67d0bb3a69ab136527cc0.jpg",
        "Thunderstorm": "https://www.wwlp.com/wp-content/uploads/sites/26/2025/06/Getty-Thunderstorm.jpg?w=1280",
    }

    # Agar condition mappingda bo‘lmasa → default rasm
    image_url = weather_images.get(condition, "https://files.modern.az/articles/2025/03/30/1743323387_ebd5d6e7-475f-3fd9-9260-783bf53486ea_850.jpg")

    # Chiroyli caption (uzbekcha holat bilan)
    caption = (
        "<b>OB➖HOVO</b>\n\n"
        "🌐 <b>TATU Samarqand filiali axborot xizmati</b>\n\n"
        f"📍 <b>{location}, {country}</b>\n"
        f"📅 <i>{datetime.now().strftime('%d-%m-%Y')}</i>\n\n"
        f"🌡️ <b>O'rtacha: {avg_temp}°C</b>\n"
        f"⬆️ Maks: {max_temp}°C   ⬇️ Min: {min_temp}°C\n"
        f"☁️ Holat: <b>{condition_uz}</b>\n"
        f"💧 Namlik: {humidity}%\n\n"
        "Bizni kuzating👇\n"
        "<a href='https://fb.com/sbtuit'>Facebook</a> | "
        "<a href='https://t.me/sbtuit2005'>Telegram</a> | "
        "<a href='https://instagram.com/sbtuit2005'>Instagram</a> | "
        "<a href='https://bit.ly/2yw9MS9'>YouTube</a>\n"
    )

    return caption, image_url

# 🎂 Tug‘ilgan kunlarni tekshirish (bugun va ertaga)
def get_birthdays():
    employees = fetch_employees()
    today = datetime.now().strftime("%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m-%d")

    birthdays_today, birthdays_tomorrow = [], []

    for emp in employees:
        try:
            # Tug‘ilgan sanani timestampdan datetime ga aylantiramiz
            timestamp = emp["birth_date"]
            if timestamp > 1e12:
                timestamp = timestamp/1000

            birth_date = datetime.fromtimestamp(timestamp)
            birth_md = birth_date.strftime("%m-%d")  # faqat oy-kun

            info = {
                    "full_name": emp["full_name"],
                    "department": emp["department"]["name"] if emp.get("department") else "",
                    "kafedra": emp["structureType"]["name"] if emp.get("kafedra") else "",
                    "birth_date": birth_date.strftime("%Y-%m-%d"),  # to‘liq sana
                    "image": emp.get("image")
            }

            if birth_md == today:
                birthdays_today.append(info)
            elif birth_md == tomorrow:
                birthdays_tomorrow.append(info)

        except Exception as e:
            pass

    return birthdays_today, birthdays_tomorrow

# 📤 Adminni tug‘ilgan kunlar bilan ogohlantirish
async def send_birthday_notifications():
    birthdays_today, birthdays_tomorrow = get_birthdays()
    
    if birthdays_today:
        for emp in birthdays_today:
            full_name = emp["full_name"]
            department = emp["department"]
            kafedra = emp["kafedra"]

            caption = f"""
            Bugun"{department}" {kafedra} xodimi <i>{full_name}</i>ning tavallud ayyomi.\n\n <i>Hurmatli {full_name}</i>\nSizga filial jamoasi nomidan sihat-salomatlik, oilaviy xotirjamlik, ishlaringizda ulkan muvaffaqiyatlar tilab qolamiz!\n\n🌐 <b>TATU Samarqand filiali axborot xizmati</b>\n\n\nBizni kuzating👇🏼\n <a href="https://fb.com/sbtuit">Facebook</a> | <a href="https://t.me/sbtuit2005">Telegram</a> | <a href="https://instagram.com/sbtuit2005">Instagram</a> | <a href="https://bit.ly/2yw9MS9">YouTube</a>"""

            if emp.get("image"):
                await bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=emp["image"],  # URL bo‘lsa to‘g‘ridan-to‘g‘ri
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=caption,
                    parse_mode="HTML"
                )

    if birthdays_tomorrow:
        msg = "📌 <b>Ertaga tug‘ilgan kunlar:</b>\n\n"
        for emp in birthdays_tomorrow:
            msg += f"👤 {emp['full_name']}\n🏢 {emp['department']}\n\n"
        await bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="HTML")

    if not birthdays_today and not birthdays_tomorrow:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text="❌ Bugun va ertaga tug‘ilgan kun yo‘q.",
            parse_mode="HTML"
        )

async def obhavo_command_telegram():
    caption, image_url = get_daily_average_weatherapi("Samarqand")
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=image_url,   # ob-havoga mos rasm
        caption=caption,
        parse_mode="HTML"
    )

@router.message(F.text == "/obhavo_api")
async def obhavo_command(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return
    caption, image_url = get_daily_average_weatherapi("Samarqand")
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=image_url,   # ob-havoga mos rasm
        caption=caption,
        parse_mode="HTML"
    )

# === /test komandasi ===
@router.message(F.text == "/test")
async def test_command(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return
    if str(message.from_user.id) != str(ADMIN_ID):
        return await message.answer("⛔ Bu buyruq faqat admin uchun!")

    await message.answer("⏳ Test boshlanmoqda...")
    await send_birthday_notifications()
    await message.answer("✅ Test tugadi.")

# Router yordamida handlerlarni ro'yxatga olish
def register_admin_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish