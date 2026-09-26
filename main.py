import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.exceptions import TelegramNetworkError, TelegramConflictError

from config import BOT_TOKEN
from handlers.admin import admin_router
from handlers.user import user_router
from database import db

# Windows konsolida UTF-8 kodirovkasini to'g'rilash
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Log sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("KinoBot")

# Render va bulutli hostinglar uchun Healthcheck HTTP serveri
async def start_healthcheck_server():
    try:
        port = int(os.getenv("PORT", 8080))
        app = web.Application()
        app.router.add_get("/", lambda req: web.Response(text="Kino Bot Status: OK 200 (Running 24/7)"))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Healthcheck HTTP server {port}-portda ishga tushdi.")
    except Exception as e:
        logger.warning(f"Healthcheck serverini yoqishda ogohlantirish: {e}")

# Telegram bot buyruqlari menyusi
async def set_commands(bot: Bot):
    try:
        commands = [
            BotCommand(command="start", description="Botni ishga tushirish"),
            BotCommand(command="admin", description="Admin paneli"),
            BotCommand(command="myid", description="Mening ID raqamim"),
        ]
        await bot.set_my_commands(commands)
    except Exception as e:
        logger.warning(f"Buyruqlarni o'rnatishda xatolik: {e}")

async def main():
    if not BOT_TOKEN or "YOUR_TOKEN" in BOT_TOKEN:
        logger.error("Xatolik: BOT_TOKEN ko'rsatilmagan!")
        return

    # Render uchun HTTP healthcheck serverini ishga tushirish
    await start_healthcheck_server()

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni ulash
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # Buyruqlarni menyuga qo'shish
    await set_commands(bot)

    try:
        bot_info = await bot.get_me()
        print("=" * 45)
        print(f"[*] KINO BOT ISHGA TUSHDI: @{bot_info.username}")
        print(f"[*] Bazada kinolar soni: {db.get_movies_count()} ta")
        print(f"[*] Bazada foydalanuvchilar: {db.get_users_count()} ta")
        print("[*] 24/7 rejim faollashtirildi!")
        print("=" * 45)
    except Exception as e:
        logger.error(f"Telegramga ulanishda xatolik: {e}")

    # Uzluksiz 24/7 ishlash sikli (aloqa uzilsa avtomatik qayta ulanadi)
    while True:
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            break
        except TelegramConflictError:
            logger.critical("⚠️ XATOLIK: Bot boshqa server yoki konsolda ham yoqilgan! 10 soniyadan so'ng qayta urinib ko'riladi...")
            await asyncio.sleep(10)
        except (TelegramNetworkError, Exception) as e:
            logger.warning(f"⚠️ Ulanishda uzilish: {e}. 5 soniyadan so'ng qayta ulanadi...")
            await asyncio.sleep(5)

    try:
        await bot.session.close()
    except Exception:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nBot to'xtatildi!")
