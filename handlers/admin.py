import asyncio
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_PASSWORD, INITIAL_ADMINS
from database import db
from keyboards import (
    admin_menu, cancel_kb, user_menu, get_delete_confirm_kb,
    channels_admin_keyboard, skip_media_kb, channel_post_movies_keyboard,
    confirm_channel_post_send_keyboard, channel_watch_button
)

admin_router = Router()

# FSM holatlari
class AdminLoginState(StatesGroup):
    waiting_for_password = State()

class ChangePasswordState(StatesGroup):
    waiting_for_new_password = State()

class AddMovieState(StatesGroup):
    waiting_for_media = State()
    waiting_for_code = State()

class DeleteMovieState(StatesGroup):
    waiting_for_code = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

class AddChannelStates(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_channel_name = State()
    waiting_for_channel_link = State()

class ChannelPostStates(StatesGroup):
    waiting_for_media = State()
    waiting_for_text = State()
    confirm_post = State()


def is_user_admin(user_id: int) -> bool:
    if user_id in INITIAL_ADMINS or db.is_admin(user_id):
        return True
    return False

# Bekor qilish tugmasi uchun handler
@admin_router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    if is_user_admin(message.from_user.id):
        await message.answer("❌ Harakat bekor qilindi.", reply_markup=admin_menu)
    else:
        await message.answer("❌ Harakat bekor qilindi.", reply_markup=user_menu)

# /admin BUYRUG'I
@admin_router.message(Command("admin"))
async def admin_entry_handler(message: types.Message, state: FSMContext):
    # Agar allaqachon admin bo'lsa
    if is_user_admin(message.from_user.id):
        await state.clear()
        await message.answer("🛠 <b>Admin paneliga xush kelibsiz!</b>\nKerakli bo'limni tanlang:", reply_markup=admin_menu, parse_mode="HTML")
    else:
        # Begonalar uchun hech narsa ko'rsatmaymiz
        await message.answer("⛔️ Siz administrator emassiz!", reply_markup=user_menu)

# To'g'ridan-to'g'ri /davlat20102412 buyrug'i yoki matni orqali admin bo'lish
@admin_router.message(Command("davlat20102412"))
@admin_router.message(F.text.casefold().in_(["/davlat20102412", "davlat20102412"]))
async def direct_davlat20102412_handler(message: types.Message, state: FSMContext):
    await state.clear()
    db.add_admin(message.from_user.id)
    await message.answer(
        "🎉 <b>Admin paroli to'g'ri!</b>\n\n"
        "Siz muvaffaqiyatli Administrator bo'ldingiz.\nAdmin panelidan foydalanishingiz mumkin:",
        reply_markup=admin_menu,
        parse_mode="HTML"
    )

# Maxfiy kodni tekshirish
@admin_router.message(AdminLoginState.waiting_for_password)
async def check_admin_password(message: types.Message, state: FSMContext):
    entered = message.text.strip().lower()
    current_password = db.get_admin_password().lower()

    valid_passwords = [
        current_password,
        current_password.lstrip("/"),
        "/" + current_password.lstrip("/"),
        "davlat20102412",
        "/davlat20102412"
    ]

    if entered in valid_passwords:
        db.add_admin(message.from_user.id)
        await state.clear()
        await message.answer(
            "🎉 <b>Muvaffaqiyatli kirdingiz!</b>\n\n"
            "Siz admin bo'ldingiz. Endi kinolarni yuklashingiz, o'chirishingiz va botni boshqarishingiz mumkin:",
            reply_markup=admin_menu,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>Maxfiy kod noto'g'ri!</b>\n\nQaytadan urinib ko'ring yoki bekor qiling:",
            reply_markup=cancel_kb,
            parse_mode="HTML"
        )

# /setadmin buyrug'i orqali ham to'g'ridan-to'g'ri kirish
@admin_router.message(Command("setadmin"))
async def set_admin_handler(message: types.Message):
    args = message.text.split(maxsplit=1)
    current_password = db.get_admin_password()

    if len(args) < 2:
        await message.answer(f"⚠️ Parolni ham kiriting!\nFormat: `/setadmin <parol>`", parse_mode="Markdown")
        return

    password = args[1].strip()
    if password == current_password or password == ADMIN_PASSWORD:
        db.add_admin(message.from_user.id)
        await message.answer("🎉 Tabriklaymiz! Siz muvaffaqiyatli Administrator bo'ldingiz.\nAdmin panelidan foydalanishingiz mumkin:", reply_markup=admin_menu)
    else:
        await message.answer("❌ Maxfiy parol noto'g'ri!")

# 🔑 ADMIN KODINI KO'RISH VA O'ZGARTIRISH
@admin_router.message(F.text == "🔑 Admin kodi")
async def show_change_admin_key(message: types.Message, state: FSMContext):
    if not is_user_admin(message.from_user.id):
        return

    current_password = db.get_admin_password()
    await state.set_state(ChangePasswordState.waiting_for_new_password)
    await message.answer(
        f"🔑 <b>Hozirgi Admin kodi:</b> <code>{current_password}</code>\n\n"
        f"💡 Yangi adminlar ushbu kodni botga yozib admin panelga kira oladilar.\n\n"
        f"Agar yangi kod o'rnatmoqchi bo'lsangiz, <b>yangi kodni yozing:</b>\n"
        f"(O'zgarishsiz qoldirish uchun ❌ Bekor qilish tugmasini bosing)",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )

@admin_router.message(ChangePasswordState.waiting_for_new_password)
async def process_new_admin_key(message: types.Message, state: FSMContext):
    new_code = message.text.strip()
    if not new_code or len(new_code) < 2:
        await message.answer("⚠️ Kod juda qisqa. Qaytadan kiriting:")
        return

    db.set_admin_password(new_code)
    await state.clear()
    await message.answer(
        f"✅ <b>Admin kodi muvaffaqiyatli yangilandi!</b>\n\n"
        f"Yangi kod: <code>{new_code}</code>\n\n"
        f"Endi boshqa foydalanuvchilar <code>{new_code}</code> kodi orqali admin bo'la oladilar.",
        reply_markup=admin_menu,
        parse_mode="HTML"
    )

# Foydalanuvchi rejimiga o'tish
@admin_router.message(F.text == "🚪 Foydalanuvchi rejimi")
async def exit_admin_mode(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👤 Siz foydalanuvchi rejimiga o'tdingiz.\nKino kodini yuborib kinoni topishingiz mumkin.", reply_markup=user_menu)

# 1. KINO YUKLASH / SAQLASH
@admin_router.message(F.text == "🎬 Kino yuklash / saqlash")
async def start_add_movie(message: types.Message, state: FSMContext):
    if not is_user_admin(message.from_user.id):
        return
    await state.set_state(AddMovieState.waiting_for_media)
    await message.answer("🎬 <b>Kino faylini (video yoki hujjat sifatida) yuboring:</b>\n\nBekor qilish uchun pastdagi tugmani bosing.", reply_markup=cancel_kb, parse_mode="HTML")

@admin_router.message(AddMovieState.waiting_for_media)
async def process_movie_media(message: types.Message, state: FSMContext):
    file_id = None
    file_type = "video"
    caption = message.caption or ""

    if message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.animation:
        file_id = message.animation.file_id
        file_type = "animation"
    else:
        await message.answer("⚠️ Iltimos, video yoki kino fayli yuboring!")
        return

    # Holatga ma'lumotlarni saqlaymiz
    await state.update_data(file_id=file_id, file_type=file_type, caption=caption)
    await state.set_state(AddMovieState.waiting_for_code)
    await message.answer("✅ Kino qabul qilindi!\n\n🔢 <b>Endi bu kino uchun KOD kiriting:</b>\n(Masalan: <code>15</code>, <code>204</code> yoki <code>avatar</code>)", reply_markup=cancel_kb, parse_mode="HTML")

@admin_router.message(AddMovieState.waiting_for_code)
async def process_movie_code(message: types.Message, state: FSMContext):
    code = message.text.strip().lower()
    if not code:
        await message.answer("⚠️ Kod bo'sh bo'lishi mumkin emas. Qaytadan kiriting:")
        return

    data = await state.get_data()
    file_id = data.get("file_id")
    file_type = data.get("file_type")
    caption = data.get("caption")

    success = db.add_movie(code=code, file_id=file_id, file_type=file_type, caption=caption)
    await state.clear()

    if success:
        await message.answer(
            f"🎉 <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            f"🔑 <b>Kino kodi:</b> <code>{code}</code>\n\n"
            f"Endi foydalanuvchilar botga <code>{code}</code> deb yozsa, ushbu kino yuboriladi.",
            reply_markup=admin_menu,
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Xatolik yuz berdi. Kino saqlanmadi.", reply_markup=admin_menu)

# 2. KINO O'CHIRISH
@admin_router.message(F.text == "🗑 Kino o'chirish")
async def start_delete_movie(message: types.Message, state: FSMContext):
    if not is_user_admin(message.from_user.id):
        return
    await state.set_state(DeleteMovieState.waiting_for_code)
    await message.answer("🗑 <b>O'chirmoqchi bo'lgan kino kodini yozing:</b>", reply_markup=cancel_kb, parse_mode="HTML")

@admin_router.message(DeleteMovieState.waiting_for_code)
async def process_delete_movie(message: types.Message, state: FSMContext):
    code = message.text.strip().lower()
    movie = db.get_movie(code)
    if not movie:
        await message.answer(f"⚠️ <code>{code}</code> kodli kino topilmadi!", reply_markup=admin_menu, parse_mode="HTML")
        await state.clear()
        return

    # Tasdiqlash
    await state.clear()
    await message.answer(
        f"❓ <b>Haqiqatan ham {code} kodli kinoni o'chirmoqchimisiz?</b>",
        reply_markup=get_delete_confirm_kb(code),
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data.startswith("del_yes_"))
async def confirm_delete_callback(call: types.CallbackQuery):
    code = call.data.replace("del_yes_", "")
    if db.delete_movie(code):
        await call.message.edit_text(f"✅ <b>{code}</b> kodli kino bazadan o'chirildi!", parse_mode="HTML")
    else:
        await call.message.edit_text("❌ Kino topilmadi yoki allaqachon o'chirilgan.")
    await call.answer()

@admin_router.callback_query(F.data == "del_no")
async def cancel_delete_callback(call: types.CallbackQuery):
    await call.message.edit_text("❌ O'chirish bekor qilindi.")
    await call.answer()

# 3. KINOLAR RO'YXATI
@admin_router.message(F.text == "📋 Kinolar ro'yxati")
async def list_movies(message: types.Message):
    if not is_user_admin(message.from_user.id):
        return
    movies = db.get_recent_movies(limit=20)
    total_count = db.get_movies_count()

    if not movies:
        await message.answer("📭 Hozircha bazada hech qanday kino yo'q.", reply_markup=admin_menu)
        return

    text = f"📋 <b>Bazada jami {total_count} ta kino mavjud.</b>\n\n<b>Oxirgi qo'shilganlar:</b>\n"
    for i, m in enumerate(movies, 1):
        caption_preview = (m['caption'][:30] + '...') if m['caption'] else "Tavsifsiz"
        text += f"{i}. Kod: <code>{m['code']}</code> | 👁 Ko'rishlar: {m['views']} | 📝 {caption_preview}\n"

    await message.answer(text, reply_markup=admin_menu, parse_mode="HTML")

# 4. STATISTIKA
@admin_router.message(F.text == "📊 Statistika")
async def show_statistics(message: types.Message):
    if not is_user_admin(message.from_user.id):
        return
    users_count = db.get_users_count()
    movies_count = db.get_movies_count()

    text = (
        f"📊 <b>Bot statistikasi:</b>\n\n"
        f"👥 Foydalanuvchilar soni: <b>{users_count} ta</b>\n"
        f"🎬 Yuklangan kinolar soni: <b>{movies_count} ta</b>\n"
    )
    await message.answer(text, reply_markup=admin_menu, parse_mode="HTML")

# 5. BARCHAGA XABAR YUBORISH (BROADCAST)
@admin_router.message(F.text == "📢 Barchaga xabar yuborish")
async def start_broadcast(message: types.Message, state: FSMContext):
    if not is_user_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer(
        "📢 <b>Barcha bot foydalanuvchilariga yubormoqchi bo'lgan xabaringizni yuboring:</b>\n"
        "(Bu matn, rasm, video, audio yoki post bo'lishi mumkin)",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )

@admin_router.message(BroadcastState.waiting_for_message)
async def process_broadcast(message: types.Message, state: FSMContext):
    users = db.get_all_users()
    await state.clear()
    status_msg = await message.answer(f"⏳ Xabar tarqatilmoqda... (Jami: {len(users)} ta foydalanuvchi)", reply_markup=admin_menu)

    success_count = 0
    blocked_count = 0

    for user_id in users:
        try:
            await message.copy_to(chat_id=user_id)
            success_count += 1
            await asyncio.sleep(0.04) # Telegram cheklovlariga tushmaslik uchun
        except Exception:
            blocked_count += 1

    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"📬 Yetkazildi: {success_count} ta\n"
        f"🚫 Yetkazilmadi (bloklangan): {blocked_count} ta",
        parse_mode="HTML"
    )

# 6. MAJBURIY KANALLARNI BOSHQARISH
@admin_router.message(F.text == "📢 Kanallarni boshqarish")
async def manage_channels_menu(message: types.Message):
    if not is_user_admin(message.from_user.id):
        return

    channels = db.get_all_channels()
    text = "📢 <b>Majburiy kanallar ro'yxati:</b>\n\n"
    if not channels:
        text += "<i>Hozircha birorta ham majburiy kanal qo'shilmagan.</i>\n"
    else:
        for i, c in enumerate(channels, 1):
            text += f"{i}. <b>{c['channel_name']}</b>\n   🆔 <code>{c['channel_id']}</code> | 🔗 <a href='{c['channel_link']}'>Havola</a>\n\n"

    text += "\n<i>Yangi kanal qo'shish yoki mavjudini o'chirish uchun quyidagi tugmalardan foydalaning:</i>"
    await message.answer(text, reply_markup=channels_admin_keyboard(channels), parse_mode="HTML")

@admin_router.callback_query(F.data == "admin_add_channel")
async def start_add_channel_callback(callback: types.CallbackQuery, state: FSMContext):
    if not is_user_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
    await state.set_state(AddChannelStates.waiting_for_channel_id)
    await callback.message.answer(
        "📢 <b>1-qadam: Kanal ID sini yoki username ini kiriting:</b>\n\n"
        "<i>Masalan: -1001234567890 yoki @kanal_username</i>\n\n"
        "💡 <i>Eslatma: Bot ushbu kanalda administrator bo'lishi kerak.</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await callback.answer()

@admin_router.message(AddChannelStates.waiting_for_channel_id, F.text)
async def receive_channel_id(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await cancel_action(message, state)
        return

    channel_id = message.text.strip()
    await state.update_data(channel_id=channel_id)
    await state.set_state(AddChannelStates.waiting_for_channel_name)
    await message.answer(
        "📝 <b>2-qadam: Kanal nomini kiriting:</b>\n\n"
        "<i>Masalan: Bizning rasmiy kanalimiz</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )

@admin_router.message(AddChannelStates.waiting_for_channel_name, F.text)
async def receive_channel_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await cancel_action(message, state)
        return

    channel_name = message.text.strip()
    await state.update_data(channel_name=channel_name)
    await state.set_state(AddChannelStates.waiting_for_channel_link)
    await message.answer(
        "🔗 <b>3-qadam: Kanal taklif havolasini (Link) kiriting:</b>\n\n"
        "<i>Masalan: https://t.me/kanal_username yoki maxsus havola</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )

@admin_router.message(AddChannelStates.waiting_for_channel_link, F.text)
async def receive_channel_link(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await cancel_action(message, state)
        return

    channel_link = message.text.strip()
    data = await state.get_data()
    channel_id = data.get("channel_id")
    channel_name = data.get("channel_name")

    db.add_channel(channel_id, channel_name, channel_link)
    await state.clear()

    await message.answer(
        f"✅ <b>Kanal muvaffaqiyatli saqlandi!</b>\n\n"
        f"📢 <b>Nomi:</b> {channel_name}\n"
        f"🆔 <b>ID:</b> <code>{channel_id}</code>\n"
        f"🔗 <b>Link:</b> {channel_link}",
        reply_markup=admin_menu,
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data.startswith("admin_del_chan_"))
async def delete_channel_callback(callback: types.CallbackQuery):
    if not is_user_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
    chan_db_id = int(callback.data.split("_")[3])
    db.remove_channel_by_id(chan_db_id)
    await callback.answer("Kanal o'chirildi!", show_alert=True)

    channels = db.get_all_channels()
    text = "📢 <b>Majburiy kanallar ro'yxati:</b>\n\n"
    if not channels:
        text += "<i>Hozircha birorta ham majburiy kanal qo'shilmagan.</i>\n"
    else:
        for i, c in enumerate(channels, 1):
            text += f"{i}. <b>{c['channel_name']}</b>\n   🆔 <code>{c['channel_id']}</code> | 🔗 <a href='{c['channel_link']}'>Havola</a>\n\n"

    text += "\n<i>Yangi kanal qo'shish yoki mavjudini o'chirish uchun quyidagi tugmalardan foydalaning:</i>"
    try:
        await callback.message.edit_text(text, reply_markup=channels_admin_keyboard(channels), parse_mode="HTML")
    except Exception:
        pass

# ================== 7. KANALGA UZATISH ==================

@admin_router.message(F.text == "📢 Kanalga uzatish")
async def channel_post_start(message: types.Message, state: FSMContext):
    if not is_user_admin(message.from_user.id):
        return

    channels = db.get_all_channels()
    if not channels:
        await message.answer(
            "⚠️ <b>Kanal ulanmagan!</b>\n\n"
            "Iltimos, avval <b>«📢 Kanallarni boshqarish»</b> bo'limidan kanal qo'shing va botni u yerda administrator qiling.",
            reply_markup=admin_menu,
            parse_mode="HTML"
        )
        return

    movies = db.get_recent_movies(limit=20)
    if not movies:
        await message.answer("📭 Bazada hozircha kinolar yo'q. Avval kino yuklang!", reply_markup=admin_menu)
        return

    await state.clear()
    await message.answer(
        "📢 <b>Kanalga uzatish</b>\n\n"
        "Qaysi kino uchun kanalga post tayyorlamoqchisiz?\n"
        "<i>(Kino tanlansa, kanaldagi 'Kinoni tomosha qilish' tugmasini bosgan odamga botda o'sha kino avtomatik ochiladi!)</i>",
        reply_markup=channel_post_movies_keyboard(movies),
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data.startswith("sendtochan_"))
async def select_movie_for_channel_post(callback: types.CallbackQuery, state: FSMContext):
    if not is_user_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    movie_code = callback.data.split("_", 1)[1]
    movie = db.get_movie(movie_code)
    if not movie:
        await callback.answer("Kino topilmadi!", show_alert=True)
        return

    caption = movie.get("caption") or ""
    await state.update_data(
        movie_code=movie_code,
        movie_caption=caption,
        movie_file_id=movie.get("file_id"),
        movie_file_type=movie.get("file_type", "video")
    )
    await state.set_state(ChannelPostStates.waiting_for_media)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"🎬 <b>{movie_code}</b> kodli kino tanlandi!\n\n"
        f"📸 <b>1-qadam: Post uchun Rasm yoki Video yuboring:</b>\n\n"
        f"<i>(Kanalda chiroyli ko'rinishi uchun rasm yoki treyler video yuboring, yoki rasm yuklamaslik uchun '⏩ O'tkazib yuborish' tugmasini bosing)</i>",
        reply_markup=skip_media_kb,
        parse_mode="HTML"
    )
    await callback.answer()

@admin_router.message(ChannelPostStates.waiting_for_media, F.photo)
@admin_router.message(ChannelPostStates.waiting_for_media, F.video)
@admin_router.message(ChannelPostStates.waiting_for_media, F.animation)
async def receive_post_media(message: types.Message, state: FSMContext):
    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = "photo"
    elif message.video:
        media_id = message.video.file_id
        media_type = "video"
    else:
        media_id = message.animation.file_id
        media_type = "animation"

    await state.update_data(media_id=media_id, media_type=media_type)
    await ask_post_text(message, state)

@admin_router.message(ChannelPostStates.waiting_for_media, F.text == "⏩ O'tkazib yuborish")
async def skip_post_media(message: types.Message, state: FSMContext):
    await state.update_data(media_id=None, media_type=None)
    await ask_post_text(message, state)

async def ask_post_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    movie_code = data.get("movie_code", "")
    movie_caption = data.get("movie_caption", "")

    sample_text = movie_caption if movie_caption else f"🍿 Yangi Premyera!\n\n🎬 Kino kodi: {movie_code}\n\n👇 Pastdagi tugmani bosib kinoni tomosha qiling:"

    await state.set_state(ChannelPostStates.waiting_for_text)
    await message.answer(
        f"📝 <b>2-qadam: Post matnini (caption) kiriting:</b>\n\n"
        f"<i>(Kanalga yuboriladigan xabar matnini yozing. HTML format va emojilardan foydalanishingiz mumkin)</i>\n\n"
        f"💡 <b>Tavsiya etilgan namuna:</b>\n<code>{sample_text}</code>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )

@admin_router.message(ChannelPostStates.waiting_for_text, F.text)
async def receive_post_text(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await cancel_action(message, state)
        return

    post_text = message.text.strip()
    await state.update_data(post_text=post_text)
    await state.set_state(ChannelPostStates.confirm_post)

    data = await state.get_data()
    media_id = data.get("media_id")
    media_type = data.get("media_type")
    movie_code = data.get("movie_code", "")

    bot_info = await message.bot.get_me()
    watch_kb = channel_watch_button(bot_info.username or "kino_bot", movie_code=movie_code)

    await message.answer("👁 <b>Post ko'rinishi (Preview):</b>", parse_mode="HTML")

    try:
        if media_id and media_type == "photo":
            await message.answer_photo(photo=media_id, caption=post_text, reply_markup=watch_kb, parse_mode="HTML")
        elif media_id and media_type == "video":
            await message.answer_video(video=media_id, caption=post_text, reply_markup=watch_kb, parse_mode="HTML")
        elif media_id and media_type == "animation":
            await message.answer_animation(animation=media_id, caption=post_text, reply_markup=watch_kb, parse_mode="HTML")
        else:
            await message.answer(post_text, reply_markup=watch_kb, parse_mode="HTML")
    except Exception:
        # Formatlash xatosi bo'lsa oddiy matnda chiqarish
        if media_id and media_type == "photo":
            await message.answer_photo(photo=media_id, caption=post_text, reply_markup=watch_kb)
        elif media_id and media_type == "video":
            await message.answer_video(video=media_id, caption=post_text, reply_markup=watch_kb)
        else:
            await message.answer(post_text, reply_markup=watch_kb)

    await message.answer(
        "❓ <b>Ushbu postni kanalga joylashni tasdiqlaysizmi?</b>",
        reply_markup=confirm_channel_post_send_keyboard(),
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data == "do_channel_post_send")
async def finalize_channel_post_send(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    if not is_user_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    data = await state.get_data()
    await state.clear()

    channels = db.get_all_channels()
    if not channels:
        await callback.answer("Ulangan kanallar topilmadi!", show_alert=True)
        return

    bot_info = await bot.get_me()
    bot_username = bot_info.username or "kino_bot"

    post_text = data.get("post_text", "")
    media_id = data.get("media_id")
    media_type = data.get("media_type")
    movie_code = data.get("movie_code", "")
    markup = channel_watch_button(bot_username, movie_code=movie_code)

    success_count = 0
    errors = []

    for c in channels:
        try:
            target_id = c["channel_id"]
            chat_target = int(target_id) if str(target_id).lstrip("-").isdigit() else target_id

            if media_id and media_type == "photo":
                try:
                    await bot.send_photo(chat_id=chat_target, photo=media_id, caption=post_text, reply_markup=markup, parse_mode="HTML")
                except Exception:
                    await bot.send_photo(chat_id=chat_target, photo=media_id, caption=post_text, reply_markup=markup)
            elif media_id and media_type == "video":
                try:
                    await bot.send_video(chat_id=chat_target, video=media_id, caption=post_text, reply_markup=markup, parse_mode="HTML")
                except Exception:
                    await bot.send_video(chat_id=chat_target, video=media_id, caption=post_text, reply_markup=markup)
            elif media_id and media_type == "animation":
                try:
                    await bot.send_animation(chat_id=chat_target, animation=media_id, caption=post_text, reply_markup=markup, parse_mode="HTML")
                except Exception:
                    await bot.send_animation(chat_id=chat_target, animation=media_id, caption=post_text, reply_markup=markup)
            else:
                try:
                    await bot.send_message(chat_id=chat_target, text=post_text, reply_markup=markup, parse_mode="HTML")
                except Exception:
                    await bot.send_message(chat_id=chat_target, text=post_text, reply_markup=markup)

            success_count += 1
        except Exception as e:
            errors.append(f"{c['channel_name']}: {e}")

    try:
        await callback.message.delete()
    except Exception:
        pass

    if success_count > 0:
        await callback.message.answer(
            f"🎉 <b>Post muvaffaqiyatli ravishda {success_count} ta kanalga joylandi!</b>",
            reply_markup=admin_menu,
            parse_mode="HTML"
        )
    else:
        err_msg = "\n".join(errors)
        await callback.message.answer(
            f"❌ <b>Kanalga joylashda xatolik yuz berdi:</b>\n<code>{err_msg}</code>\n\n"
            f"💡 Bot ushbu kanalda administrator ekanligiga va xabar yozish ruxsatiga ega ekanligiga ishonch hosil qiling.",
            reply_markup=admin_menu,
            parse_mode="HTML"
        )

    await callback.answer()

@admin_router.callback_query(F.data == "do_channel_post_cancel")
async def cancel_channel_post_send(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text("❌ Kanalga joylash bekor qilindi.")
    except Exception:
        pass
    await callback.message.answer("Admin menyu:", reply_markup=admin_menu)
    await callback.answer()


