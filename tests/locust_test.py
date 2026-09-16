from locust import HttpUser, task, between
import random
from bs4 import BeautifulSoup

class QuizUser(HttpUser):
    host = "http://127.0.0.1:5000"
    wait_time = between(1, 3)

    keywords = [
        'Python', 'JavaScript', 'Java', 'C#', 'C++', 'Операционные системы',
        'Тестирование', 'Системное администрирование', 'DevOps',
        'Data Science', 'Базы данных', 'Web-разработка', 'Информационная безопасность',
        'Мобильная разработка', 'Искусственный интеллект', 'Веб-дизайн', 'Робототехника', 'Figma', 'Blockchain'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None

    def on_start(self):
        # Генерация уникального имени пользователя
        self.user_id = f"test{random.randint(1, 5)}"

        # Логин с сохранением сессии
        response = self.client.get("/login", name="GET /login")
        if response.status_code not in [200, 302]:
            print(f"Failed to load login page with status code: {response.status_code}")
            self.environment.runner.quit()

        response = self.client.post(
            "/login",
            {"username": self.user_id, "password": "1111"},
            name="POST /login",
            allow_redirects=True  # Разрешить редиректы
        )
        if response.status_code not in [200, 302]:
            print(f"Failed to login with status code: {response.status_code}")
            self.environment.runner.quit()

    @task
    def testing_flow(self):
        # Выбор одного случайного тега
        self.selected_tag = random.choice(self.keywords)

        # Запрос страницы выбора тегов
        response = self.client.get("/select_tags", name="GET /select_tags")
        if response.status_code not in [200, 302]:
            print(f"Failed to load select_tags page with status code: {response.status_code}")
            return

        # Отправка выбранного тега
        response = self.client.post(
            "/select_tags",
            {"tags": [self.selected_tag]},
            name="POST /select_tags",
            allow_redirects=True  # Разрешить редиректы
        )
        if response.status_code not in [200, 302]:
            print(f"Failed to select tags with status code: {response.status_code}")
            return

        # Запрос страницы начала теста
        response = self.client.get(
            "/start_test",
            name="GET /start_test"
        )
        if response.status_code not in [200, 302]:
            print(f"Failed to load start_test page with status code: {response.status_code}")
            return

        # Основной цикл прохождения теста
        for _ in range(5):  # Предполагаем, что у нас 5 вопросов
            # Запрос вопроса
            response = self.client.get("/question", name="GET /question")
            if response.status_code not in [200, 302]:
                print(f"Unexpected status: {response.status_code}")
                break

            # Парсинг вариантов ответов
            soup = BeautifulSoup(response.text, 'html.parser')
            answer_options = [input_tag.get('value') for input_tag in soup.find_all('input')]

            if not answer_options:
                print("No answers found")
                print("HTML content:", response.text)  # Логирование HTML содержимого для отладки
                break

            # Выбор случайного ответа
            self.selected_answer = random.choice(answer_options)

            # Отправка ответа
            response = self.client.post(
                "/answer",
                {"answers": self.selected_answer},
                name="POST /answer",
                allow_redirects=True  # Разрешить редиректы
            )

            if response.status_code not in [200, 302]:
                print(f"Unexpected status: {response.status_code}")
                break

        # Получение результатов
        self._get_results()

    def _get_results(self):
        """Вспомогательный метод для получения результатов с гарантированным именованием"""
        response = self.client.get("/results", name="GET /results")
        if response.status_code not in [200, 302]:
            print(f"Failed to get results with status code: {response.status_code}")
