from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
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
    return abs(int(crc_value)) % (2**31)

# Функция для парсинга данных одного курса
def parse_course(course_element):
    """Парсинг данных одного курса с обработкой ошибок"""
    try:
        # Название курса
        title = course_element.find_element(By.CSS_SELECTOR, "div.t776__title p").text
    except:
        title = "Название не найдено"

    try:
        # Ссылка на курс
        link = course_element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
    except:
        link = "Ссылка не найдена"

    try:
        # Описание курса
        description = course_element.find_element(By.CSS_SELECTOR, "div.t776__descr p").text
    except:
        description = "Описание отсутствует"

    return {
        "title": title,
        "link": link,
        "description": description
    }

# Настройка драйвера
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

try:
    # Открываем страницу
    driver.get(
        "https://www.lektorium.tv/mooc?filters467051319=%D0%A2%D0%B5%D0%BC%D0%B0__eq__%D0%A0%D0%BE%D0%B1%D0%BE%D1%82%D0%BE%D1%82%D0%B5%D1%85%D0%BD%D0%B8%D0%BA%D0%B0+%D0%B8+%D0%BF%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5__and__%D0%94%D0%BE%D1%81%D1%82%D1%83%D0%BF__eq__%D0%91%D0%B5%D1%81%D0%BF%D0%BB%D0%B0%D1%82%D0%BD%D1%8B%D0%B9")

    # Ждем загрузки страницы
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.t776__col.js-product")))

    all_courses = []
    previous_count = 0

    while True:
        # Находим все элементы курсов
        courses = driver.find_elements(By.CSS_SELECTOR, "div.t776__col.js-product")

        # Парсим только новые курсы
        for i in range(previous_count, len(courses)):
            course_data = parse_course(courses[i])
            if course_data:
                all_courses.append(course_data)
                print(f"\nКурс {len(all_courses)}:")
                print(f"Название: {course_data['title']}")
                print(f"Ссылка: {course_data['link']}")
                print(f"Описание: {course_data['description']}")
                print("-" * 50)

        previous_count = len(courses)

        # Пытаемся найти и нажать кнопку "Показать еще"
        try:
            show_more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.t776__buttonwrapper td"))
            )
            # Двойная прокрутка для надежности
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            driver.execute_script("arguments[0].scrollIntoView();", show_more_button)
            time.sleep(0.5)
            show_more_button.click()
            print("\nНажата кнопка 'Показать еще'...")

            # Ждем появление новых курсов
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.t776__col.js-product")) > previous_count
            )
            time.sleep(2)  # Дополнительное время для полной загрузки
        except:
            print("\nБольше курсов нет")
            break

    print(f"\nВсего спарсено курсов: {len(all_courses)}")

    # Запись данных в базу данных
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
            prepared_data = []
            for course in all_courses:
                course_id = generate_unique_int_id(course['link'])
                prepared_data.append((course['title'], course_id, course['link'], course['description'], 'Лекториум'))

            cursor.executemany(insert_query, prepared_data)
            conn.commit()

except Exception as e:
    print(f"Произошла ошибка: {str(e)}")

finally:
    driver.quit()