import requests
from urllib.parse import urlencode
import psycopg2
from tabulate import tabulate  # pip install tabulate (если не установлено)
import time  # Для задержки между запросами

# Данные для авторизации на Stepik
CLIENT_ID = 'zJCLRFktDem0PSKmIF1J0aIYgK1QNpXVq92YS6yL'
CLIENT_SECRET = 'JYgere9xihnKkuLEPFmIBMWrBQJR6yBsGHBUQ5NZ3MApGXEYBVAe9kY8tURBm0qkqc2s6V7IEtsNMbavNcd7WrPmxaJler2yvHKtau6xVO1J0zjFNwpC59wQcfADJhwc'
AUTH_URL = 'https://stepik.org/oauth2/token/'
COURSES_URL = 'https://stepik.org/api/courses?'

# Параметры подключения к PostgreSQL
db_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': '5432'
}

# Список тегов
keywords = [
    'Python', 'JavaScript', 'Java', 'C#', 'C++', 'Операционные системы',
    'Тестирование', 'Системное администрирование', 'DevOps',
    'Data Science', 'Базы данных', 'Web-разработка', 'Информационная безопасность', 'Мобильная разработка', 'Искусственный интеллект','Веб-дизайн','Робототехника','Figma','Blockchain'
]


# Функция для получения токена доступа
def get_access_token(client_id, client_secret):
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    response = requests.post(AUTH_URL, data=payload)
    return response.json().get('access_token')


# Функция для получения бесплатных курсов по ключевому слову
def fetch_free_courses_by_keyword(keyword, access_token, page=1):
    params = {
        'search': keyword,
        'price': 0,  # Бесплатные курсы
        'language': 'ru',  # Фильтруем только курсы на русском языке
        'page': page  # Параметр страницы
    }
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    full_url = COURSES_URL + urlencode(params)
    response = requests.get(full_url, headers=headers)
    return response.json()


# Получаем токен доступа
access_token = get_access_token(CLIENT_ID, CLIENT_SECRET)

# Получаем курсы по каждому тегу
all_courses = []
for keyword in keywords:
    page = 1
    while True:
        result = fetch_free_courses_by_keyword(keyword, access_token, page)
        courses_data = result.get('courses', [])
        meta = result.get('meta', {})
        pages = meta.get('pages', 1)

        for course in courses_data:
            all_courses.append({
                'название': course['title'],
                'id_курса': course['id'],
                'ссылка': f"https://stepik.org/course/{course['id']}",
                'краткое_описание': course.get('summary', ''),
                'полное_описание': course.get('description', ''),
                'уровень_сложности': course.get('difficulty', ''),
                'тег': keyword,
                'площадка': 'Stepik'  # Добавляем поле "площадка"
            })

        if page >= pages:
            break
        page += 1

    # Добавляем задержку между запросами (2 секунды)
    time.sleep(2)

# Подключаемся к базе данных
conn = psycopg2.connect(**db_params)
cursor = conn.cursor()

# Создаем таблицу, если её нет (с уникальным ограничением на поле "id_курса")
create_table_query = """
CREATE TABLE IF NOT EXISTS курсы (
    id SERIAL PRIMARY KEY,
    название TEXT NOT NULL,
    id_курса INTEGER UNIQUE NOT NULL,  -- уникальное ограничение на id_курса
    ссылка TEXT NOT NULL,
    краткое_описание TEXT,
    полное_описание TEXT,
    уровень_сложности TEXT,
    тег TEXT,
    площадка TEXT  -- Новое поле "площадка"
);
"""
cursor.execute(create_table_query)
conn.commit()

# Вставляем данные в таблицу
insert_query = """
INSERT INTO курсы (название, id_курса, ссылка, краткое_описание, полное_описание, уровень_сложности, тег, площадка) 
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id_курса) DO UPDATE SET название = EXCLUDED.название, краткое_описание = EXCLUDED.краткое_описание, полное_описание = EXCLUDED.полное_описание, уровень_сложности = EXCLUDED.уровень_сложности, тег = EXCLUDED.тег, площадка = EXCLUDED.площадка;
"""

for course in all_courses:
    cursor.execute(insert_query, tuple(course.values()))

conn.commit()

# Читаем таблицу и выводим её в консоль
select_query = "SELECT * FROM курсы;"
cursor.execute(select_query)
rows = cursor.fetchall()

# Выводим таблицу в красивом виде
columns = ['id', 'название', 'id_курса', 'ссылка', 'краткое_описание', 'полное_описание', 'уровень_сложности', 'тег',
           'площадка']
print(tabulate(rows, headers=columns, tablefmt="grid"))

# Закрываем соединение
cursor.close()
conn.close()