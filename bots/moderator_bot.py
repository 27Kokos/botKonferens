from telebot import TeleBot, types
from datetime import datetime

# === Импорты из ядра ===
from core.data_manager import log
from core.moderation_manager import (
    get_pending_suggestions,
    get_processed_suggestions,
    update_suggestion_status,
    get_stats,
)
from core.user_manager import (
    get_all_users,
    reset_all_users_progress,
    delete_all_users,
    reset_user_progress,
)
from core.leaderboard import update_leaderboard
from config import MODERATOR_BOT_TOKEN


# === Инициализация ===
moderator_bot = TeleBot(MODERATOR_BOT_TOKEN)


# ===============================
# 🏠 Главное меню
# ===============================
@moderator_bot.message_handler(commands=['start'])
def start(message):
    text = (
        "👋 <b>Добро пожаловать, модератор!</b>\n\n"
        "🛠 <b>Что хотите сделать?</b>"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💡 Предложения", callback_data="suggestions"))
    markup.add(types.InlineKeyboardButton("📊 Статистика", callback_data="stats"))
    markup.add(types.InlineKeyboardButton("🧹 Сбросить прогресс", callback_data="reset_progress"))
    markup.add(types.InlineKeyboardButton("⚙️ Пользователи", callback_data="users_menu"))
    moderator_bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)


# ===============================
# 💡 Предложения
# ===============================
def show_pending_suggestions(chat_id):
    suggestions = get_pending_suggestions()
    if not suggestions:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_main"))
        moderator_bot.send_message(chat_id, "✅ Нет предложений на модерацию.", reply_markup=markup)
        return

    for s in suggestions:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve::{s['id']}"),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject::{s['id']}")
        )
        moderator_bot.send_message(
            chat_id,
            f"💡 <b>От @{s['user_data']['username'] or s['user_data']['first_name']}:</b>\n\n"
            f"{s['content']}",
            parse_mode="HTML",
            reply_markup=markup,
        )

    # кнопка «назад»
    back = types.InlineKeyboardMarkup()
    back.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_main"))
    moderator_bot.send_message(chat_id, "📬 Конец списка предложений", reply_markup=back)


def show_processed_suggestions(chat_id):
    processed = get_processed_suggestions(limit=15)
    if not processed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="stats"))
        moderator_bot.send_message(chat_id, "📭 Нет обработанных предложений.", reply_markup=markup)
        return
    text = "📜 <b>История модерации:</b>\n\n"
    for s in processed:
        icon = "✅" if s["status"] == "approved" else "❌"
        text += f"{icon} {s['content'][:50]}... ({s['status']})\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="stats"))
    moderator_bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


# ===============================
# 📊 Статистика
# ===============================
def show_stats(chat_id):
    stats = get_stats()
    text = (
        f"📊 <b>Статистика предложений:</b>\n\n"
        f"💡 Всего: {stats['total']}\n"
        f"✅ Одобрено: {stats['approved']}\n"
        f"❌ Отклонено: {stats['rejected']}\n"
        f"🕓 В ожидании: {stats['pending']}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 История", callback_data="processed"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_main"))
    moderator_bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


# ===============================
# ⚙️ Пользователи
# ===============================
def show_users_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👥 Все пользователи", callback_data="all_users"))
    markup.add(types.InlineKeyboardButton("🧹 Удалить всех", callback_data="delete_all_users"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_main"))
    moderator_bot.send_message(chat_id, "⚙️ <b>Управление пользователями</b>", parse_mode="HTML", reply_markup=markup)


def show_all_users(chat_id):
    users = get_all_users()
    if not users:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="users_menu"))
        moderator_bot.send_message(chat_id, "📭 Нет пользователей.", reply_markup=markup)
        return
    text = "<b>👥 Все пользователи:</b>\n\n"
    for uid, u in users.items():
        text += f"• {u['first_name']} (@{u['username'] or 'нет'}) — {u['total_points']}⭐\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="users_menu"))
    moderator_bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


# ===============================
# 🧹 Сброс прогресса
# ===============================
def show_reset_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Сбросить всех", callback_data="reset_all"))
    markup.add(types.InlineKeyboardButton("👤 Сбросить одного", callback_data="reset_one_menu"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_main"))
    moderator_bot.send_message(chat_id, "🧹 <b>Выберите действие:</b>", parse_mode="HTML", reply_markup=markup)


def show_reset_one_menu(chat_id):
    """Меню выбора конкретного пользователя для сброса"""
    users = get_all_users()
    if not users:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="reset_progress"))
        moderator_bot.send_message(chat_id, "📭 Нет пользователей для сброса.", reply_markup=markup)
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for uid, u in users.items():
        name = f"{u['first_name']} (@{u['username'] or 'нет'})"
        markup.add(types.InlineKeyboardButton(f"🧹 {name}", callback_data=f"reset_user::{uid}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="reset_progress"))
    moderator_bot.send_message(chat_id, "👤 <b>Выберите пользователя для сброса:</b>", parse_mode="HTML", reply_markup=markup)


# ===============================
# 🎯 Обработчик callback
# ===============================
@moderator_bot.callback_query_handler(func=lambda c: True)
def handle_callbacks(call):
    data = call.data
    chat_id = call.message.chat.id

    try:
        # Главное меню
        if data == "back_main":
            moderator_bot.delete_message(chat_id, call.message.message_id)
            start(call.message)

        # Предложения
        elif data == "suggestions":
            moderator_bot.delete_message(chat_id, call.message.message_id)
            show_pending_suggestions(chat_id)
        elif data == "processed":
            moderator_bot.delete_message(chat_id, call.message.message_id)
            show_processed_suggestions(chat_id)

        # Статистика
        elif data == "stats":
            moderator_bot.delete_message(chat_id, call.message.message_id)
            show_stats(chat_id)

        # Пользователи
        elif data == "users_menu":
            moderator_bot.delete_message(chat_id, call.message.message_id)
            show_users_menu(chat_id)
        elif data == "all_users":
            moderator_bot.delete_message(chat_id, call.message.message_id)
            show_all_users(chat_id)
        elif data == "delete_all_users":
            delete_all_users()
            moderator_bot.send_message(chat_id, "🧹 Все пользователи удалены.")

        # Сброс прогресса
        elif data == "reset_progress":
            moderator_bot.delete_message(chat_id, call.message.message_id)
            show_reset_menu(chat_id)
        elif data == "reset_all":
            reset_all_users_progress()
            update_leaderboard()
            moderator_bot.send_message(chat_id, "✅ Прогресс всех пользователей сброшен.")
        elif data == "reset_one_menu":
            moderator_bot.delete_message(chat_id, call.message.message_id)
            show_reset_one_menu(chat_id)
        elif data.startswith("reset_user::"):
            uid = data.split("::")[1]
            reset_user_progress(uid)
            update_leaderboard()
            moderator_bot.send_message(chat_id, f"✅ Прогресс пользователя {uid} сброшен.")

        # Модерация
        elif data.startswith("approve::"):
            suggestion_id = data.split("::")[1]
            update_suggestion_status(suggestion_id, "approved", chat_id)
            moderator_bot.answer_callback_query(call.id, "✅ Одобрено")
            moderator_bot.delete_message(chat_id, call.message.message_id)
        elif data.startswith("reject::"):
            suggestion_id = data.split("::")[1]
            update_suggestion_status(suggestion_id, "rejected", chat_id)
            moderator_bot.answer_callback_query(call.id, "❌ Отклонено")
            moderator_bot.delete_message(chat_id, call.message.message_id)

    except Exception as e:
        log(f"❌ Ошибка moderator_bot: {e}")
        moderator_bot.send_message(chat_id, "⚠️ Произошла ошибка.")


# ===============================
# 🚀 Запуск
# ===============================
if __name__ == "__main__":
    log("[MODERATOR BOT] Запуск админ-бота...")
    moderator_bot.infinity_polling()
