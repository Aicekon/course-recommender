import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()


def reset_user_progress(username):
    """Полностью сбрасывает прогресс пользователя"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '1111'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )

    try:
        with conn.cursor() as cursor:
            # 1. Получаем ID пользователя
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_id = cursor.fetchone()

            if not user_id:
                print(f"Пользователь {username} не найден!")
                return

            user_id = user_id[0]

            # 2. Удаляем историю ответов
            cursor.execute("""
                DELETE FROM user_question_history 
                WHERE user_id = %s
            """, (user_id,))

            # 3. Сбрасываем рейтинги вопросов
            cursor.execute("""
                DELETE FROM question_ratings 
                WHERE user_id = %s
            """, (user_id,))

            # 4. Удаляем активные сессии
            cursor.execute("""
                DELETE FROM user_test_sessions 
                WHERE user_id = %s
            """, (user_id,))

            conn.commit()
            print(f"Прогресс пользователя {username} (ID: {user_id}) полностью сброшен!")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при сбросе прогресса: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    username = input("Введите логин пользователя для сброса прогресса: ").strip()
    confirm = input(f"Вы уверены, что хотите сбросить ВЕСЬ прогресс пользователя {username}? (y/n): ")

    if confirm.lower() == 'y':
        reset_user_progress(username)
    else:
        print("Отменено")