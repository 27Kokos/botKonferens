import time
from bots.moderator_bot import moderator_bot
from core.data_manager import log

if __name__ == "__main__":
    log("🛠 [MODERATOR BOT] Запуск админ-бота...")

    while True:
        try:
            moderator_bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            log(f"❌ Ошибка в админ-боте: {e}")
            time.sleep(5)
