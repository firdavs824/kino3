from typing import List, Dict, Any
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Bekor qilish tugmasi
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Bekor qilish")]
    ],
    resize_keyboard=True
)

# Media o'tkazib yuborish tugmasi
skip_media_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏩ O'tkazib yuborish")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ],
    resize_keyboard=True
)

# Admin asosiy menyusi
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Kino yuklash / saqlash"), KeyboardButton(text="🗑 Kino o'chirish")],
        [KeyboardButton(text="📋 Kinolar ro'yxati"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📢 Kanalga uzatish"), KeyboardButton(text="📢 Kanallarni boshqarish")],
        [KeyboardButton(text="📢 Barchaga xabar yuborish"), KeyboardButton(text="🔑 Admin kodi")],
        [KeyboardButton(text="🚪 Foydalanuvchi rejimi")]
    ],
    resize_keyboard=True
)

# Foydalanuvchi menyusi (begonalarga admin paneli ko'rinmaydi)
user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Kino qidirish (kod orqali)")],
        [KeyboardButton(text="ℹ️ Bot haqida")]
    ],
    resize_keyboard=True
)

# Inline tasdiqlash tugmalari
def get_delete_confirm_kb(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirilsin", callback_data=f"del_yes_{code}"),
                InlineKeyboardButton(text="❌ Yo'q, qolsin", callback_data="del_no")
            ]
        ]
    )

# Majburiy obuna klaviaturasi
def must_subscribe_keyboard(channels: List[Dict[str, Any]], movie_code: str = "") -> InlineKeyboardMarkup:
    buttons = []
    for c in channels:
        buttons.append([
            InlineKeyboardButton(text=f"📢 {c['channel_name']}", url=c['channel_link'])
        ])
    
    cb_data = f"checksub_{movie_code}" if movie_code else "checksub_main"
    buttons.append([
        InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data=cb_data)
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Admin uchun kanallarni boshqarish klaviaturasi
def channels_admin_keyboard(channels: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="admin_add_channel")
        ]
    ]
    for c in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {c['channel_name']} (O'chirish)",
                callback_data=f"admin_del_chan_{c['id']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Kanalga uzatish uchun kinolar ro'yxati klaviaturasi
def channel_post_movies_keyboard(movies: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    buttons = []
    for m in movies:
        code = m.get("code", "")
        caption = m.get("caption") or ""
        caption_preview = (caption[:25] + "...") if caption else "Kino"
        buttons.append([
            InlineKeyboardButton(
                text=f"🎬 Kod: {code} | {caption_preview}",
                callback_data=f"sendtochan_{code}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Kanalga joylashni tasdiqlash tugmalari
def confirm_channel_post_send_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, kanalga joyla!", callback_data="do_channel_post_send"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="do_channel_post_cancel")
            ]
        ]
    )

# Kanalga tashlangan post ostidagi tugma (Botga o'tib kinoni ochish)
def channel_watch_button(bot_username: str, movie_code: str = "") -> InlineKeyboardMarkup:
    url = f"https://t.me/{bot_username}?start={movie_code}" if movie_code else f"https://t.me/{bot_username}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎬 Kinoni tomosha qilish",
                    url=url
                )
            ]
        ]
    )

