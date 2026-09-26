import os
import re

DEFAULT_BOT_TOKEN = "8663351252:AAGV_vQBcybibET7upszRwMFD0-mS55IMsY"

raw_token = os.getenv("BOT_TOKEN", "").strip()

def clean_token(token: str) -> str:
    if not token or len(token) < 15:
        return DEFAULT_BOT_TOKEN
    t = token.strip().strip('"').strip("'").strip()
    if "=" in t:
        t = t.split("=", 1)[1].strip().strip('"').strip("'").strip()
    match = re.search(r"(\d{8,12}:[A-Za-z0-9_-]{30,})", t)
    if match:
        return match.group(1)
    return DEFAULT_BOT_TOKEN

BOT_TOKEN = clean_token(raw_token)

# Birlamchi Admin ID lari (agar bilsangiz shu yerga kiritishingiz mumkin yoki ADMIN_IDS muhit o'zgaruvchisi orqali)
INITIAL_ADMINS = []
admin_ids_env = os.getenv("ADMIN_IDS", "")
if admin_ids_env:
    try:
        INITIAL_ADMINS.extend([int(x.strip()) for x in admin_ids_env.split(",") if x.strip().isdigit()])
    except Exception:
        pass

# Admin bo'lish uchun maxfiy parol
raw_pwd = os.getenv("ADMIN_PASSWORD", "davlat20102412")
if raw_pwd:
    p = raw_pwd.strip().strip('"').strip("'")
    if "=" in p:
        p = p.split("=", 1)[1].strip().strip('"').strip("'")
    ADMIN_PASSWORD = p if p else "davlat20102412"
else:
    ADMIN_PASSWORD = "davlat20102412"
