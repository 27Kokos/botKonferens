import html
from datetime import datetime
from core.data_manager import load_json, save_json, log
from config import USERS_FILE, USER_STATES_FILE


def init_user(user_id, username, first_name):
    """Создание нового пользователя при /start"""
    users = load_json(USERS_FILE)
    uid = str(user_id)

    if uid not in users:
        users[uid] = {
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
        save_json(users, USERS_FILE)
        log(f"👤 Создан новый пользователь: {username or first_name or 'без имени'}")

    return users[uid]


def get_user(user_id):
    """Получить данные пользователя"""
    users = load_json(USERS_FILE)
    return users.get(str(user_id))


def save_user(user_id, data):
    """Обновить данные пользователя"""
    users = load_json(USERS_FILE)
    uid = str(user_id)

    if uid in users:
        users[uid].update(data)
        save_json(users, USERS_FILE)
        return True
    return False


def update_user_after_quiz(user_id, quiz_id, score, max_score):
    """Обновление данных после теста"""
    users = load_json(USERS_FILE)
    uid = str(user_id)

    if uid not in users:
        return False

    user = users[uid]
    user['progress']['quizzes_completed'][quiz_id] = {
        'score': score,
        'max_score': max_score,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    user['total_points'] += score
    user['stats']['quizzes_taken'] += 1

    total_quizzes = user['stats']['quizzes_taken']
    total_score = sum(q['score'] for q in user['progress']['quizzes_completed'].values())
    total_max = sum(q['max_score'] for q in user['progress']['quizzes_completed'].values())

    user['stats']['average_score'] = round((total_score / total_max) * 100, 2) if total_max > 0 else 0

    if score == max_score and 'perfect_score' not in user['progress']['achievements']:
        user['progress']['achievements'].append('perfect_score')
    if total_quizzes == 1 and 'first_quiz' not in user['progress']['achievements']:
        user['progress']['achievements'].append('first_quiz')

    save_json(users, USERS_FILE)
    return True


def reset_user_progress(user_id, reset_type="full"):
    """Сбросить прогресс конкретного пользователя"""
    users = load_json(USERS_FILE)
    uid = str(user_id)
    if uid not in users:
        return False

    user = users[uid]

    if reset_type in ("full", "quizzes"):
        user['progress']['quizzes_completed'] = {}
        user['stats']['quizzes_taken'] = 0
        user['stats']['average_score'] = 0

    if reset_type in ("full", "articles"):
        user['progress']['articles_viewed'] = {}
        user['stats']['articles_read'] = 0
        user['stats']['languages_learned'] = []

    if reset_type in ("full", "points"):
        user['total_points'] = 0

    if reset_type in ("full", "achievements"):
        user['progress']['achievements'] = []

    save_json(users, USERS_FILE)
    return True


def reset_all_users_progress():
    """Полный сброс статистики всех пользователей"""
    users = load_json(USERS_FILE)
    for uid, u in users.items():
        u['total_points'] = 0
        u['progress']['articles_viewed'] = {}
        u['progress']['quizzes_completed'] = {}
        u['progress']['achievements'] = []
        u['stats'] = {
            "quizzes_taken": 0,
            "articles_read": 0,
            "average_score": 0,
            "total_reading_time": 0,
            "languages_learned": []
        }
    return save_json(users, USERS_FILE)


def delete_all_users():
    """Удалить всех пользователей"""
    save_json({}, USERS_FILE)
    save_json({}, USER_STATES_FILE)
    return True


def get_all_users():
    """Получить всех пользователей"""
    return load_json(USERS_FILE)

