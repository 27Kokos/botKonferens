import json

# Создаем тестовые квизы
sample_quizzes = {
    "VBA_basic": {
        "quiz_id": "VBA_basic",
        "language": "VBA",
        "title": "Основы VBA",
        "description": "Тест по базовым концепциям VBA",
        "difficulty": "beginner",
        "time_limit": 600,
        "questions": [
            {
                "question_id": 1,
                "question_text": "Как объявить переменную в VBA?",
                "question_type": "single_choice",
                "options": [
                    "Dim x As Integer",
                    "var x = Integer", 
                    "Integer x",
                    "declare x Integer"
                ],
                "correct_answer": 0,
                "points": 10,
                "explanation": "В VBA переменные объявляются с помощью ключевого слова Dim"
            },
            {
                "question_id": 2,
                "question_text": "Что делает оператор 'Set' в VBA?",
                "question_type": "single_choice",
                "options": [
                    "Присваивает значение переменной",
                    "Присваивает объект переменной",
                    "Устанавливает свойства объекта",
                    "Создает новую переменную"
                ],
                "correct_answer": 1,
                "points": 10,
                "explanation": "Set используется для присвоения объекта переменной"
            }
        ],
        "total_points": 20,
        "passing_score": 12
    },
    "C_basic": {
        "quiz_id": "C_basic",
        "language": "C",
        "title": "Основы C",
        "description": "Тест по базовым концепциям языка C",
        "difficulty": "beginner", 
        "time_limit": 600,
        "questions": [
            {
                "question_id": 1,
                "question_text": "Какой оператор используется для вывода в C?",
                "question_type": "single_choice",
                "options": [
                    "print()",
                    "printf()",
                    "cout <<",
                    "System.out.println()"
                ],
                "correct_answer": 1,
                "points": 10,
                "explanation": "В языке C для вывода используется функция printf()"
            }
        ],
        "total_points": 10,
        "passing_score": 6
    },
    "Bash_basic": {
        "quiz_id": "Bash_basic", 
        "language": "Bash",
        "title": "Основы Bash",
        "description": "Тест по базовым командам Bash",
        "difficulty": "beginner",
        "time_limit": 600,
        "questions": [
            {
                "question_id": 1,
                "question_text": "Какая команда показывает текущую директорию в Bash?",
                "question_type": "single_choice",
                "options": [
                    "pwd",
                    "ls",
                    "cd",
                    "where"
                ],
                "correct_answer": 0,
                "points": 10,
                "explanation": "Команда pwd (print working directory) показывает текущую директорию"
            }
        ],
        "total_points": 10,
        "passing_score": 6
    }
}

# Сохраняем sample данные
with open('quizzes.json', 'w', encoding='utf-8') as f:
    json.dump(sample_quizzes, f, ensure_ascii=False, indent=2)

print("Тестовые данные для квизов созданы!")