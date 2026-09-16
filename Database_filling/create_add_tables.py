import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()


def create_additional_tables():
    conn = None
    try:
        # Подключаемся к существующей БД
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '1111'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("Создаем дополнительные таблицы...")

        # 1. Таблица истории ответов пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_question_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
                is_correct BOOLEAN NOT NULL,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                attempt_count INTEGER NOT NULL,
                session_id TEXT,
                user_answer TEXT,
                correct_answer TEXT
            )
        """)
        print("Таблица user_question_history создана/проверена")

        # 2. Таблица рейтингов вопросов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_ratings (
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
                rating FLOAT NOT NULL DEFAULT 0.5,
                last_correct TIMESTAMP,
                last_asked TIMESTAMP,
                correct_count INTEGER DEFAULT 0,
                incorrect_count INTEGER DEFAULT 0,
                first_answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, question_id)
            )
        """)
        print("Таблица question_ratings создана/проверена")
        # Добавьте в create_additional_tables()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_test_sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data JSONB NOT NULL,
                expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours')
            )
        """)

        # Создаем индексы для ускорения запросов
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_history_composite 
            ON user_question_history(user_id, question_id, answered_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_question_ratings_composite 
            ON question_ratings(user_id, rating, last_asked)
        """)
        print("Индексы созданы/проверены")

        # Проверяем существующие таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('user_question_history', 'question_ratings')
        """)
        existing_tables = [table[0] for table in cursor.fetchall()]

        print("\nПроверка созданных таблиц:")
        for table in ['user_question_history', 'question_ratings']:
            status = "создана" if table in existing_tables else "не создана"
            print(f"- {table}: {status}")

    except Exception as e:
        print(f"\nОшибка при создании таблиц: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    create_additional_tables()