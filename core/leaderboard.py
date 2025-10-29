from core.data_manager import load_json, save_json, log
from config import USERS_FILE, LEADERBOARD_FILE, TOP_LIMIT
from datetime import datetime


def get_leaderboard_display_name(user_data):
    """Возвращаем отображаемое имя для пользователя в лидерборде"""
    if not user_data:
        return "Unknown"
    if user_data.get('username') and user_data.get('username') != "без username":
        return f"@{user_data['username']}"
    return user_data.get('first_name', 'Пользователь')


def update_leaderboard():
    """
    Формируем и сохраняем лидерборд на основе users.json
    Возвращает структуру лидерборда.
    """
    users = load_json(USERS_FILE, {})
    leaderboard = load_json(LEADERBOARD_FILE, {})

    ranking = []
    for uid, user_data in users.items():
        ranking.append({
            "user_id": int(uid) if uid.isdigit() else uid,
            "username": user_data.get('username', ''),
            "first_name": user_data.get('first_name', ''),
            "total_points": user_data.get('total_points', 0),
            "quizzes_taken": user_data.get('stats', {}).get('quizzes_taken', 0),
            "articles_read": user_data.get('stats', {}).get('articles_read', 0)
        })

    # Сортируем по очкам (убывание)
    ranking.sort(key=lambda x: x['total_points'], reverse=True)

    # Добавляем ранги
    for i, u in enumerate(ranking):
        u['rank'] = i + 1

    leaderboard['ranking'] = ranking
    leaderboard['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    saved = save_json(leaderboard, LEADERBOARD_FILE)
    if not saved:
        log("❌ Не удалось сохранить leaderboard.json")
    else:
        log("✅ Лидерборд обновлён")

    return leaderboard


def get_leaderboard_top(limit: int = TOP_LIMIT):
    """Вернуть топ N пользователей для отображения"""
    leaderboard = load_json(LEADERBOARD_FILE, {})
    ranking = leaderboard.get('ranking', [])
    return ranking[:limit]

