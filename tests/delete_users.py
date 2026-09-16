import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()


def get_db_connection():
    """Устанавливает соединение с PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '1111'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except OperationalError as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        return None


def delete_user(username):
    """Удаляет пользователя и все связанные данные"""
    conn = get_db_connection()
    if not conn:
        print("Не удалось подключиться к БД")
        return False

    try:
        with conn.cursor() as cursor:
            # Получаем ID пользователя
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()

            if not user_data:
                print(f"Пользователь {username} не найден")
                return False

            user_id = user_data[0]

            # Удаляем связанные данные
            print(f"Удаление данных пользователя {username} (ID: {user_id})...")

            # Удаляем историю вопросов
            cursor.execute("DELETE FROM user_question_history WHERE user_id = %s", (user_id,))
            print(f"Удалено записей истории: {cursor.rowcount}")

            # Удаляем рейтинги вопросов
            cursor.execute("DELETE FROM question_ratings WHERE user_id = %s", (user_id,))
            print(f"Удалено рейтингов: {cursor.rowcount}")

            # Удаляем самого пользователя
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

            conn.commit()
            print(f"Пользователь {username} успешно удален")
            return True

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при удалении пользователя: {e}")
        return False
    finally:
        if conn:
            conn.close()


def delete_users():
    """Основная функция для удаления пользователей"""
    users_to_delete = ['user', 'admin']

    for username in users_to_delete:
        print(f"\nПопытка удаления пользователя: {username}")
        success = delete_user(username)

        if not success:
            print(f"Не удалось удалить пользователя {username}")


if __name__ == '__main__':
    print("Скрипт удаления пользователей user и admin")
    print("----------------------------------------")
    delete_users()
    print("\nОперация завершена")