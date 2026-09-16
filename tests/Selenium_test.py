import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def performance_test():
    print("=== Начало тестирования ===")

    # Инициализация драйвера с увеличенным временем ожидания
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 15)  # Увеличили таймаут до 15 секунд

    try:
        # 1. Логин
        driver.get("http://127.0.0.1:5000/login")

        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        username_field.send_keys("user")
        password_field.send_keys("1234")

        start_time = time.time()
        submit_button.click()
        wait.until(EC.url_contains("select_tags"))  # Ждём страницу выбора тегов
        print(f"Логин: {time.time() - start_time:.2f} сек")

        # 2. Выбор тега Python
        start_time = time.time()
        python_checkbox = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[value='Python']")))
        start_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        python_checkbox.click()
        start_button.click()
        wait.until(EC.url_contains("question"))  # Ждём загрузки вопроса
        print(f"Выбор тега: {time.time() - start_time:.2f} сек")

        # 3. Ответы на 5 вопросов
        for i in range(5):
            start_time = time.time()

            # Ждём появления формы с вопросом
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#answer-form")))

            # Выбираем первый вариант ответа
            first_answer = driver.find_element(By.CSS_SELECTOR, "input[name='answers']")
            submit_button = driver.find_element(By.ID, "submit-btn")

            first_answer.click()
            submit_button.click()

            # Ожидание нового вопроса или результатов
            if i < 4:
                # Ждём обновления вопроса (исчезновение старой кнопки)
                wait.until(EC.staleness_of(submit_button))
                # Ждём появления новой кнопки
                wait.until(EC.presence_of_element_located((By.ID, "submit-btn")))
            else:
                # После 5-го вопроса ждём результатов
                wait.until(EC.url_contains("results"))

            print(f"Вопрос {i + 1}: {time.time() - start_time:.2f} сек")

    except Exception as e:
        print(f"Ошибка: {str(e)}")
        # Сделаем скриншот при ошибке
        driver.save_screenshot(f"error_{int(time.time())}.png")
    finally:
        driver.quit()
        print("=== Тест завершён ===")


performance_test()