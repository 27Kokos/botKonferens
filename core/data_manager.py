
import json
import os
from datetime import datetime
from config import ENCODING, DEBUG
import sys

def log(message: str):
    """Безопасный лог в консоль без сбоев кодировки"""
    try:
        # убираем emoji, которые не поддерживает Windows
        safe_message = message.encode(sys.stdout.encoding, errors="replace").decode(sys.stdout.encoding)
        print(safe_message)
    except Exception:
        print(message.encode("utf-8", errors="replace").decode("utf-8"))



def load_json(path: str, default=None):
    """Загрузка JSON файла"""
    if not os.path.exists(path):
        return default or {}
    try:
        with open(path, 'r', encoding=ENCODING) as f:
            return json.load(f)
    except json.JSONDecodeError:
        log(f"⚠️ Ошибка декодирования JSON: {path}")
        return default or {}
    except Exception as e:
        log(f"❌ Ошибка чтения {path}: {e}")
        return default or {}


def save_json(data, path: str) -> bool:
    """Сохранение JSON файла"""
    try:
        with open(path, 'w', encoding=ENCODING) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log(f"❌ Ошибка записи {path}: {e}")
        return False


def timestamp() -> str:
    """Возвращает текущее время в строке"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
