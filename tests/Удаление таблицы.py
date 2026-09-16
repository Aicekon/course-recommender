import psycopg2

# Параметры подключения к PostgreSQL
db_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': '5432'
}

# Подключаемся к базе данных
conn = psycopg2.connect(**db_params)
cursor = conn.cursor()

# Удаляем таблицу
drop_table_query = """
DROP TABLE IF EXISTS курсы;
"""
cursor.execute(drop_table_query)
conn.commit()

# Закрываем соединение
cursor.close()
conn.close()

print("Таблица успешно удалена.")