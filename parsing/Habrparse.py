import requests
from lxml import html
import psycopg2
import time  # Импортируем модуль time

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

# Создание таблицы, если она не существует
cur.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id SERIAL PRIMARY KEY,
        article_id INTEGER UNIQUE,
        title TEXT,
        link TEXT,
        views TEXT,
        date_published TIMESTAMP,
        source TEXT,
        tag TEXT,
        description TEXT,
        complexity_level TEXT,
        informational_value TEXT
    );
''')
conn.commit()

# Список тегов для парсинга
keywords = [
    'Python', 'JavaScript', 'Java', 'C#', 'C++', 'Операционные системы',
    'Тестирование', 'Системное администрирование', 'DevOps',
    'Data Science', 'Базы данных', 'Web-разработка', 'Информационная безопасность', 'Мобильная разработка',
    'Искусственный интеллект', 'Веб-дизайн', 'Робототехника', 'Figma', 'Blockchain'
]

# Функция для парсинга данных с одной страницы
def parse_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка статуса ответа
        html_content = response.text
        tree = html.fromstring(html_content)

        articles = tree.xpath('//article[@class="tm-articles-list__item"]')
        data = []

        for article in articles:
            # Извлекаем заголовок статьи
            title_element = article.xpath('.//h2/a/span')
            title = ''.join(title_element[0].xpath('.//text()')).strip() if title_element else "Заголовок не найден"
            print(keyword)
            print(title)
            # Извлекаем ссылку на статью
            link_element = article.xpath('.//h2/a')
            link = "https://habr.com" + link_element[0].get('href') if link_element else "Ссылка не найдена"

            # Извлекаем количество просмотров
            views_element = article.xpath('.//span[@class="tm-icon-counter__value"]')
            views = views_element[0].text.strip() if views_element else "Просмотры не найдены"

            # Извлекаем дату публикации
            date_element = article.xpath('.//time')
            date = date_element[0].get('datetime') if date_element else "Дата не найдена"
 # Извлекаем уникальный ID статьи из ссылки
            article_id = link.split('/')[-2] if link != "Ссылка не найдена" else None

            data.append({
                'article_id': article_id,
                'title': title,
                'link': link,
                'views': views,
                'date_published': date
            })

        return data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return []

# Функция для парсинга всех страниц
def parse_all_pages(keyword):
    page = 1
    all_data = []

    while True:
        url = f"https://habr.com/ru/search/page{page}/?q={keyword}&target_type=posts&order=relevance"
        print(f"Парсинг страницы: {url}")  # Логирование URL
        data = parse_page(url)

        if not data:
            break

        all_data.extend(data)
        page += 1
        time.sleep(2)  # Добавляем задержку в 2 секунды между запросами

    return all_data

# Парсинг данных по всем тегам
for keyword in keywords:
    articles = parse_all_pages(keyword)
    for article in articles:
        article['source'] = 'Хабр'
        article['tag'] = keyword

        # Вставка данных в базу данных после каждой страницы
        cur.execute('''
            INSERT INTO articles (article_id, title, link, views, date_published, source, tag)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (article_id) DO NOTHING;
        ''', (article['article_id'], article['title'], article['link'], article['views'], article['date_published'],
              article['source'], article['tag']))
        conn.commit()

# Закрытие соединения с базой данных
cur.close()
conn.close()