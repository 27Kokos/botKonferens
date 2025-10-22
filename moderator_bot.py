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
USER_STATES_FILE = 'user_states.json'

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

def load_user_states():
    return load_data(USER_STATES_FILE)

def save_user_states(data):
    return save_data(data, USER_STATES_FILE)

def is_moderator(user_id):
    """Проверка, является ли пользователь модератором"""
    moderation_db = load_moderation_db()
    return user_id in moderation_db.get('moderators', [])

def get_pending_suggestions():
    """Получить ожидающие предложения"""
    moderation_db = load_moderation_db()
    return [s for s in moderation_db.get('moderation_queue', []) if s['status'] == 'pending']

def get_processed_suggestions(limit=10):
    """Получить обработанные предложения"""
    moderation_db = load_moderation_db()
    all_suggestions = moderation_db.get('moderation_queue', [])
    processed = [s for s in all_suggestions if s['status'] in ['approved', 'rejected']]
    return sorted(processed, key=lambda x: x.get('processed_date', x['timestamp']), reverse=True)[:limit]

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

def reset_all_users_progress():
    """Полный сброс статистики ВСЕХ пользователей"""
    users = load_users()
    
    for user_id, user_data in users.items():
        user_data['total_points'] = 0
        user_data['progress']['articles_viewed'] = {}
        user_data['progress']['quizzes_completed'] = {}
        user_data['progress']['achievements'] = []
        user_data['stats']['quizzes_taken'] = 0
        user_data['stats']['articles_read'] = 0
        user_data['stats']['average_score'] = 0
        user_data['stats']['total_reading_time'] = 0
        user_data['stats']['languages_learned'] = []
    
    return save_users(users)

def delete_all_users():
    """Удаление ВСЕХ пользователей"""
    # Очищаем файл users.json
    users = {}
    users_saved = save_users(users)
    
    # Очищаем файл user_states.json
    user_states = {}
    states_saved = save_user_states(user_states)
    
    return users_saved and states_saved

def get_user_by_id(user_id):
    """Найти пользователя по ID"""
    users = load_users()
    return users.get(str(user_id))

def get_all_users():
    """Получить всех пользователей"""
    return load_users()

@moderator_bot.message_handler(commands=['start'])
def moderator_start(message):
    """Стартовая команда для модераторов"""
    if not is_moderator(message.chat.id):
        moderator_bot.send_message(message.chat.id, "❌ У вас нет прав модератора.")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📋 Очередь предложений', callback_data='mod_queue'))
    markup.add(types.InlineKeyboardButton('📜 История предложений', callback_data='mod_history'))
    markup.add(types.InlineKeyboardButton('📊 Статистика', callback_data='mod_stats'))
    markup.add(types.InlineKeyboardButton('👤 Управление пользователями', callback_data='mod_users'))
    markup.add(types.InlineKeyboardButton('⚠️ Опасные действия', callback_data='danger_zone'))
    
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
    elif call.data == 'mod_history':
        show_suggestion_history(call.message.chat.id, call.message.message_id)
    elif call.data == 'mod_stats':
        show_moderation_stats(call.message.chat.id, call.message.message_id)
    elif call.data == 'mod_users':
        show_user_management(call.message.chat.id, call.message.message_id)
    elif call.data == 'mod_main':
        moderator_start(call.message)

@moderator_bot.callback_query_handler(func=lambda call: call.data == 'danger_zone')
def show_danger_zone(call):
    """Показать опасные действия"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔄 Сбросить статистику ВСЕХ пользователей', callback_data='reset_all_stats'))
    markup.add(types.InlineKeyboardButton('🗑 Удалить ВСЕХ пользователей', callback_data='delete_all_users'))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='mod_main'))
    
    moderator_bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="⚠️ <b>Опасная зона</b>\n\n"
             "Здесь находятся действия, которые влияют на ВСЕХ пользователей:\n\n"
             "🔄 <b>Сброс статистики</b> - обнулит очки, прогресс и достижения у всех пользователей\n"
             "🗑 <b>Удаление пользователей</b> - полностью очистит базу пользователей\n\n"
             "<b>ВНИМАНИЕ:</b> Эти действия необратимы!",
        reply_markup=markup,
        parse_mode='HTML'
    )

@moderator_bot.callback_query_handler(func=lambda call: call.data == 'reset_all_stats')
def handle_reset_all_stats(call):
    """Обработка сброса статистики всех пользователей"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Да, сбросить всю статистику', callback_data='confirm_reset_all'))
    markup.add(types.InlineKeyboardButton('❌ Отмена', callback_data='danger_zone'))
    
    moderator_bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="⚠️ <b>Подтверждение сброса статистики</b>\n\n"
             "Вы уверены, что хотите сбросить статистику ВСЕХ пользователей?\n\n"
             "Это действие:\n"
             "• Обнулит все очки\n"
             "• Удалит весь прогресс по статьям\n"
             "• Удалит все пройденные тесты\n"
             "• Удалит все достижения\n"
             "• Сбросит всю статистику\n\n"
             "<b>Действие необратимо!</b>",
        reply_markup=markup,
        parse_mode='HTML'
    )

@moderator_bot.callback_query_handler(func=lambda call: call.data == 'confirm_reset_all')
def confirm_reset_all_stats(call):
    """Подтверждение сброса статистики всех пользователей"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    success = reset_all_users_progress()
    
    if success:
        users_count = len(get_all_users())
        text = f"✅ <b>Статистика сброшена!</b>\n\nСтатистика {users_count} пользователей была полностью обнулена."
    else:
        text = "❌ <b>Ошибка при сбросе статистики</b>"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад в опасную зону', callback_data='danger_zone'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=markup,
        parse_mode='HTML'
    )

@moderator_bot.callback_query_handler(func=lambda call: call.data == 'delete_all_users')
def handle_delete_all_users(call):
    """Обработка удаления всех пользователей"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Да, удалить всех пользователей', callback_data='confirm_delete_all'))
    markup.add(types.InlineKeyboardButton('❌ Отмена', callback_data='danger_zone'))
    
    users_count = len(get_all_users())
    
    moderator_bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"⚠️ <b>Подтверждение удаления пользователей</b>\n\n"
             f"Вы уверены, что хотите удалить ВСЕХ пользователей?\n\n"
             f"Это действие:\n"
             f"• Удалит {users_count} пользователей\n"
             f"• Очистит всю базу данных пользователей\n"
             f"• Удалит все состояния пользователей\n"
             f"• Пользователям придется регистрироваться заново\n\n"
             f"<b>Действие необратимо!</b>",
        reply_markup=markup,
        parse_mode='HTML'
    )

@moderator_bot.callback_query_handler(func=lambda call: call.data == 'confirm_delete_all')
def confirm_delete_all_users(call):
    """Подтверждение удаления всех пользователей"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    users_count = len(get_all_users())
    success = delete_all_users()
    
    if success:
        text = f"✅ <b>Все пользователи удалены!</b>\n\nБыло удалено {users_count} пользователей. База данных очищена."
    else:
        text = "❌ <b>Ошибка при удалении пользователей</b>"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад в опасную зону', callback_data='danger_zone'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=markup,
        parse_mode='HTML'
    )

def show_moderation_queue(chat_id, message_id=None):
    """Показать очередь модерации"""
    if message_id:
        moderator_bot.delete_message(chat_id, message_id)
    
    pending_suggestions = get_pending_suggestions()
    
    if not pending_suggestions:
        text = "📋 <b>Очередь предложений</b>\n\nНет ожидающих рассмотрения предложений."
    else:
        text = f"📋 <b>Очередь предложений</b>\n\nОжидают рассмотрения: {len(pending_suggestions)}\n\n"
        
        for i, suggestion in enumerate(pending_suggestions[:5]):
            text += f"{i+1}. 👤 {suggestion['user_data']['first_name']}\n"
            text += f"   💬 {suggestion['content'][:50]}...\n"
            text += f"   ⏰ {suggestion['timestamp']}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    if pending_suggestions:
        markup.add(types.InlineKeyboardButton('👀 Просмотреть предложения', callback_data='view_suggestions'))
    markup.add(types.InlineKeyboardButton('📜 История предложений', callback_data='mod_history'))
    markup.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='mod_queue'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

def show_suggestion_history(chat_id, message_id=None):
    """Показать историю предложений"""
    if message_id:
        moderator_bot.delete_message(chat_id, message_id)
    
    processed_suggestions = get_processed_suggestions(10)
    
    if not processed_suggestions:
        text = "📜 <b>История предложений</b>\n\nНет обработанных предложений."
    else:
        text = "📜 <b>История предложений</b>\n\n"
        
        for i, suggestion in enumerate(processed_suggestions):
            status_emoji = "✅" if suggestion['status'] == 'approved' else "❌"
            text += f"{i+1}. {status_emoji} {suggestion['user_data']['first_name']}\n"
            text += f"   💬 {suggestion['content'][:50]}...\n"
            text += f"   ⏰ {suggestion['timestamp']}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    if processed_suggestions:
        markup.add(types.InlineKeyboardButton('📋 Подробная история', callback_data='view_detailed_history'))
    markup.add(types.InlineKeyboardButton('📋 Текущая очередь', callback_data='mod_queue'))
    markup.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='mod_history'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

@moderator_bot.callback_query_handler(func=lambda call: call.data == 'view_detailed_history')
def view_detailed_history(call):
    """Просмотр детальной истории"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    processed_suggestions = get_processed_suggestions(20)
    
    if not processed_suggestions:
        moderator_bot.answer_callback_query(call.id, "❌ Нет истории предложений")
        return
    
    show_detailed_suggestion(call.message.chat.id, call.message.message_id, processed_suggestions[0], 0)

def show_detailed_suggestion(chat_id, message_id, suggestion, index):
    """Показать детали обработанного предложения"""
    if message_id:
        moderator_bot.delete_message(chat_id, message_id)
    
    processed_suggestions = get_processed_suggestions(20)
    
    status_text = "✅ Одобрено" if suggestion['status'] == 'approved' else "❌ Отклонено"
    moderator_info = f"Модератор: {suggestion.get('moderator_id', 'Неизвестно')}"
    processed_date = suggestion.get('processed_date', 'Не указано')
    
    text = (
        f"📜 <b>История предложений</b> ({index + 1}/{len(processed_suggestions)})\n\n"
        f"👤 <b>Пользователь:</b> {suggestion['user_data']['first_name']}\n"
        f"📛 <b>Username:</b> @{suggestion['user_data']['username'] or 'нет'}\n"
        f"🆔 <b>ID:</b> {suggestion['user_id']}\n"
        f"⏰ <b>Отправлено:</b> {suggestion['timestamp']}\n"
        f"📊 <b>Статус:</b> {status_text}\n"
        f"👨‍💼 <b>{moderator_info}</b>\n"
        f"⏱ <b>Обработано:</b> {processed_date}\n\n"
        f"💬 <b>Текст предложения:</b>\n{suggestion['content']}\n"
    )
    
    if suggestion.get('response'):
        text += f"\n💭 <b>Ответ модератора:</b>\n{suggestion['response']}\n"
    
    markup = types.InlineKeyboardMarkup()
    
    # Кнопки навигации
    nav_buttons = []
    if index > 0:
        nav_buttons.append(types.InlineKeyboardButton('⬅️ Предыдущее', callback_data=f'history_prev_{index}'))
    if index < len(processed_suggestions) - 1:
        nav_buttons.append(types.InlineKeyboardButton('➡️ Следующее', callback_data=f'history_next_{index}'))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    markup.add(types.InlineKeyboardButton('📜 Назад к истории', callback_data='mod_history'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

@moderator_bot.callback_query_handler(func=lambda call: call.data.startswith(('history_prev_', 'history_next_')))
def handle_history_navigation(call):
    """Навигация по истории"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    action, index = call.data.split('_', 2)
    current_index = int(index)
    
    processed_suggestions = get_processed_suggestions(20)
    
    if not processed_suggestions:
        moderator_bot.answer_callback_query(call.id, "❌ Нет истории")
        return
    
    if action == 'prev' and current_index > 0:
        new_index = current_index - 1
    elif action == 'next' and current_index < len(processed_suggestions) - 1:
        new_index = current_index + 1
    else:
        moderator_bot.answer_callback_query(call.id, "❌ Достигнут предел")
        return
    
    show_detailed_suggestion(call.message.chat.id, call.message.message_id, processed_suggestions[new_index], new_index)

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
    
    users = get_all_users()
    
    text = (
        "👤 <b>Управление пользователями</b>\n\n"
        f"📊 Всего пользователей: {len(users)}\n\n"
        "Функции управления:"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📋 Список пользователей', callback_data='user_list'))
    markup.add(types.InlineKeyboardButton('🔍 Поиск пользователя по ID', callback_data='user_search'))
    markup.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='mod_users'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

# Функции для работы с предложениями (из предыдущей версии)
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
    show_suggestion_detail(call.message.chat.id, call.message.message_id, pending_suggestions[0], 0)

def show_suggestion_detail(chat_id, message_id, suggestion, index):
    """Показать детали предложения"""
    if message_id:
        moderator_bot.delete_message(chat_id, message_id)
    
    pending_suggestions = get_pending_suggestions()
    
    text = (
        f"📋 <b>Предложение {index + 1} из {len(pending_suggestions)}</b>\n\n"
        f"👤 <b>Пользователь:</b> {suggestion['user_data']['first_name']}\n"
        f"📛 <b>Username:</b> @{suggestion['user_data']['username'] or 'нет'}\n"
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
    
    # Кнопки навигации
    nav_buttons = []
    if index > 0:
        nav_buttons.append(types.InlineKeyboardButton('⬅️ Предыдущее', callback_data=f'prev_{index}'))
    if index < len(pending_suggestions) - 1:
        nav_buttons.append(types.InlineKeyboardButton('➡️ Следующее', callback_data=f'next_{index}'))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
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
        show_suggestion_detail(call.message.chat.id, call.message.message_id, pending_suggestions[0], 0)
    else:
        show_moderation_queue(call.message.chat.id, call.message.message_id)

@moderator_bot.callback_query_handler(func=lambda call: call.data.startswith(('prev_', 'next_')))
def handle_suggestion_navigation(call):
    """Навигация по предложениям"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    action, index = call.data.split('_', 1)
    current_index = int(index)
    
    pending_suggestions = get_pending_suggestions()
    
    if not pending_suggestions:
        moderator_bot.answer_callback_query(call.id, "❌ Нет предложений")
        return
    
    if action == 'prev' and current_index > 0:
        new_index = current_index - 1
    elif action == 'next' and current_index < len(pending_suggestions) - 1:
        new_index = current_index + 1
    else:
        moderator_bot.answer_callback_query(call.id, "❌ Достигнут предел")
        return
    
    show_suggestion_detail(call.message.chat.id, call.message.message_id, pending_suggestions[new_index], new_index)

@moderator_bot.callback_query_handler(func=lambda call: call.data == 'user_list')
def show_user_list(call):
    """Показать список пользователей"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    users = get_all_users()
    
    if not users:
        moderator_bot.send_message(call.message.chat.id, "❌ Нет зарегистрированных пользователей.")
        return
    
    # Показываем первого пользователя
    user_ids = list(users.keys())
    show_user_detail(call.message.chat.id, call.message.message_id, users[user_ids[0]], user_ids[0], 0, user_ids)

def show_user_detail(chat_id, message_id, user, user_id, index, user_ids):
    """Показать детали пользователя"""
    if message_id:
        moderator_bot.delete_message(chat_id, message_id)
    
    text = (
        f"👤 <b>Пользователь {index + 1}/{len(user_ids)}</b>\n\n"
        f"🆔 <b>ID:</b> {user_id}\n"
        f"👨‍💼 <b>Имя:</b> {user['first_name']}\n"
        f"📛 <b>Username:</b> @{user['username'] or 'нет'}\n"
        f"📅 <b>Зарегистрирован:</b> {user['joined_date']}\n"
        f"🏆 <b>Очки:</b> {user['total_points']}\n"
        f"📚 <b>Статей прочитано:</b> {user['stats']['articles_read']}\n"
        f"🧠 <b>Тестов пройдено:</b> {user['stats']['quizzes_taken']}\n"
        f"📈 <b>Средний балл:</b> {user['stats']['average_score']}%\n"
        f"🌍 <b>Изучаемые языки:</b> {', '.join(user['stats']['languages_learned']) if user['stats']['languages_learned'] else 'нет'}\n"
    )
    
    markup = types.InlineKeyboardMarkup()
    
    # Кнопки сброса прогресса
    markup.row(
        types.InlineKeyboardButton('🔄 Полный сброс', callback_data=f'reset_full_{user_id}'),
        types.InlineKeyboardButton('📚 Сброс статей', callback_data=f'reset_articles_{user_id}')
    )
    markup.row(
        types.InlineKeyboardButton('🧠 Сброс тестов', callback_data=f'reset_quizzes_{user_id}'),
        types.InlineKeyboardButton('⭐ Сброс очков', callback_data=f'reset_points_{user_id}')
    )
    
    # Кнопки навигации
    nav_buttons = []
    if index > 0:
        nav_buttons.append(types.InlineKeyboardButton('⬅️ Предыдущий', callback_data=f'user_prev_{index}'))
    if index < len(user_ids) - 1:
        nav_buttons.append(types.InlineKeyboardButton('➡️ Следующий', callback_data=f'user_next_{index}'))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    markup.add(types.InlineKeyboardButton('📋 Назад к списку', callback_data='mod_users'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='mod_main'))
    
    moderator_bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')

@moderator_bot.callback_query_handler(func=lambda call: call.data.startswith(('user_prev_', 'user_next_')))
def handle_user_navigation(call):
    """Навигация по пользователям"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    parts = call.data.split('_')
    action = parts[1]
    current_index = int(parts[2])
    
    users = get_all_users()
    user_ids = list(users.keys())
    
    if not user_ids:
        moderator_bot.answer_callback_query(call.id, "❌ Нет пользователей")
        return
    
    if action == 'prev' and current_index > 0:
        new_index = current_index - 1
    elif action == 'next' and current_index < len(user_ids) - 1:
        new_index = current_index + 1
    else:
        moderator_bot.answer_callback_query(call.id, "❌ Достигнут предел")
        return
    
    show_user_detail(call.message.chat.id, call.message.message_id, users[user_ids[new_index]], user_ids[new_index], new_index, user_ids)

@moderator_bot.callback_query_handler(func=lambda call: call.data.startswith('reset_'))
def handle_reset_progress(call):
    """Обработка сброса прогресса"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    parts = call.data.split('_')
    reset_type = parts[1]
    user_id = parts[2]
    
    reset_types = {
        'full': 'полный сброс прогресса',
        'articles': 'сброс прочитанных статей', 
        'quizzes': 'сброс результатов тестов',
        'points': 'обнуление очков'
    }
    
    success = reset_user_progress(int(user_id), reset_type)
    
    if success:
        moderator_bot.answer_callback_query(call.id, f"✅ {reset_types[reset_type]} выполнен")
        # Обновляем информацию о пользователе
        users = get_all_users()
        user_ids = list(users.keys())
        if user_id in users:
            current_index = user_ids.index(user_id)
            show_user_detail(call.message.chat.id, call.message.message_id, users[user_id], user_id, current_index, user_ids)
    else:
        moderator_bot.answer_callback_query(call.id, "❌ Ошибка при сбросе прогресса")

@moderator_bot.callback_query_handler(func=lambda call: call.data == 'user_search')
def handle_user_search(call):
    """Обработка поиска пользователя"""
    if not is_moderator(call.message.chat.id):
        moderator_bot.answer_callback_query(call.id, "❌ Нет прав доступа")
        return
    
    msg = moderator_bot.send_message(call.message.chat.id, "🔍 Введите ID пользователя для поиска:")
    moderator_bot.register_next_step_handler(msg, process_user_search)

def process_user_search(message):
    """Обработка введенного ID пользователя"""
    try:
        user_id = int(message.text.strip())
    except ValueError:
        moderator_bot.send_message(message.chat.id, "❌ Неверный формат ID. Введите числовой ID.")
        return
    
    user = get_user_by_id(user_id)
    if not user:
        moderator_bot.send_message(message.chat.id, f"❌ Пользователь с ID {user_id} не найден.")
        return
    
    # Показываем информацию о пользователе
    users = get_all_users()
    user_ids = list(users.keys())
    if str(user_id) in user_ids:
        index = user_ids.index(str(user_id))
        show_user_detail(message.chat.id, None, user, str(user_id), index, user_ids)

if __name__ == "__main__":
    print("Модератор бот запущен...")
    moderator_bot.polling(none_stop=True)