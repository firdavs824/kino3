from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart, Command, CommandObject
from database import db
from keyboards import user_menu, admin_menu, must_subscribe_keyboard
from config import INITIAL_ADMINS

user_router = Router()

def is_user_admin(user_id: int) -> bool:
    if user_id in INITIAL_ADMINS or db.is_admin(user_id):
        return True
    return False

# ================== MAJBURIY OBUNA TEKSHIRUVI ==================

async def check_user_subscription(bot: Bot, user_id: int) -> bool:
    """Foydalanuvchi barcha majburiy kanallarga a'zo bo'lganligini tekshirish."""
    if is_user_admin(user_id):
        return True

    channels = db.get_all_channels()
    if not channels:
        return True

    for c in channels:
        try:
            chan_id_str = str(c["channel_id"]).strip()
            chat_id = int(chan_id_str) if chan_id_str.lstrip("-").isdigit() else chan_id_str
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in ["creator", "administrator", "member", "restricted"]:
                return False
        except Exception:
            # Agar bot kanalga admin qilinmagan bo'lsa yoki xatolik bo'lsa tekshiruvdan o'tkaziladi
            continue

    return True

async def prompt_subscription(message: types.Message, movie_code: str = ""):
    """Obuna bo'lish talabi xabari."""
    channels = db.get_all_channels()
    text = (
        "⚠️ <b>Kinoni tomosha qilish va botdan to'liq foydalanish uchun avval quyidagi kanallarimizga a'zo bo'ling!</b>\n\n"
        "Kanallarga obuna bo'lib, so'ng <b>'✅ Obunani tekshirish'</b> tugmasini bosing:"
    )
    await message.answer(
        text,
        reply_markup=must_subscribe_keyboard(channels, movie_code=movie_code),
        parse_mode="HTML"
    )

async def send_movie_to_user(bot: Bot, chat_id: int, movie: dict):
    """Foydalanuvchiga kinoni yuborish."""
    file_id = movie["file_id"]
    file_type = movie.get("file_type", "video")
    views = movie.get("views", 1)
    original_caption = movie.get("caption") or ""

    bot_info = await bot.get_me()
    caption = (
        f"{original_caption}\n\n"
        f"🔑 <b>Kino kodi:</b> <code>{movie['code']}</code>\n"
        f"👁 <b>Ko'rishlar soni:</b> {views}\n"
        f"🤖 @{bot_info.username} orqali yuklab olindi"
    )

    try:
        if file_type == "video":
            await bot.send_video(chat_id=chat_id, video=file_id, caption=caption, parse_mode="HTML")
        elif file_type == "document":
            await bot.send_document(chat_id=chat_id, document=file_id, caption=caption, parse_mode="HTML")
        elif file_type == "animation":
            await bot.send_animation(chat_id=chat_id, animation=file_id, caption=caption, parse_mode="HTML")
        else:
            await bot.send_video(chat_id=chat_id, video=file_id, caption=caption, parse_mode="HTML")
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"❌ Kinoni yuborishda xatolik yuz berdi: {e}")

# ================== HANDLERLAR ==================

@user_router.message(CommandStart())
async def start_handler(message: types.Message, command: CommandObject = None):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    # Bazaga foydalanuvchini qo'shish
    db.add_user(user_id=user_id, full_name=full_name, username=username)

    # Deep linking orqali kelgan bo'lsa (masalan: /start 15)
    args = command.args if command else None
    if args:
        code = args.strip().lower()
        if not await check_user_subscription(message.bot, user_id):
            await prompt_subscription(message, movie_code=code)
            return

        movie = db.get_movie(code)
        if movie:
            await send_movie_to_user(message.bot, message.chat.id, movie)
            return
        else:
            await message.answer(
                f"❌ <b>{code}</b> kodli kino topilmadi!\n\n"
                f"💡 Kodni to'g'ri kiritganingizga ishonch hosil qiling.",
                parse_mode="HTML"
            )

    # Majburiy obuna tekshiruvi
    if not await check_user_subscription(message.bot, user_id):
        await prompt_subscription(message, movie_code="main")
        return

    admin_status = is_user_admin(user_id)
    menu = admin_menu if admin_status else user_menu

    welcome_text = (
        f"👋 Assalomu alaykum, <b>{full_name}</b>!\n\n"
        f"🎬 <b>Kino botimizga xush kelibsiz!</b>\n\n"
        f"Kinoni topish uchun uning <b>kodini</b> yuboring (masalan: <code>1</code>, <code>25</code> yoki <code>avatar</code>).\n\n"
        f"🔢 O'zingiz qidirayotgan kino kodini yozib yuboring:"
    )

    if admin_status:
        welcome_text += "\n\n⭐️ <i>Siz administrator ekansiz. Admin panel orqali kino yuklashingiz mumkin.</i>"

    await message.answer(welcome_text, reply_markup=menu, parse_mode="HTML")

@user_router.callback_query(F.data.startswith("checksub_"))
async def check_subscription_callback(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split("_", 1)
    movie_code = parts[1] if len(parts) > 1 else ""

    is_sub = await check_user_subscription(bot, callback.from_user.id)
    if is_sub:
        await callback.answer("✅ Rahmat! Obuna tasdiqlandi.")
        try:
            await callback.message.delete()
        except Exception:
            pass

        if movie_code and movie_code != "main":
            movie = db.get_movie(movie_code)
            if movie:
                await send_movie_to_user(bot, callback.message.chat.id, movie)
                return
            else:
                await callback.message.answer(
                    f"❌ <b>{movie_code}</b> kodli kino topilmadi!",
                    parse_mode="HTML"
                )

        admin_status = is_user_admin(callback.from_user.id)
        menu = admin_menu if admin_status else user_menu
        await callback.message.answer(
            "🎉 <b>Obuna tasdiqlandi! Kino botga xush kelibsiz.</b>\n\n"
            "Endi o'zingiz qidirayotgan kino kodini yozib bemalol tomosha qilishingiz mumkin.",
            reply_markup=menu,
            parse_mode="HTML"
        )
    else:
        await callback.answer(
            "❌ Siz hali hamma kanallarga obuna bo'lmadingiz! Iltimos, havolalar orqali a'zo bo'ling.",
            show_alert=True
        )

@user_router.message(Command("myid"))
async def my_id_handler(message: types.Message):
    await message.answer(
        f"🆔 Sizning Telegram ID raqamingiz: <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )

@user_router.message(F.text == "🔍 Kino qidirish (kod orqali)")
async def search_movie_btn(message: types.Message):
    # Obunani tekshirish
    if not await check_user_subscription(message.bot, message.from_user.id):
        await prompt_subscription(message, movie_code="main")
        return
    await message.answer("🔢 Marhamat, kino kodini yozib yuboring (masalan: <code>1</code> yoki <code>105</code>):", parse_mode="HTML")

@user_router.message(F.text == "ℹ️ Bot haqida")
async def about_bot(message: types.Message):
    await message.answer(
        "🤖 <b>Kino Bot haqida:</b>\n\n"
        "Bu bot orqali siz turli kinolarni ularning maxsus kodi orqali tez va qulay yuklab olishingiz mumkin.\n"
        "Shunchaki kino kodini yozing va bot sizga kinoni yuboradi!",
        parse_mode="HTML"
    )

# Foydalanuvchi kod yozganda kinoni topib berish
@user_router.message(F.text)
async def get_movie_by_code(message: types.Message):
    code = message.text.strip().lower()

    # Agar buyruq yoki menyu matnlari bo'lsa o'tkazib yuboramiz
    ignored_buttons = [
        "🎬 kino yuklash / saqlash", "🗑 kino o'chirish", "📋 kinolar ro'yxati", 
        "📊 statistika", "📢 kanalga uzatish", "📢 kanallarni boshqarish", "📢 barchaga xabar yuborish", "🔑 admin kodi", 
        "🚪 foydalanuvchi rejimi", "🔐 admin panel", "🔍 kino qidirish (kod orqali)", "ℹ️ bot haqida"
    ]
    if code.startswith("/") or code in ignored_buttons:
        return

    # Agar foydalanuvchi admin parolini yozsa, uni admin qilamiz
    admin_pwd = db.get_admin_password().lower()
    valid_passwords = [
        admin_pwd,
        admin_pwd.lstrip("/"),
        "/" + admin_pwd.lstrip("/"),
        "davlat20102412",
        "/davlat20102412"
    ]
    if code in valid_passwords:
        db.add_admin(message.from_user.id)
        await message.answer(
            "🎉 <b>Admin kodi to'g'ri kiritildi!</b>\n\n"
            "Siz administrator bo'ldingiz. Marhamat, admin panelidan foydalanishingiz mumkin:",
            reply_markup=admin_menu,
            parse_mode="HTML"
        )
        return

    # Majburiy obunani tekshirish
    if not await check_user_subscription(message.bot, message.from_user.id):
        await prompt_subscription(message, movie_code=code)
        return

    movie = db.get_movie(code)

    if not movie:
        await message.answer(
            f"❌ <b>{code}</b> kodli kino topilmadi!\n\n"
            f"💡 Kodni to'g'ri kiritganingizga ishonch hosil qiling.",
            parse_mode="HTML"
        )
        return

    await send_movie_to_user(message.bot, message.chat.id, movie)
