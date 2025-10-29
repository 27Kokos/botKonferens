
# ==============================
# ⚙️ CONFIGURATION FILE
# ==============================

# --- Telegram tokens ---
MAIN_BOT_TOKEN = "8317740647:AAEsqXPmGOrZSgDbaIMUnJPvnBO_ZYFvfgQ"          # ← замени
MODERATOR_BOT_TOKEN = "8339489199:AAELTq_I7ge6_3p_GQ-IeZhT8liL47v7xaI" # ← замени

# --- File paths ---
DATA_PATH = "data/"

USERS_FILE = DATA_PATH + "users.json"
USER_STATES_FILE = DATA_PATH + "user_states.json"
QUIZZES_FILE = DATA_PATH + "quizzes.json"
LEADERBOARD_FILE = DATA_PATH + "leaderboard.json"
ARTICLES_FILE = DATA_PATH + "articles.json"
MODERATION_DB_FILE = DATA_PATH + "moderation_db.json"

# --- General settings ---
TOP_LIMIT = 15           # Сколько показывать людей в рейтинге
ENCODING = "utf-8"

# --- Debug ---
DEBUG = True  # Если True — выводит отладочные логи в консоль
