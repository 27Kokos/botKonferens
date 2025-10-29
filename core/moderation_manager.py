from datetime import datetime
from core.data_manager import load_json, save_json, timestamp, log
from config import MODERATION_DB_FILE


def load_moderation_db():
    return load_json(MODERATION_DB_FILE, {"moderation_queue": [], "suggestion_stats": {}})


def save_moderation_db(data):
    return save_json(data, MODERATION_DB_FILE)


def add_suggestion(user_id, username, first_name, text):
    """Добавить предложение в базу"""
    db = load_moderation_db()
    if "moderation_queue" not in db:
        db["moderation_queue"] = []

    suggestion = {
        "id": f"{user_id}_{int(datetime.now().timestamp())}",
        "type": "suggestion",
        "user_id": user_id,
        "user_data": {
            "username": username,
            "first_name": first_name
        },
        "content": text,
        "timestamp": timestamp(),
        "status": "pending",
        "moderator_id": None,
        "response": None
    }
    db["moderation_queue"].append(suggestion)

    if "suggestion_stats" not in db:
        db["suggestion_stats"] = {"total": 0, "approved": 0, "rejected": 0, "pending": 0}

    db["suggestion_stats"]["total"] += 1
    db["suggestion_stats"]["pending"] += 1

    log(f"💡 Добавлено предложение от @{username or 'нет'}: {text[:50]}")
    return save_moderation_db(db)


def get_pending_suggestions():
    """Все ожидающие предложения"""
    db = load_moderation_db()
    return [s for s in db.get("moderation_queue", []) if s["status"] == "pending"]


def get_processed_suggestions(limit=20):
    """Обработанные предложения"""
    db = load_moderation_db()
    all_suggestions = db.get("moderation_queue", [])
    processed = [s for s in all_suggestions if s["status"] in ["approved", "rejected"]]
    return sorted(processed, key=lambda x: x.get("processed_date", x["timestamp"]), reverse=True)[:limit]


def update_suggestion_status(suggestion_id, status, moderator_id, response=None):
    """Обновить статус предложения"""
    db = load_moderation_db()

    for s in db.get("moderation_queue", []):
        if s["id"] == suggestion_id:
            s["status"] = status
            s["moderator_id"] = moderator_id
            s["response"] = response
            s["processed_date"] = timestamp()
            break

    stats = db.get("suggestion_stats", {"total": 0, "approved": 0, "rejected": 0, "pending": 0})
    stats["pending"] = len([s for s in db["moderation_queue"] if s["status"] == "pending"])
    if status == "approved":
        stats["approved"] += 1
    elif status == "rejected":
        stats["rejected"] += 1

    db["suggestion_stats"] = stats
    return save_moderation_db(db)


def is_moderator(user_id):
    """Проверка модератора"""
    db = load_moderation_db()
    return user_id in db.get("moderators", [])


def get_stats():
    """Статистика предложений"""
    db = load_moderation_db()
    return db.get("suggestion_stats", {"total": 0, "approved": 0, "rejected": 0, "pending": 0})
