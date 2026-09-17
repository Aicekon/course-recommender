# Автоматизированный подбор онлайн-курсов на основе анализа учебных достижений

Информационная система для персонализированного подбора онлайн-курсов на основе адаптивного тестирования и анализа учебных достижений с применением NLP и машинного обучения.

## 📌 О проекте

Система решает проблему информационной перегрузки в онлайн-образовании: пользователь проходит адаптивный тест, а система на основе его ответов подбирает подходящие курсы и статьи.

**Как это работает:**

1. **Сбор информации** — парсеры собирают бесплатные курсы с LoftSchool, Stepik, Лекториум и статьи с Habr.
2. **Заполнение данными** — NLP-модели дополняют недостающие данные (теги, уровень сложности, тип статьи).
3. **Адаптивное тестирование** — вопросы подбираются индивидуально на основе предыдущих ответов пользователя.
4. **Анализ и подбор** — по результатам теста выдаются рекомендации курсов и материалов.

## 🛠️ Стек технологий

| Слой | Технологии |
|---|---|
| Язык | Python 3 |
| Веб-фреймворк | Flask, Flask-Session |
| База данных | PostgreSQL, psycopg2 |
| NLP / ML | Transformers (HuggingFace), PyTorch |
| Модели | Helsinki-NLP/opus-mt-ru-en, facebook/bart-large-mnli |
| Парсинг | requests, BeautifulSoup (bs4), lxml, Selenium |
| Визуализация | Matplotlib, base64 |
| Прочее | python-dotenv, passlib |

## 🚀 Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/ваш_логин/имя_репозитория.git
cd имя_репозитория
```

### 2. Создать виртуальное окружение и установить зависимости

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Скачать ML-модели

Модели не хранятся в репозитории из-за размера. Скачайте их скриптом:

```bash
python Models_dowloading.py
```

### 4. Настроить переменные окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

Содержимое `.env`:

```
SECRET_KEY=ваш_секретный_ключ
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=5432
```

### 5. Создать таблицы в БД

```bash
python users.py
python questions.py
python create_add_tables.py
```

### 6. Запустить приложение

```bash
python app.py
```

Приложение будет доступно по адресу http://127.0.0.1:5000

## 📁 Структура проекта

```
.
├── app.py                      # Flask-приложение (основной файл)
├── Models_dowloading.py        # Скрипт скачивания ML-моделей
├── users.py                    # Создание таблицы users
├── questions.py                # Создание таблиц questions, answers
├── create_add_tables.py        # Дополнительные таблицы (рейтинги, сессии)
├── import.py                   # Импорт вопросов из Excel
├── Habrparse.py                # Парсер статей с Habr
├── lektoriumparse.py           # Парсер курсов с Лекториум
├── LoftSchoolparse.py          # Парсер курсов с LoftSchool
├── stepikapi.py                # Работа с API Stepik
├── ArticlesClassify.py         # Классификация статей (NLP)
├── range_articles.py           # Оценка сложности статей
├── range_courses.py            # Оценка сложности курсов
├── tagging courses.py          # Тегирование курсов
├── templates/                  # HTML-шаблоны
├── static/                     # CSS, JS, изображения
├── docs/                       # Скриншоты
└── requirements.txt
```
## 🎬 Демонстрация

https://github.com/user-attachments/assets/c6715b03-56a1-4599-82a3-7d62666b59d7