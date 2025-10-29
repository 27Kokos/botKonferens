import time
from bots.main_bot import bot
from core.data_manager import log

if __name__ == "__main__":
    log("🚀 [MAIN BOT] Запуск основного бота...")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            log(f"❌ Ошибка в основном боте: {e}")
            time.sleep(5)
