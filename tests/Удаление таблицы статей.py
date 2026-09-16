import psycopg2

# Параметры подключения к PostgreSQL
db_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': '5432'
}

# Подключение к базе данных
conn = psycopg2.connect(**db_params)
cur = conn.cursor()

# Удаление таблицы articles
cur.execute('''
    DROP TABLE IF EXISTS articles;
''')
conn.commit()

# Закрытие соединения с базой данных
cur.close()
conn.close()