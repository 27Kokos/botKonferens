from core.data_manager import load_json, save_json, log
from core.user_manager import update_user_after_quiz
from core.leaderboard import update_leaderboard
from config import QUIZZES_FILE


def load_quizzes():
    """Загрузить все квизы"""
    return load_json(QUIZZES_FILE, {})


def get_quiz(quiz_id):
    """Получить один квиз"""
    quizzes = load_quizzes()
    return quizzes.get(quiz_id)


def finalize_quiz_for_user(user_id, quiz_id, score, max_score):
    """
    Обновляет пользователя после прохождения квиза и обновляет лидерборд.
    Это вызывает user_manager.update_user_after_quiz (которая сохраняет users.json)
    """
    success = update_user_after_quiz(user_id, quiz_id, score, max_score)
    if not success:
        log(f"❌ Ошибка обновления пользователя {user_id} после квиза {quiz_id}")
        return False

    try:
        update_leaderboard()
    except Exception as e:
        log(f"⚠️ Ошибка при обновлении лидерборда после квиза: {e}")

    log(f"✅ Квиз {quiz_id} завершён для {user_id}: {score}/{max_score}")
    return True

