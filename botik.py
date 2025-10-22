import telebot
from telebot import types
import json
import os
from datetime import datetime
import html
import sys
import codecs

# Устанавливаем кодировку UTF-8 для вывода в консоль
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Инициализация бота
bot = telebot.TeleBot('8317740647:AAEsqXPmGOrZSgDbaIMUnJPvnBO_ZYFvfgQ') 

# Файлы данных
USER_STATES_FILE = 'user_states.json'
USERS_FILE = 'users.json'
QUIZZES_FILE = 'quizzes.json'
LEADERBOARD_FILE = 'leaderboard.json'
ARTICLES_FILE = 'articles.json'
MODERATION_DB_FILE = 'moderation_db.json'

# Загрузка и сохранение данных
def load_data(file_path):
    """Загрузка данных из JSON файла"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Ошибка при декодировании JSON {file_path}. Файл может быть поврежден.")
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

def load_articles():
    """Загрузка структуры статей"""
    return load_data(ARTICLES_FILE)

def get_article(language, article_key):
    """Получение данных статьи"""
    articles = load_articles()
    return articles.get(language, {}).get(article_key)

def mark_article_as_read(user_id, language, article_key):
    """Пометить статью как прочитанную"""
    users = load_data(USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        return False
    
    user = users[user_id_str]
    
    # Инициализируем структуру если нет
    if 'articles_viewed' not in user['progress']:
        user['progress']['articles_viewed'] = {}
    
    if language not in user['progress']['articles_viewed']:
        user['progress']['articles_viewed'][language] = []
    
    # Проверяем, не прочитана ли уже статья
    if article_key not in user['progress']['articles_viewed'][language]:
        user['progress']['articles_viewed'][language].append(article_key)
        
        # Начисляем очки за прочтение
        article = get_article(language, article_key)
        if article:
            user['total_points'] += article.get('points', 10)
        
        # Обновляем статистику
        user['stats']['articles_read'] = sum(len(articles) for articles in user['progress']['articles_viewed'].values())
        
        # Обновляем изученные языки
        user['stats']['languages_learned'] = list(user['progress']['articles_viewed'].keys())
        
        save_data(users, USERS_FILE)
        
        # Обновляем лидерборд
        update_leaderboard()
        
        return True
    
    return False

def load_moderation_db():
    """Загрузка базы модерации"""
    return load_data(MODERATION_DB_FILE)

def save_moderation_db(data):
    """Сохранение базы модерации"""
    return save_data(data, MODERATION_DB_FILE)

def add_suggestion_to_moderation(user_id, username, first_name, suggestion_text):
    """Добавление предложения в очередь модерации"""
    moderation_db = load_moderation_db()
    
    if 'moderation_queue' not in moderation_db:
        moderation_db['moderation_queue'] = []
    
    suggestion = {
        "id": f"{user_id}_{int(datetime.now().timestamp())}",
        "type": "suggestion",
        "user_id": user_id,
        "user_data": {
            "username": username,
            "first_name": first_name
        },
        "content": suggestion_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
        "moderator_id": None,
        "response": None
    }
    
    moderation_db['moderation_queue'].append(suggestion)
    
    # Обновляем статистику
    if 'suggestion_stats' not in moderation_db:
        moderation_db['suggestion_stats'] = {"total": 0, "approved": 0, "rejected": 0, "pending": 0}
    
    moderation_db['suggestion_stats']['total'] += 1
    moderation_db['suggestion_stats']['pending'] += 1
    
    return save_moderation_db(moderation_db)

def get_user_articles_progress(user_id, language):
    """Получить прогресс по статьям для языка"""
    users = load_data(USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        return []
    
    user = users[user_id_str]
    return user['progress']['articles_viewed'].get(language, [])

def init_user(user_id, username, first_name):
    """Инициализация нового пользователя"""
    users = load_data(USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        users[user_id_str] = {
            "user_id": user_id,
            "username": username or "без username",
            "first_name": first_name or "Пользователь",
            "joined_date": datetime.now().strftime("%Y-%m-%d"),
            "total_points": 0,
            "progress": {
                "articles_viewed": {},
                "quizzes_completed": {},
                "achievements": []
            },
            "stats": {
                "quizzes_taken": 0,
                "articles_read": 0,
                "average_score": 0,
                "total_reading_time": 0,
                "languages_learned": []
            }
        }
        save_data(users, USERS_FILE)
        print(f"Создан новый пользователь: {username or first_name or 'без имени'}")
    
    return users[user_id_str]

def update_user_progress(user_id, data):
    """Обновление данных пользователя"""
    users = load_data(USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str in users:
        users[user_id_str].update(data)
        save_data(users, USERS_FILE)
        return True
    return False

def get_quiz(quiz_id):
    """Получение данных квиза"""
    quizzes = load_data(QUIZZES_FILE)
    return quizzes.get(quiz_id)

def update_user_after_quiz(user_id, quiz_id, score, max_score):
    """Обновление статистики пользователя после прохождения теста"""
    users = load_data(USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str in users:
        user = users[user_id_str]
        
        # Обновляем пройденные тесты
        user['progress']['quizzes_completed'][quiz_id] = {
            'score': score,
            'max_score': max_score,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Обновляем общие очки
        user['total_points'] += score
        
        # Обновляем статистику
        user['stats']['quizzes_taken'] += 1
        
        # Пересчитываем средний балл
        total_quizzes = user['stats']['quizzes_taken']
        if total_quizzes > 0:
            total_score = sum([q['score'] for q in user['progress']['quizzes_completed'].values()])
            total_max = sum([q['max_score'] for q in user['progress']['quizzes_completed'].values()])
            user['stats']['average_score'] = round((total_score / total_max) * 100, 2) if total_max > 0 else 0
        
        # Добавляем достижения
        if score == max_score and 'perfect_score' not in user['progress']['achievements']:
            user['progress']['achievements'].append('perfect_score')
        if total_quizzes == 1 and 'first_quiz' not in user['progress']['achievements']:
            user['progress']['achievements'].append('first_quiz')
        
        save_data(users, USERS_FILE)
        
        # Обновляем лидерборд
        update_leaderboard()
        
        return True
    return False

# Функции лидерборда
def update_leaderboard():
    """Обновление лидерборда"""
    users = load_data(USERS_FILE)
    leaderboard = load_data(LEADERBOARD_FILE)
    
    # Общий рейтинг (по общим очкам)
    ranking = []
    for user_id, user_data in users.items():
        ranking.append({
            "user_id": int(user_id),
            "username": user_data['username'],
            "first_name": user_data['first_name'],
            "total_points": user_data['total_points'],
            "quizzes_taken": user_data['stats']['quizzes_taken'],
            "articles_read": user_data['stats']['articles_read']
        })
    
    # Сортируем по очкам (по убыванию)
    ranking.sort(key=lambda x: x['total_points'], reverse=True)
    
    # Добавляем ранги
    for i, user in enumerate(ranking):
        user['rank'] = i + 1
    
    leaderboard['ranking'] = ranking
    leaderboard['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    save_data(leaderboard, LEADERBOARD_FILE)
    return leaderboard

def get_leaderboard_display_name(user_data):
    """Получить отображаемое имя пользователя"""
    if user_data.get('username'):
        return f"@{user_data['username']}"
    else:
        return user_data['first_name']

def show_leaderboard(chat_id, message_id=None):
    """Показать лидерборд"""
    if message_id:
        bot.delete_message(chat_id, message_id)
    
    # Обновляем лидерборд перед показом
    leaderboard = update_leaderboard()
    
    ranking = leaderboard['ranking'][:15]  # Топ-15
    last_updated = leaderboard['last_updated']
    
    leaderboard_text = "🏆 <b>Общий рейтинг</b>\n\n"
    
    if not ranking:
        leaderboard_text += "📊 Пока никто не заработал очков.\nБудьте первым!"
    else:
        for i, user in enumerate(ranking):
            medal = ""
            if i == 0: medal = "🥇"
            elif i == 1: medal = "🥈" 
            elif i == 2: medal = "🥉"
            else: medal = f"{i+1}."
            
            leaderboard_text += (
                f"{medal} <b>{get_leaderboard_display_name(user)}</b>\n"
                f"   ⭐ {user['total_points']} очков | "
                f"📚 {user['articles_read']} статей | "
                f"🧠 {user['quizzes_taken']} тестов\n"
            )
    
    leaderboard_text += f"\n🕐 Обновлено: {last_updated}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔄 Обновить', callback_data='leaderboard'))
    markup.add(types.InlineKeyboardButton('📊 Мой прогресс', callback_data='progress'))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_main'))
    
    bot.send_message(chat_id, leaderboard_text, reply_markup=markup, parse_mode='HTML')
    
    user_states[str(chat_id)] = 'leaderboard'
    save_data(user_states, USER_STATES_FILE)

# Загрузка состояний пользователей
user_states = load_data(USER_STATES_FILE)
print("Загружены состояния пользователей:", user_states)

# Активные тесты пользователей {user_id: {quiz_data, current_question, answers}}
active_quizzes = {}

@bot.message_handler(commands=['start'])
def start(message):
    # Инициализируем пользователя
    user = init_user(
        message.chat.id, 
        message.from_user.username, 
        message.from_user.first_name
    )
    
    # Приветственное сообщение с HTML разметкой
    welcome_text = (
        f"👋 Привет, <b>{html.escape(message.from_user.first_name or 'Пользователь')}</b>!\n\n"
        f"🚀 Добро пожаловать в <b>CodeForge</b> - твою платформу для изучения программирования!\n\n"
        f"✨ <b>Здесь ты можешь:</b>\n"
        f"• 📚 Изучать материалы по разным языкам\n"
        f"• 🧠 Проверять знания в тестах\n"
        f"• 📊 Следить за своим прогрессом\n"
        f"• 🏆 Соревноваться в рейтинге\n"
        f"• 💡 Предлагать улучшения\n\n"
        f"<b>Выбери действие:</b>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📚 Языки программирования', callback_data='languages'))
    markup.add(types.InlineKeyboardButton('🧠 Пройти тест', callback_data='take_quiz'))
    markup.add(types.InlineKeyboardButton('📊 Мой прогресс', callback_data='progress'))
    markup.add(types.InlineKeyboardButton('🏆 Лидерборд', callback_data='leaderboard'))
    markup.add(types.InlineKeyboardButton('💡 Предложения', callback_data='predlozka'))
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')
    
    user_states[str(message.chat.id)] = 'main_menu'
    save_data(user_states, USER_STATES_FILE)

@bot.message_handler(commands=['progress'])
def progress_command(message):
    """Команда для просмотра прогресса"""
    show_progress(message.chat.id)

@bot.message_handler(commands=['leaderboard'])
def leaderboard_command(message):
    """Команда для просмотра лидерборда"""
    show_leaderboard(message.chat.id)

def show_progress(chat_id):
    """Показать прогресс пользователя"""
    users = load_data(USERS_FILE)
    user_id_str = str(chat_id)
    
    if user_id_str not in users:
        bot.send_message(chat_id, "Вы еще не начали обучение. Используйте /start")
        return
    
    user = users[user_id_str]
    
    # Статистика
    total_quizzes = user['stats']['quizzes_taken']
    total_articles = user['stats']['articles_read']
    avg_score = user['stats']['average_score']
    total_points = user['total_points']
    
    # Формируем сообщение с HTML разметкой
    progress_text = (
        f"📊 <b>Ваш прогресс в CodeForge</b>\n\n"
        f"👤 <b>{html.escape(user['first_name'])}</b>\n"
        f"📅 <b>Зарегистрирован:</b> {html.escape(user['joined_date'])}\n"
        f"🏆 <b>Всего очков:</b> {total_points}\n"
        f"📚 <b>Прочитано статей:</b> {total_articles}\n"
        f"🧠 <b>Пройдено тестов:</b> {total_quizzes}\n"
        f"📈 <b>Средний балл:</b> {avg_score}%\n"
    )
    
    # Добавляем прогресс по языкам
    if user['progress']['articles_viewed']:
        progress_text += "\n🌍 <b>Прогресс по языкам:</b>\n"
        articles_data = load_articles()
        
        for language, read_articles in user['progress']['articles_viewed'].items():
            total_articles_in_lang = len(articles_data.get(language, {}))
            if total_articles_in_lang > 0:
                percentage = (len(read_articles) / total_articles_in_lang) * 100
                progress_text += f"• <b>{language}</b>: {len(read_articles)}/{total_articles_in_lang} ({percentage:.1f}%)\n"
    
    # Добавляем информацию о пройденных тестах
    if user['progress']['quizzes_completed']:
        progress_text += "\n🎯 <b>Пройденные тесты:</b>\n"
        for quiz_name, result in user['progress']['quizzes_completed'].items():
            percentage = (result['score'] / result['max_score']) * 100
            progress_text += f"• <b>{html.escape(quiz_name)}</b>: {result['score']}/{result['max_score']} ({percentage:.1f}%)\n"
    
    # Добавляем достижения
    if user['progress']['achievements']:
        achievements_text = {
            'perfect_score': '🎖 Идеальный результат',
            'first_quiz': '🥇 Первый тест'
        }
        user_achievements = [achievements_text.get(a, a) for a in user['progress']['achievements']]
        progress_text += f"\n🏅 <b>Достижения:</b>\n" + "\n".join([f"• {a}" for a in user_achievements])
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📚 Изучать материалы', callback_data='languages'))
    markup.add(types.InlineKeyboardButton('🧠 Пройти тест', callback_data='take_quiz'))
    markup.add(types.InlineKeyboardButton('🏆 Лидерборд', callback_data='leaderboard'))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_main'))
    
    bot.send_message(chat_id, progress_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    user_id = callback.message.chat.id
    user_id_str = str(user_id)
    
    try:
        # Обработка основных действий
        if callback.data == 'languages':
            show_languages_menu(user_id, callback.message.message_id)
            
        elif callback.data == 'take_quiz':
            show_quiz_selection(user_id, callback.message.message_id)
        
        elif callback.data == 'progress':
            bot.delete_message(user_id, callback.message.message_id)
            show_progress(user_id)
        
        elif callback.data == 'predlozka': 
            bot.delete_message(user_id, callback.message.message_id)
            bot.send_message(user_id, 
                            '💡 <b>Напишите своё предложение:</b>\n\n'
                            'Мы ценим ваше мнение и постоянно работаем над улучшением бота!', 
                            parse_mode='HTML')
            user_states[user_id_str] = 'predlozka_menu'
            save_data(user_states, USER_STATES_FILE)
        
        # Обработка кнопки "Назад"
        elif callback.data == 'back_to_main':
            bot.delete_message(user_id, callback.message.message_id)
            start(callback.message)
        
        elif callback.data == 'back_to_languages':
            bot.delete_message(user_id, callback.message.message_id)
            show_languages_menu(user_id, None)
        
        # Обработка выбора языка
        elif callback.data in ['VBA', 'C', 'Bash', 'Python', 'JavaScript']:
            show_language_specific_menu(user_id, callback.data, callback.message.message_id)
        
        # Обработка выбора конкретного теста
        elif callback.data.startswith('quiz_'):
            quiz_id = callback.data[5:]  # Убираем 'quiz_'
            show_quiz_info(user_id, quiz_id, callback.message.message_id)
        
        # Обработка начала теста
        elif callback.data.startswith('start_quiz_'):
            quiz_id = callback.data[11:]  # Убираем 'start_quiz_'
            start_quiz(user_id, quiz_id, callback.message.message_id)
        
        # Обработка ответов в тесте
        elif callback.data.startswith('answer_'):
            handle_quiz_answer(callback)
        
        # Завершение теста
        elif callback.data == 'end_quiz':
            end_quiz_early(user_id, callback.message.message_id)
        
        # Обработка выбора статьи (ИСПРАВЛЕНО - используем :: вместо _)
        elif callback.data.startswith('article::'):
            parts = callback.data.split('::')
            if len(parts) >= 3:
                language = parts[1]
                article_key = parts[2]
                show_article_menu(user_id, language, article_key, callback.message.message_id)
            else:
                bot.send_message(user_id, "❌ Ошибка при загрузке статьи.")
        
        # Обработка отметки прочтения (ИСПРАВЛЕНО - используем :: вместо _)
        elif callback.data.startswith('mark_read::'):
            parts = callback.data.split('::')
            if len(parts) >= 3:
                language = parts[1]
                article_key = parts[2]
                
                success = mark_article_as_read(user_id, language, article_key)
                
                if success:
                    article = get_article(language, article_key)
                    points = article.get('points', 10) if article else 10
                    
                    bot.answer_callback_query(
                        callback.id, 
                        f"✅ Статья отмечена как прочитанная! +{points} очков"
                    )
                    
                    # Обновляем сообщение
                    show_article_menu(user_id, language, article_key, callback.message.message_id)
                else:
                    bot.answer_callback_query(
                        callback.id, 
                        "❌ Статья уже была прочитана ранее"
                    )
            else:
                bot.answer_callback_query(callback.id, "❌ Ошибка при отметке статьи")
        
        # Обработка лидерборда
        elif callback.data == 'leaderboard':
            show_leaderboard(user_id, message_id=callback.message.message_id)
    
    except Exception as e:
        print(f"Ошибка в обработчике callback: {e}")
        bot.send_message(user_id, "❌ Произошла ошибка. Попробуйте еще раз.")

def show_languages_menu(chat_id, message_id):
    """Показать меню выбора языков"""
    if message_id:
        bot.delete_message(chat_id, message_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('VBA', callback_data='VBA'))
    markup.add(types.InlineKeyboardButton('C', callback_data='C'))
    markup.add(types.InlineKeyboardButton('Bash', callback_data='Bash'))
    markup.add(types.InlineKeyboardButton('Python', callback_data='Python'))
    markup.add(types.InlineKeyboardButton('JavaScript', callback_data='JavaScript'))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_main'))
    
    bot.send_message(chat_id, 
                    '📚 <b>Выберите язык программирования:</b>\n\n'
                    'Изучайте материалы и проходите тесты по выбранному языку.', 
                    reply_markup=markup, parse_mode='HTML')
    
    user_states[str(chat_id)] = 'languages_menu'
    save_data(user_states, USER_STATES_FILE)

def show_language_specific_menu(chat_id, language, message_id):
    """Показать меню для конкретного языка"""
    bot.delete_message(chat_id, message_id)
    
    articles = load_articles().get(language, {})
    user_progress = get_user_articles_progress(chat_id, language)
    
    markup = types.InlineKeyboardMarkup()
    
    # Добавляем кнопки для статей с индикацией прогресса (ИСПРАВЛЕНО - используем :: вместо _)
    for article_key, article_data in articles.items():
        is_read = article_key in user_progress
        emoji = "✅" if is_read else "📖"
        button_text = f"{emoji} {article_data['title']}"
        markup.add(types.InlineKeyboardButton(
            button_text, 
            callback_data=f'article::{language}::{article_key}'
        ))
    
    # Добавляем кнопку для теста
    language_data = {
        'VBA': 'VBA_basic',
        'C': 'C_basic', 
        'Bash': 'Bash_basic',
        'Python': 'Python_basic',
        'JavaScript': 'JavaScript_basic'
    }
    
    quiz_id = language_data.get(language)
    if quiz_id:
        markup.add(types.InlineKeyboardButton('🧠 Пройти тест', callback_data=f'quiz_{quiz_id}'))
    
    # Показываем прогресс по языку
    progress_text = ""
    if articles:
        progress_percentage = (len(user_progress) / len(articles)) * 100
        progress_text = f"\n📊 Прогресс: {len(user_progress)}/{len(articles)} ({progress_percentage:.1f}%)"
    else:
        progress_text = "\n📊 Статьи для этого языка пока не добавлены"
    
    markup.add(types.InlineKeyboardButton('📚 Другие языки', callback_data='back_to_languages'))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_main'))
    
    bot.send_message(chat_id, 
                    f'📚 <b>{html.escape(language)}</b>{progress_text}\n\n'
                    f'Выберите статью для изучения:', 
                    reply_markup=markup, parse_mode='HTML')
    
    user_states[str(chat_id)] = f'{language.lower()}_menu'
    save_data(user_states, USER_STATES_FILE)

def show_article_menu(chat_id, language, article_key, message_id):
    """Показать меню статьи"""
    bot.delete_message(chat_id, message_id)
    
    article = get_article(language, article_key)
    if not article:
        bot.send_message(chat_id, "❌ Статья не найдена.")
        return
    
    user_progress = get_user_articles_progress(chat_id, language)
    is_read = article_key in user_progress
    
    # Формируем сообщение со статьей
    article_text = (
        f"📖 <b>{html.escape(article['title'])}</b>\n\n"
        f"📝 {html.escape(article['description'])}\n\n"
        f"⚡ <b>Сложность:</b> {article['difficulty']}\n"
        f"⏱ <b>Время изучения:</b> {article['estimated_time']}\n"
        f"🏆 <b>Награда:</b> {article['points']} очков\n"
        f"📊 <b>Статус:</b> {'✅ Прочитано' if is_read else '❌ Не прочитано'}\n\n"
        f"Изучите статью и отметьте прочтение:"
    )
    
    markup = types.InlineKeyboardMarkup()
    
    # Кнопка для перехода к статье
    markup.add(types.InlineKeyboardButton(
        '🔗 Перейти к статье', 
        url=article['url']
    ))
    
    # Кнопка для отметки прочтения (только если еще не прочитана) (ИСПРАВЛЕНО - используем :: вместо _)
    if not is_read:
        markup.add(types.InlineKeyboardButton(
            '✅ Отметить как прочитанную', 
            callback_data=f'mark_read::{language}::{article_key}'
        ))
    
    markup.add(types.InlineKeyboardButton(
        '📚 Назад к статьям', 
        callback_data=f'{language}'
    ))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_main'))
    
    bot.send_message(chat_id, article_text, reply_markup=markup, parse_mode='HTML')
    
    user_states[str(chat_id)] = f'article_{language}_{article_key}'
    save_data(user_states, USER_STATES_FILE)

def show_quiz_selection(chat_id, message_id):
    """Показать выбор тестов"""
    bot.delete_message(chat_id, message_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🧠 VBA - Основы', callback_data='quiz_VBA_basic'))
    markup.add(types.InlineKeyboardButton('🧠 C - Основы', callback_data='quiz_C_basic'))
    markup.add(types.InlineKeyboardButton('🧠 Bash - Основы', callback_data='quiz_Bash_basic'))
    markup.add(types.InlineKeyboardButton('🧠 Python - Основы', callback_data='quiz_Python_basic'))
    markup.add(types.InlineKeyboardButton('🧠 JavaScript - Основы', callback_data='quiz_JavaScript_basic'))
    markup.add(types.InlineKeyboardButton('🧠 Тест по всем темам', callback_data='quiz_Big_Test'))
    markup.add(types.InlineKeyboardButton('📚 Изучать материалы', callback_data='languages'))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_main'))
    
    bot.send_message(chat_id, 
                    '🧠 <b>Выберите тест для прохождения:</b>\n\n'
                    'Тесты помогут проверить ваши знания и заработать очки опыта!', 
                    reply_markup=markup, parse_mode='HTML')
    
    user_states[str(chat_id)] = 'quiz_selection_menu'
    save_data(user_states, USER_STATES_FILE)

def show_quiz_info(chat_id, quiz_id, message_id):
    """Показать информацию о тесте"""
    bot.delete_message(chat_id, message_id)
    
    quiz = get_quiz(quiz_id)
    if not quiz:
        bot.send_message(chat_id, "❌ Извините, этот тест временно недоступен.")
        return
    
    # Показываем информацию о тесте
    quiz_info = (
        f"🧠 <b>{html.escape(quiz['title'])}</b>\n\n"
        f"📝 <i>{html.escape(quiz['description'])}</i>\n\n"
        f"⚡ <b>Сложность:</b> {html.escape(quiz['difficulty'])}\n"
        f"⏱ <b>Время:</b> {quiz['time_limit']} секунд\n"
        f"📊 <b>Вопросов:</b> {len(quiz['questions'])}\n"
        f"🏆 <b>Максимальный балл:</b> {quiz['total_points']}\n"
        f"🎯 <b>Проходной балл:</b> {quiz['passing_score']}\n\n"
        f"Готовы проверить свои знания?"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🚀 Начать тест', callback_data=f'start_quiz_{quiz_id}'))
    markup.add(types.InlineKeyboardButton('📋 Выбрать другой тест', callback_data='take_quiz'))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_main'))
    
    bot.send_message(chat_id, quiz_info, reply_markup=markup, parse_mode='HTML')
    user_states[str(chat_id)] = f'quiz_info_{quiz_id}'
    save_data(user_states, USER_STATES_FILE)

def start_quiz(chat_id, quiz_id, message_id):
    """Начать тест"""
    bot.delete_message(chat_id, message_id)
    
    quiz = get_quiz(quiz_id)
    if not quiz:
        bot.send_message(chat_id, "❌ Извините, этот тест временно недоступен.")
        return
    
    # Инициализируем состояние теста
    active_quizzes[chat_id] = {
        'quiz_id': quiz_id,
        'current_question': 0,
        'score': 0,
        'start_time': datetime.now(),
        'user_answers': [],
        'quiz_data': quiz
    }
    
    # Отправляем первый вопрос
    send_quiz_question(chat_id, 0)

def send_quiz_question(chat_id, question_index):
    """Отправить вопрос теста"""
    if chat_id not in active_quizzes:
        return
        
    quiz_data = active_quizzes[chat_id]
    quiz = quiz_data['quiz_data']
    
    if question_index >= len(quiz['questions']):
        finish_quiz(chat_id)
        return
    
    question = quiz['questions'][question_index]
    
    # Создаем клавиатуру с вариантами ответов
    markup = types.InlineKeyboardMarkup()
    
    for i, option in enumerate(question['options']):
        markup.add(types.InlineKeyboardButton(option, callback_data=f'answer_{question_index}_{i}'))
    
    # Кнопка для досрочного завершения
    markup.add(types.InlineKeyboardButton('⏹ Завершить тест', callback_data='end_quiz'))
    
    question_text = (
        f"❓ <b>Вопрос {question_index + 1} из {len(quiz['questions'])}</b>\n\n"
        f"{html.escape(question['question_text'])}"
    )
    
    bot.send_message(chat_id, question_text, reply_markup=markup, parse_mode='HTML')
    
    # Обновляем текущий вопрос
    active_quizzes[chat_id]['current_question'] = question_index

def handle_quiz_answer(callback):
    """Обработка ответа на вопрос теста"""
    user_id = callback.message.chat.id
    user_id_str = str(user_id)
    
    if user_id not in active_quizzes:
        bot.answer_callback_query(callback.id, "Тест не активен. Начните заново.")
        return
    
    # Парсим данные callback
    parts = callback.data.split('_')
    question_index = int(parts[1])
    answer_index = int(parts[2])
    
    quiz_data = active_quizzes[user_id]
    quiz = quiz_data['quiz_data']
    question = quiz['questions'][question_index]
    
    # Сохраняем ответ пользователя
    quiz_data['user_answers'].append({
        'question_index': question_index,
        'answer_index': answer_index,
        'is_correct': answer_index == question['correct_answer']
    })
    
    # Проверяем правильность ответа и начисляем баллы
    if answer_index == question['correct_answer']:
        quiz_data['score'] += question['points']
        bot.answer_callback_query(callback.id, f"✅ Правильно! +{question['points']} баллов")
    else:
        correct_answer = question['options'][question['correct_answer']]
        bot.answer_callback_query(callback.id, f"❌ Неправильно. Правильный ответ: {correct_answer}")
    
    # Удаляем сообщение с вопросом
    bot.delete_message(user_id, callback.message.message_id)
    
    # Переходим к следующему вопросу
    next_question_index = question_index + 1
    if next_question_index < len(quiz['questions']):
        send_quiz_question(user_id, next_question_index)
    else:
        finish_quiz(user_id)

def finish_quiz(chat_id):
    """Завершить тест и показать результаты"""
    quiz_data = active_quizzes.pop(chat_id, None)
    if not quiz_data:
        return
    
    quiz = quiz_data['quiz_data']
    score = quiz_data['score']
    max_score = quiz['total_points']
    percentage = (score / max_score) * 100
    
    # Обновляем статистику пользователя
    update_user_after_quiz(chat_id, quiz['quiz_id'], score, max_score)
    
    # Формируем сообщение с результатами
    result_text = (
        f"🎉 <b>Тест завершен!</b>\n\n"
        f"🧠 <b>{html.escape(quiz['title'])}</b>\n"
        f"🏆 <b>Ваш результат:</b> {score}/{max_score} баллов ({percentage:.1f}%)\n\n"
    )
    
    if percentage >= 80:
        result_text += "🔥 <b>Отличный результат!</b> Вы хорошо знаете материал!\n"
    elif percentage >= 60:
        result_text += "👍 <b>Хороший результат!</b> Есть что повторить.\n"
    else:
        result_text += "📚 <b>Нужно подтянуть знания.</b> Рекомендуем изучить материалы еще раз.\n"
    
    # Показываем неправильные ответы с объяснениями
    wrong_answers = [ans for ans in quiz_data['user_answers'] if not ans['is_correct']]
    if wrong_answers:
        result_text += "\n📝 <b>Разбор ошибок:</b>\n"
        for wrong in wrong_answers[:3]:  # Показываем только первые 3 ошибки
            question = quiz['questions'][wrong['question_index']]
            result_text += f"\n• {html.escape(question['question_text'][:50])}...\n"
            result_text += f"  <b>Правильно:</b> {html.escape(question['options'][question['correct_answer']])}\n"
            result_text += f"  <b>Объяснение:</b> {html.escape(question['explanation'])}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📊 Мой прогресс', callback_data='progress'))
    markup.add(types.InlineKeyboardButton('🧠 Пройти еще тест', callback_data='take_quiz'))
    markup.add(types.InlineKeyboardButton('📚 Изучать материалы', callback_data='languages'))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_main'))
    
    bot.send_message(chat_id, result_text, reply_markup=markup, parse_mode='HTML')

def end_quiz_early(chat_id, message_id):
    """Досрочное завершение теста"""
    bot.delete_message(chat_id, message_id)
    
    if chat_id in active_quizzes:
        active_quizzes.pop(chat_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🧠 Пройти тест', callback_data='take_quiz'))
    markup.add(types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_main'))
    
    bot.send_message(chat_id, 
                    "⏹ <b>Тест был прерван. Ваши результаты не сохранены.</b>\n\n"
                    "Вы всегда можете начать заново!",
                    reply_markup=markup, parse_mode='HTML')

# Обработчик для предложений
@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == 'predlozka_menu')
def predlozka(message):
    text_predloz = message.text
    user_info = f"Пользователь: @{message.from_user.username or 'нет'} ({message.from_user.first_name or 'нет'})"
    
    # Добавляем предложение в очередь модерации
    success = add_suggestion_to_moderation(
        message.chat.id,
        message.from_user.username,
        message.from_user.first_name,
        text_predloz
    )
    
    if success:
        # Безопасный вывод для консоли Windows
        try:
            print(f"IDEA: Получено предложение от {user_info}: {text_predloz}")
        except UnicodeEncodeError:
            # Если все равно возникает ошибка кодировки, используем безопасный вывод
            safe_user_info = user_info.encode('utf-8', errors='replace').decode('utf-8')
            safe_text = text_predloz.encode('utf-8', errors='replace').decode('utf-8')
            print(f"IDEA: Получено предложение от {safe_user_info}: {safe_text}")
    else:
        try:
            print(f"ERROR: Ошибка при добавлении предложения в очередь от {user_info}")
        except UnicodeEncodeError:
            safe_user_info = user_info.encode('utf-8', errors='replace').decode('utf-8')
            print(f"ERROR: Ошибка при добавлении предложения в очередь от {safe_user_info}")
    
    # Сбрасываем состояние и показываем меню
    user_states[str(message.chat.id)] = 'main_menu'
    save_data(user_states, USER_STATES_FILE)
    
    # Показываем подтверждение и главное меню
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📚 Языки программирования', callback_data='languages'))
    markup.add(types.InlineKeyboardButton('🧠 Пройти тест', callback_data='take_quiz'))
    markup.add(types.InlineKeyboardButton('📊 Мой прогресс', callback_data='progress'))
    markup.add(types.InlineKeyboardButton('🏆 Лидерборд', callback_data='leaderboard'))
    
    bot.send_message(message.chat.id, 
                    '✅ <b>Спасибо за ваше предложение!</b>\n\n'
                    'Мы обязательно его рассмотрим и учтем в развитии бота!',
                    reply_markup=markup, parse_mode='HTML')

# Сохранение данных при выходе
import atexit
atexit.register(lambda: save_data(user_states, USER_STATES_FILE))

if __name__ == '__main__':
    try:
        print("Бот CodeForge запущен...")
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        # Добавляем паузу перед завершением, чтобы увидеть ошибку
        import time
        time.sleep(10)