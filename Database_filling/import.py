import pandas as pd
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

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


def import_questions_from_excel(file_path):
    # Чтение Excel-файла
    df = pd.read_excel(file_path)

    # Подключение к БД
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Создание таблиц
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            question_text TEXT NOT NULL,
            tag TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id SERIAL PRIMARY KEY,
            question_id INTEGER REFERENCES questions(id),
            answer_text TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            option_code CHAR(1) NOT NULL
        )
    """)

    # Очистка таблиц перед импортом
    cursor.execute("TRUNCATE TABLE answers, questions RESTART IDENTITY")

    # Подготовка и выполнение запросов на вставку
    inserted_count = 0
    for _, row in df.iterrows():
        try:
            # Вставляем вопрос
            cursor.execute(
                "INSERT INTO questions (question_text, tag) VALUES (%s, %s) RETURNING id",
                (row['question'], row['tag'])
            )
            question_id = cursor.fetchone()[0]

            # Вставляем варианты ответов
            options = [
                ('a', row['a'], row['correct_answer'].lower()),
                ('b', row['b'], row['correct_answer'].lower()),
                ('c', row['c'], row['correct_answer'].lower()),
                ('d', row['d'], row['correct_answer'].lower())
            ]

            for option_code, answer_text, correct_answer in options:
                is_correct = option_code in correct_answer.split('/')
                cursor.execute(
                    "INSERT INTO answers (question_id, answer_text, is_correct, option_code) VALUES (%s, %s, %s, %s)",
                    (question_id, answer_text, is_correct, option_code)
                )

            inserted_count += 1
        except Exception as e:
            print(f"Ошибка при вставке вопроса: {row['question']}")
            print(f"Ошибка: {e}")

    # Фиксация изменений и закрытие соединения
    conn.commit()
    cursor.close()
    conn.close()

    print(f"Успешно импортировано {inserted_count} вопросов из {len(df)}")

if __name__ == "__main__":
    # Укажите путь к вашему файлу Excel
    excel_file = "Новая таблица (7).xlsx"

    if os.path.exists(excel_file):
        import_questions_from_excel(excel_file)
    else:
        print(f"Файл {excel_file} не найден в текущей директории")