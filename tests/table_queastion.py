import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
from tabulate import tabulate

# Загрузка переменных окружения
load_dotenv()

# Параметры подключения к базе данных
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '1111'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}


def display_questions(limit=None):
    """Отображает вопросы из таблицы questions"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Формируем запрос с учетом лимита
        query = "SELECT id, question_text, option_a, option_b, option_c, option_d, correct_answer, tags FROM questions"
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        questions = cursor.fetchall()

        if not questions:
            print("Таблица questions пуста")
            return

        # Подготавливаем данные для красивого вывода
        headers = ["ID", "Вопрос", "A", "B", "C", "D", "Правильный ответ", "Теги"]
        rows = []

        for q in questions:
            # Обрезаем длинные вопросы для удобства просмотра
            short_question = q[1] if len(q[1]) < 50 else q[1][:47] + "..."
            rows.append([q[0], short_question, q[2], q[3], q[4], q[5], q[6], q[7]])

        # Выводим таблицу
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"\nВсего вопросов: {len(questions)}")

    except psycopg2.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("Содержимое таблицы questions:\n")

    # Можно указать лимит выводимых записей (None - без лимита)
    display_questions()  # Показать первые 10 вопросов

    input("\nНажмите Enter для выхода...")