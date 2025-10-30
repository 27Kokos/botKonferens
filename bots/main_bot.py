import html
import sys
import codecs
from datetime import datetime
from telebot import TeleBot, types

# === Импорт из ядра ===
from core.data_manager import log, load_json, save_json
from core.user_manager import init_user
from core.articles import load_articles, get_article, mark_article_as_read, get_user_articles_progress
from core.leaderboard import update_leaderboard, get_leaderboard_display_name
from core.quizzes import get_quiz, finalize_quiz_for_user
from core.moderation_manager import add_suggestion
from config import MAIN_BOT_TOKEN, USERS_FILE, USER_STATES_FILE

# === Настройки кодировки (для Windows-консоли) ===
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# === Инициализация бота ===
bot = TeleBot(MAIN_BOT_TOKEN)

# === Глобальные переменные ===
user_states = load_json(USER_STATES_FILE)
active_quizzes = {}


# ===============================
# 💬 Команда /start
# ===============================
@bot.message_handler(commands=['start'])
def start(message):
    user = init_user(message.chat.id, message.from_user.username, message.from_user.first_name)
    welcome_text = (
        f"👋 Привет, <b>{html.escape(user['first_name'])}</b>!\n\n"
        f"🚀 Добро пожаловать в <b>CodeForge</b> — платформу для изучения программирования!\n\n"
        f"✨ <b>Ты можешь:</b>\n"
        f"• 📚 Изучать языки\n"
        f"• 🧠 Проходить тесты\n"
        f"• 📊 Следить за прогрессом\n"
        f"• 🏆 Соревноваться в рейтинге\n"
        f"• 💡 Отправлять предложения\n\n"
        f"<b>Выбери действие:</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📚 Языки программирования', callback_data='languages'))
    markup.add(types.InlineKeyboardButton('🧠 Пройти тест', callback_data='take_quiz'))
    markup.add(types.InlineKeyboardButton('📊 Мой прогресс', callback_data='progress'))
    markup.add(types.InlineKeyboardButton('🏆 Лидерборд', callback_data='leaderboard'))
    markup.add(types.InlineKeyboardButton('💡 Предложения', callback_data='suggestion'))
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

    user_states[str(message.chat.id)] = 'main_menu'
    save_json(user_states, USER_STATES_FILE)


# ===============================
# 📚 Меню языков
# ===============================
def show_languages_menu(chat_id, message_id=None):
    if message_id:
        bot.delete_message(chat_id, message_id)

    markup = types.InlineKeyboardMarkup()
    for lang in ['VBA', 'C', 'Bash', 'Python', 'JavaScript']:
        markup.add(types.InlineKeyboardButton(lang, callback_data=lang))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_main'))

    bot.send_message(chat_id, '📚 <b>Выбери язык программирования:</b>', parse_mode='HTML', reply_markup=markup)
    user_states[str(chat_id)] = 'languages'
    save_json(user_states, USER_STATES_FILE)


# ===============================
# 🧠 Меню тестов
# ===============================
def show_quiz_selection(chat_id, message_id=None):
    if message_id:
        bot.delete_message(chat_id, message_id)

    markup = types.InlineKeyboardMarkup()
    for lang in ['VBA', 'C', 'Bash', 'Python', 'JavaScript']:
        markup.add(types.InlineKeyboardButton(f'🧠 {lang} - Основы', callback_data=f'quiz_{lang}_basic'))
    markup.add(types.InlineKeyboardButton('🧠 Тест по всем темам', callback_data='quiz_Big_Test'))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_main'))

    bot.send_message(chat_id, '🧠 <b>Выбери тест:</b>', parse_mode='HTML', reply_markup=markup)
    user_states[str(chat_id)] = 'quiz_selection'
    save_json(user_states, USER_STATES_FILE)


# ===============================
# 🏆 Лидерборд
# ===============================
def show_leaderboard(chat_id, message_id=None):
    if message_id:
        bot.delete_message(chat_id, message_id)
    leaderboard = update_leaderboard()
    ranking = leaderboard.get('ranking', [])[:15]
    text = "🏆 <b>Общий рейтинг</b>\n\n"
    if not ranking:
        text += "Пока никто не заработал очков."
    else:
        for i, u in enumerate(ranking):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            text += f"{medal} <b>{get_leaderboard_display_name(u)}</b> — ⭐ {u['total_points']} очков\n"
    text += f"\n🕐 Обновлено: {leaderboard['last_updated']}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='leaderboard'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='back_main'))
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')


# ===============================
# 📊 Прогресс
# ===============================
def show_progress(chat_id):
    users = load_json(USERS_FILE)
    uid = str(chat_id)
    if uid not in users:
        bot.send_message(chat_id, "Вы еще не начали обучение. Используйте /start.")
        return
    u = users[uid]
    text = (
        f"📊 <b>Ваш прогресс</b>\n\n"
        f"👤 <b>{html.escape(u['first_name'])}</b>\n"
        f"📅 С {u['joined_date']}\n"
        f"🏆 Очков: {u['total_points']}\n"
        f"📚 Статей: {u['stats']['articles_read']}\n"
        f"🧠 Тестов: {u['stats']['quizzes_taken']}\n"
        f"📈 Средний балл: {u['stats']['average_score']}%\n"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🏆 Лидерборд', callback_data='leaderboard'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='back_main'))
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ===============================
# 💡 Предложения
# ===============================
@bot.message_handler(func=lambda m: user_states.get(str(m.chat.id)) == 'suggestion_wait')
def handle_suggestion(message):
    text = message.text.strip()
    success = add_suggestion(message.chat.id, message.from_user.username, message.from_user.first_name, text)
    if success:
        bot.send_message(message.chat.id, "✅ Спасибо! Ваше предложение отправлено на модерацию.")
    else:
        bot.send_message(message.chat.id, "❌ Ошибка при отправке предложения.")
    user_states[str(message.chat.id)] = 'main_menu'
    save_json(user_states, USER_STATES_FILE)
    start(message)


# ===============================
# 🎯 Callback обработчик
# ===============================
@bot.callback_query_handler(func=lambda c: True)
def handle_callbacks(call):
    uid = call.message.chat.id
    data = call.data

    try:
        if data == 'languages':
            show_languages_menu(uid, call.message.message_id)
        elif data == 'take_quiz':
            show_quiz_selection(uid, call.message.message_id)
        elif data == 'leaderboard':
            show_leaderboard(uid, call.message.message_id)
        elif data == 'progress':
            bot.delete_message(uid, call.message.message_id)
            show_progress(uid)
        elif data == 'suggestion':
            bot.delete_message(uid, call.message.message_id)
            bot.send_message(uid, "💡 Напишите ваше предложение:")
            user_states[str(uid)] = 'suggestion_wait'
            save_json(user_states, USER_STATES_FILE)
        elif data == 'back_main':
            bot.delete_message(uid, call.message.message_id)
            start(call.message)

        elif data in ['VBA', 'C', 'Bash', 'Python', 'JavaScript']:
            show_language_articles(uid, data, call.message.message_id)

        elif data.startswith('quiz_'):
            quiz_id = data.replace('quiz_', '')
            show_quiz_info(uid, quiz_id, call.message.message_id)

        elif data.startswith('start_quiz_'):
            quiz_id = data.split('start_quiz_')[1]
            start_quiz(uid, quiz_id, call.message.message_id)

        elif data.startswith('answer_'):
            handle_quiz_answer(call)

        elif data.startswith('article::'):
            _, lang, article_key = data.split('::')
            show_article(uid, lang, article_key, call.message.message_id)

        elif data.startswith('mark_read::'):
            _, lang, article_key = data.split('::')
            if mark_article_as_read(uid, lang, article_key):
                bot.answer_callback_query(call.id, "✅ Статья отмечена как прочитанная!")
                show_article(uid, lang, article_key, call.message.message_id)
            else:
                bot.answer_callback_query(call.id, "❌ Уже отмечена ранее")

    except Exception as e:
        log(f"❌ Ошибка callback: {e}")
        bot.send_message(uid, "Произошла ошибка. Попробуйте позже.")


# ===============================
# 📚 Меню статей для языка
# ===============================
def show_language_articles(chat_id, language, message_id=None):
    if message_id:
        bot.delete_message(chat_id, message_id)
    articles = load_articles().get(language, {})
    user_progress = get_user_articles_progress(chat_id, language)

    markup = types.InlineKeyboardMarkup()
    for key, art in articles.items():
        emoji = "✅" if key in user_progress else "📖"
        markup.add(types.InlineKeyboardButton(f"{emoji} {art['title']}", callback_data=f"article::{language}::{key}"))

    markup.add(types.InlineKeyboardButton('📚 Другие языки', callback_data='languages'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='back_main'))

    bot.send_message(chat_id, f"📚 <b>{language}</b> — выбери статью:", parse_mode='HTML', reply_markup=markup)


# ===============================
# 📖 Показ статьи
# ===============================
def show_article(chat_id, language, key, message_id=None):
    if message_id:
        bot.delete_message(chat_id, message_id)
    article = get_article(language, key)
    if not article:
        bot.send_message(chat_id, "❌ Статья не найдена.")
        return
    user_progress = get_user_articles_progress(chat_id, language)
    is_read = key in user_progress
    text = (
        f"📖 <b>{article['title']}</b>\n\n"
        f"{article['description']}\n\n"
        f"⚡ Сложность: {article['difficulty']}\n"
        f"⏱ Время: {article['estimated_time']}\n"
        f"🏆 Награда: {article['points']} очков\n"
        f"📊 Статус: {'✅ Прочитано' if is_read else '❌ Не прочитано'}"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔗 Перейти к статье', url=article['url']))
    if not is_read:
        markup.add(types.InlineKeyboardButton('✅ Отметить как прочитанную', callback_data=f'mark_read::{language}::{key}'))
    markup.add(types.InlineKeyboardButton('📚 Назад', callback_data=language))
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ===============================
# 🧠 Квизы
# ===============================
def show_quiz_info(chat_id, quiz_id, message_id=None):
    if message_id:
        bot.delete_message(chat_id, message_id)
    quiz = get_quiz(quiz_id)
    if not quiz:
        bot.send_message(chat_id, "❌ Этот тест недоступен.")
        return
    text = (
        f"🧠 <b>{quiz['title']}</b>\n\n"
        f"{quiz['description']}\n\n"
        f"⚡ Сложность: {quiz['difficulty']}\n"
        f"⏱ Время: {quiz['time_limit']} сек\n"
        f"📊 Вопросов: {len(quiz['questions'])}\n"
        f"🏆 Максимум: {quiz['total_points']}\n"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🚀 Начать', callback_data=f'start_quiz_{quiz_id}'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='back_main'))
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


def start_quiz(chat_id, quiz_id, message_id=None):
    if message_id:
        bot.delete_message(chat_id, message_id)
    quiz = get_quiz(quiz_id)
    if not quiz:
        bot.send_message(chat_id, "❌ Квиз недоступен.")
        return
    active_quizzes[chat_id] = {"quiz": quiz, "score": 0, "current": 0}
    send_quiz_question(chat_id)


def send_quiz_question(chat_id):
    data = active_quizzes.get(chat_id)
    if not data:
        return
    quiz = data["quiz"]
    index = data["current"]
    if index >= len(quiz['questions']):
        finish_quiz(chat_id)
        return
    q = quiz['questions'][index]
    
    # Экранируем HTML-сущности в тексте вопроса
    question_text = html.escape(q['question_text'])
    
    markup = types.InlineKeyboardMarkup()
    for i, opt in enumerate(q['options']):
        # Также экранируем варианты ответов
        escaped_opt = html.escape(opt)
        markup.add(types.InlineKeyboardButton(escaped_opt, callback_data=f'answer_{index}_{i}'))
    
    bot.send_message(chat_id, f"❓ <b>{question_text}</b>", parse_mode='HTML', reply_markup=markup)


def handle_quiz_answer(call):
    uid = call.message.chat.id
    data = call.data.split('_')
    q_index, ans_index = int(data[1]), int(data[2])
    quiz_data = active_quizzes.get(uid)
    if not quiz_data:
        bot.answer_callback_query(call.id, "Ошибка. Тест не активен.")
        return
    quiz = quiz_data['quiz']
    q = quiz['questions'][q_index]
    correct = q['correct_answer']
    
    # Экранируем текст правильного ответа
    correct_answer_text = html.escape(q['options'][correct])
    
    if ans_index == correct:
        quiz_data['score'] += q['points']
        bot.answer_callback_query(call.id, f"✅ Правильно! +{q['points']}")
    else:
        bot.answer_callback_query(call.id, f"❌ Неверно. Правильный ответ: {correct_answer_text}")
    
    bot.delete_message(uid, call.message.message_id)
    quiz_data['current'] += 1
    send_quiz_question(uid)


def finish_quiz(chat_id):
    data = active_quizzes.pop(chat_id, None)
    if not data:
        return
    quiz = data['quiz']
    score = data['score']
    max_score = quiz['total_points']
    finalize_quiz_for_user(chat_id, quiz['quiz_id'], score, max_score)
    percent = round(score / max_score * 100, 1)
    
    # Создаем клавиатуру с кнопкой возврата в главное меню
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_main'))
    
    bot.send_message(
        chat_id, 
        f"🎉 Тест завершён!\n\n<b>{quiz['title']}</b>\n"
        f"Ваш результат: {score}/{max_score} ({percent}%)",
        parse_mode='HTML',
        reply_markup=markup  # Добавляем кнопку
    )


if __name__ == "__main__":
    log("🚀 Main bot запущен")
    bot.infinity_polling()

