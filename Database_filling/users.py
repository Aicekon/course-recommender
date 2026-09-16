import psycopg2
from passlib.hash import sha256_crypt

# Параметры подключения к базе данных
db_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': '5432'
}

# Функция для хеширования паролей
def hash_password(password):
    return sha256_crypt.hash(password)

try:
    # Устанавливаем соединение с базой данных
    connection = psycopg2.connect(**db_params)
    cursor = connection.cursor()

    # Создаем таблицу users
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role VARCHAR(10) CHECK(role IN ('admin', 'user')) DEFAULT 'user' NOT NULL,
        hash_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid()
    )
    '''
    cursor.execute(create_table_query)
    print("Таблица успешно создана.")

    # Данные для вставки (администратор и пользователь)
    data_to_insert = [
        ("admin", hash_password("admin"), "admin"),
        ("user", hash_password("user"), "user")
    ]

    # Вставляем данные в таблицу
    insert_query = """
    INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)
    ON CONFLICT DO NOTHING
    """
    cursor.executemany(insert_query, data_to_insert)
    connection.commit()
    print("Данные успешно вставлены.")

except Exception as e:
    print(f"Ошибка: {e}")
finally:
    if connection is not None:
        cursor.close()
        connection.close()
        print("Подключение закрыто.")