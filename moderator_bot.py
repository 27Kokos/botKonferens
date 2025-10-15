import telebot
from telebot import types
import json
import os
from datetime import datetime


# Инициализация бота-модератора
moderator_bot = telebot.TeleBot('8339489199:AAELTq_I7ge6_3p_GQ-IeZhT8liL47v7xaI')

# Файлы данных
MODERATION_DB_FILE = 'moderation_db.json'
USERS_FILE = 'users.json'

def load_data(file_path):
    """Загрузка данных из JSON файла"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Ошибка при декодировании JSON {file_path}")
            return {}
    return {}

def save_data(data, file_path):
    """Сохранение данных в JSON файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении данных {file_path}: {e}")
        return False

def load_moderation_db():
    return load_data(MODERATION_DB_FILE)

def save_moderation_db(data):
    return save_data(data, MODERATION_DB_FILE)

def load_users():
    return load_data(USERS_FILE)

def save_users(data):
    return save_data(data, USERS_FILE)

def is_moderator(user_id):
    """Проверка, является ли пользователь модератором"""
    moderation_db = load_moderation_db()
    return user_id in moderation_db.get('moderators', [])

def reset_user_progress(user_id, reset_type="full"):
    """Сброс прогресса пользователя"""
    users = load_users()
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        return False
    
    user = users[user_id_str]
    
    if reset_type == "full" or reset_type == "quizzes":
        user['progress']['quizzes_completed'] = {}
        user['stats']['quizzes_taken'] = 0
        user['stats']['average_score'] = 0
    
    if reset_type == "full" or reset_type == "articles":
        user['progress']['articles_viewed'] = {}
        user['stats']['articles_read'] = 0
        user['stats']['languages_learned'] = []
    
    if reset_type == "full" or reset_type == "points":
        user['total_points'] = 0
    
    if reset_type == "full" or reset_type == "achievements":
        user['progress']['achievements'] = []
    
    return save_users(users)

def get_pending_suggestions():
    """Получить ожидающие предложения"""
    moderation_db = load_moderation_db()
    return [s for s in moderation_db.get('moderation_queue', []) if s['status'] == 'pending']

def update_suggestion_status(suggestion_id, status, moderator_id, response=None):
    """Обновить статус предложения"""
    moderation_db = load_moderation_db()
    
    for suggestion in moderation_db['moderation_queue']:
        if suggestion['id'] == suggestion_id:
            suggestion['status'] = status
            suggestion['moderator_id'] = moderator_id
            suggestion['response'] = response
            suggestion['processed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    
    # Обновляем статистику
    stats = moderation_db['suggestion_stats']
    stats['pending'] = len([s for s in moderation_db['moderation_queue'] if s['status'] == 'pending'])
    
    if status == 'approved':
        stats['approved'] += 1
    elif status == 'rejected':
        stats['rejected'] += 1
    
    return save_moderation_db(moderation_db)

@moderator_bot.message_handler(commands=['start'])
def moderator_start(message):
    """Стартовая команда для модераторов"""
    if not is_moderator(message.chat.id):
        moderator_bot.send_message(message.chat.id, "❌ У вас нет прав модератора.")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📋 Очередь предложений', callback_data='mod_queue'))
    markup.add(types.InlineKeyboardButton('📊 Статистика', callback_data='mod_stats'))
    markup.add(types.InlineKeyboardButton('👤 Управление пользователями', callback_data='mod_users'))
    
    moderator_bot.send_message(
        message.chat.id,
        "🛠 <b>Панель модератора CodeForge</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=markup,
        parse_mode='HTML'
    )

@moderator_bot.callback_query_handler(func=lambda call: call.data.startswith('mod_'))
def handle_moderator_actions(call):
    """Обработка действий модератора"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    if call.data == 'mod_queue':
        show_moderation_queue(call.message.chat.id, call.message.message_id)
    elif call.data == 'mod_stats':
        show_moderation_stats(call.message.chat.id, call.message.message_id)
    elif call.data == 'mod_users':
        show_user_management(call.message.chat.id, call.message.message_id)
    elif call.data == 'mod_main':
        moderator_start(call.message)

def show_moderation_queue(chat_id, message_id=None):
    """Показать очередь модерации"""
    if message_id:
        moderator_bot.delete_message(chat_id, message_id)
    
    pending_suggestions = get_pending_suggestions()
    
    if not pending_suggestions:
        text = "📋 <b>Очередь предложений</b>\n\nНет ожидающих рассмотрения предложений."
    else:
        text = f"📋 <b>Очередь предложений</b>\n\nОжидают рассмотрения: {len(pending_suggestions)}\n\n"
        
        for i, suggestion in enumerate(pending_suggestions[:5]):  # Показываем первые 5
            text += f"{i+1}. 👤 {suggestion['user_data']['first_name']}\n"
            text += f"   💬 {suggestion['content'][:50]}...\n"
            text += f"   ⏰ {suggestion['timestamp']}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    if pending_suggestions:
        markup.add(types.InlineKeyboardButton('👀 Просмотреть предложения', callback_data='view_suggestions'))
    markup.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='mod_queue'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

def show_moderation_stats(chat_id, message_id=None):
    """Показать статистику модерации"""
    if message_id:
        moderator_bot.delete_message(chat_id, message_id)
    
    moderation_db = load_moderation_db()
    stats = moderation_db.get('suggestion_stats', {})
    
    text = (
        "📊 <b>Статистика модерации</b>\n\n"
        f"📨 Всего предложений: {stats.get('total', 0)}\n"
        f"✅ Одобрено: {stats.get('approved', 0)}\n"
        f"❌ Отклонено: {stats.get('rejected', 0)}\n"
        f"⏳ Ожидают: {stats.get('pending', 0)}\n"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='mod_stats'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

def show_user_management(chat_id, message_id=None):
    """Показать управление пользователями"""
    if message_id:
        moderator_bot.delete_message(chat_id, message_id)
    
    users = load_users()
    
    text = (
        "👤 <b>Управление пользователями</b>\n\n"
        f"📊 Всего пользователей: {len(users)}\n\n"
        "Функции управления:"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📋 Список пользователей', callback_data='user_list'))
    markup.add(types.InlineKeyboardButton('🔍 Поиск пользователя', callback_data='user_search'))
    markup.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='mod_users'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

# Новые функции для работы с предложениями
@moderator_bot.callback_query_handler(func=lambda call: call.data == 'view_suggestions')
def view_suggestions(call):
    """Просмотр предложений"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    pending_suggestions = get_pending_suggestions()
    
    if not pending_suggestions:
        moderator_bot.answer_callback_query(call.id, "❌ Нет ожидающих предложений")
        return
    
    # Показываем первое предложение
    show_suggestion_detail(call.message.chat.id, call.message.message_id, pending_suggestions[0])

def show_suggestion_detail(chat_id, message_id, suggestion):
    """Показать детали предложения"""
    if message_id:
        moderator_bot.delete_message(chat_id, message_id)
    
    text = (
        f"📋 <b>Предложение от пользователя</b>\n\n"
        f"👤 <b>Пользователь:</b> {suggestion['user_data']['first_name']}\n"
        f"📛 <b>Username:</b> @{suggestion['user_data']['username']}\n"
        f"🆔 <b>ID:</b> {suggestion['user_id']}\n"
        f"⏰ <b>Время:</b> {suggestion['timestamp']}\n\n"
        f"💬 <b>Текст предложения:</b>\n{suggestion['content']}\n\n"
        f"<b>Выберите действие:</b>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('✅ Одобрить', callback_data=f'approve_{suggestion["id"]}'),
        types.InlineKeyboardButton('❌ Отклонить', callback_data=f'reject_{suggestion["id"]}')
    )
    markup.add(types.InlineKeyboardButton('⏭ Следующее', callback_data='view_suggestions'))
    markup.add(types.InlineKeyboardButton('📋 Назад к очереди', callback_data='mod_queue'))
    
    moderator_bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

@moderator_bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_suggestion_decision(call):
    """Обработка решения по предложению"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    action, suggestion_id = call.data.split('_', 1)
    
    # Находим предложение
    moderation_db = load_moderation_db()
    suggestion = None
    for s in moderation_db['moderation_queue']:
        if s['id'] == suggestion_id:
            suggestion = s
            break
    
    if not suggestion:
        moderator_bot.answer_callback_query(call.id, "❌ Предложение не найдено")
        return
    
    if action == 'approve':
        update_suggestion_status(suggestion_id, 'approved', call.from_user.id)
        moderator_bot.answer_callback_query(call.id, "✅ Предложение одобрено")
    else:
        update_suggestion_status(suggestion_id, 'rejected', call.from_user.id)
        moderator_bot.answer_callback_query(call.id, "❌ Предложение отклонено")
    
    # Показываем следующее предложение или возвращаем в очередь
    pending_suggestions = get_pending_suggestions()
    if pending_suggestions:
        show_suggestion_detail(call.message.chat.id, call.message.message_id, pending_suggestions[0])
    else:
        show_moderation_queue(call.message.chat.id, call.message.message_id)

if __name__ == '__main__':
    print("Бот-модератор запущен...")
    moderator_bot.polling(none_stop=True)