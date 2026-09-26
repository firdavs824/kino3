import os

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8663351252:AAGV_vQBcybibET7upszRwMFD0-mS55IMsY")

# Birlamchi Admin ID lari (agar bilsangiz shu yerga kiritishingiz mumkin yoki ADMIN_IDS muhit o'zgaruvchisi orqali)
INITIAL_ADMINS = []
admin_ids_env = os.getenv("ADMIN_IDS", "")
if admin_ids_env:
    try:
        INITIAL_ADMINS.extend([int(x.strip()) for x in admin_ids_env.split(",") if x.strip().isdigit()])
    except Exception:
        pass

# Admin bo'lish uchun maxfiy parol
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "davlat20102412")


