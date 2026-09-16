import requests
from bs4 import BeautifulSoup
import psycopg2
from contextlib import closing
import zlib

# Параметры подключения к базе данных
db_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': '5432'
}

# Функция для генерации уникального целочисленного идентификатора
def generate_unique_int_id(url):
    """Возвращает уникальный целочисленный идентификатор на основе URL."""
    crc_value = zlib.crc32(url.encode())
    # Ограничиваем размер до безопасного диапазона
    return abs(int(crc_value)) % (2**31)

# Функция для парсинга данных
def parse_courses():
    url = "https://loftschool.com/modules"
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Ошибка при загрузке страницы: статус-код {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')
    parsed_data = []

    # Сбор данных с сайта
    counter = 1
    while True:
        title_selector = f'#root-layout-component > div.x-wrapper.x-static-footer > main > section > div > div.modules__list > div:nth-child({counter}) > div.module-card__header > div.module-card__info > div.module-card__title'
        description_selector = f'#root-layout-component > div.x-wrapper.x-static-footer > main > section > div > div.modules__list > div:nth-child({counter}) > div.module-card__main > article'
        link_selector = f'#root-layout-component > div.x-wrapper.x-static-footer > main > section > div > div.modules__list > div:nth-child({counter}) > div.module-card__main > div.module-card__payment > a'

        title_element = soup.select_one(title_selector)
        description_element = soup.select_one(description_selector)
        link_element = soup.select_one(link_selector)

        if title_element is None or link_element is None:
            break

        title = title_element.text.strip()
        description = description_element.text.strip()
        href = link_element['href']
        full_link = f'https://loftschool.com{href}'

        # Генерируем уникальный идентификатор на основе URL
        course_id = generate_unique_int_id(full_link)

        # Формируем кортеж данных
        parsed_data.append((title, course_id, full_link, description))
        counter += 1

    return parsed_data

# Основная логика программы
if __name__ == "__main__":
    # Парсим данные
    data_to_insert = parse_courses()

    # Добавляем значение "площадка" для всех записей
    updated_data = [(item[0], item[1], item[2], item[3], 'LoftSchool') for item in data_to_insert]

    # Подключение к базе данных и сохранение данных
    with closing(psycopg2.connect(**db_params)) as conn:
        with conn.cursor() as cursor:
            # Заполнение таблиц данными
            insert_query = """
            INSERT INTO курсы (название, id_курса, ссылка, краткое_описание, площадка)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id_курса) DO UPDATE SET
              название = EXCLUDED.название,
              ссылка = EXCLUDED.ссылка,
              краткое_описание = EXCLUDED.краткое_описание,
              площадка = EXCLUDED.площадка;
            """
            cursor.executemany(insert_query, updated_data)
            conn.commit()

    print("Парсинг и запись данных завершены успешно!")