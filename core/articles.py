
from core.data_manager import load_json, save_json, log
from core.leaderboard import update_leaderboard
from config import ARTICLES_FILE, USERS_FILE
from datetime import datetime


def load_articles():
    """Загрузить структуру статей"""
    return load_json(ARTICLES_FILE, {})


def get_article(language, article_key):
    """Получить конкретную статью"""
    articles = load_articles()
    return articles.get(language, {}).get(article_key)


def get_user_articles_progress(user_id, language):
    """Вернуть список просмотренных статей пользователя для языка"""
    users = load_json(USERS_FILE, {})
    uid = str(user_id)
    if uid not in users:
        return []
    user = users[uid]
    return user['progress'].get('articles_viewed', {}).get(language, [])


def mark_article_as_read(user_id, language, article_key):
    """
    Отметить статью как прочитанную:
    - добавить статью в progress.articles_viewed[language]
    - начислить очки (article.points)
    - обновить stats (articles_read, languages_learned)
    - сохранить users.json и обновить лидерборд
    """
    users = load_json(USERS_FILE, {})
    uid = str(user_id)

    if uid not in users:
        log(f"⚠️ Попытка отметить статью за несуществующего пользователя {uid}")
        return False

    user = users[uid]

    # Инициализация структуры если нет
    if 'progress' not in user:
        user['progress'] = {"articles_viewed": {}, "quizzes_completed": {}, "achievements": []}
    if 'articles_viewed' not in user['progress']:
        user['progress']['articles_viewed'] = {}

    if language not in user['progress']['articles_viewed']:
        user['progress']['articles_viewed'][language] = []

    # Проверяем, не прочитана ли уже статья
    if article_key in user['progress']['articles_viewed'][language]:
        return False

    # Добавляем статью в прочитанные
    user['progress']['articles_viewed'][language].append(article_key)

    # Начисление очков
    article = get_article(language, article_key)
    points = article.get('points', 10) if article else 10
    if 'total_points' not in user:
        user['total_points'] = 0
    user['total_points'] += points

    # Обновление статистики
    user['stats'] = user.get('stats', {
        "quizzes_taken": 0,
        "articles_read": 0,
        "average_score": 0,
        "total_reading_time": 0,
        "languages_learned": []
    })

    # Обновляем articles_read (сумма по всем языкам)
    user['stats']['articles_read'] = sum(len(v) for v in user['progress']['articles_viewed'].values())

    # Обновляем languages_learned
    user['stats']['languages_learned'] = list(user['progress']['articles_viewed'].keys())

    # Сохраняем пользователей
    users[uid] = user
    saved = save_json(users, USERS_FILE)
    if not saved:
        log("❌ Не удалось сохранить users.json при отметке статьи")
        return False

    # Обновляем лидерборд
    try:
        update_leaderboard()
    except Exception as e:
        log(f"⚠️ Ошибка при обновлении лидерборда: {e}")

    log(f"✅ Пользователь {uid} прочитал статью {language}/{article_key} (+{points} очков)")
    return True
