from transformers import pipeline
import torch
import psycopg2
from tqdm import tqdm  # Для красивого прогресс-бара

# Подключение к базе данных
db_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '1111',
    'host': 'localhost',
    'port': '5432'
}

conn = psycopg2.connect(**db_params)
cur = conn.cursor()

# Загрузка локальных моделей
device = "cuda" if torch.cuda.is_available() else "cpu"

try:
    translator = pipeline(
        "translation",
        model="models/translator",
        tokenizer="models/translator",
        device=device
    )

    classifier = pipeline(
        "zero-shot-classification",
        model="models/classifier",
        tokenizer="models/classifier",
        device=device
    )
except Exception as e:
    print(f"Ошибка при загрузке моделей: {e}")
    exit(1)


# Функция для обработки текста
def process_text(text):
    try:
        # Перевод
        translated = translator(text, max_length=512)[0]['translation_text']

        # Классификация
        categories = ["technical tutorial", "news/announcement", "opinion/discussion"]
        result = classifier(translated, categories)

        # Выбираем категорию с наивысшей вероятностью
        best_label = result['labels'][0]
        best_score = float(result['scores'][0])

        return {
            "original": text,
            "translation": translated,
            "classification": {
                "label": best_label,
                "score": best_score
            }
        }
    except Exception as e:
        print(f"Ошибка при обработке текста: {e}")
        return None


# Извлечение заголовков из базы данных (только строки с пустым informational_value)
cur.execute('''
    SELECT id, title FROM articles 
    WHERE informational_value IS NULL OR informational_value = '';
''')
rows = cur.fetchall()

total_articles = len(rows)
print(f"Найдено статей для обработки: {total_articles}")

if total_articles == 0:
    print("Нет статей для обработки. Выход.")
    cur.close()
    conn.close()
    exit()

# Обработка заголовков с прогресс-баром
processed = 0
for row in tqdm(rows, desc="Обработка статей"):
    article_id, title = row
    remaining = total_articles - processed - 1

    try:
        # Обработка текста
        result = process_text(title)

        if result is None:
            print(f"\n[Статья ID {article_id}] Ошибка обработки, пропуск")
            continue

        label = result['classification']['label']
        score = result['classification']['score']

        # Обновление записи в базе данных
        cur.execute('''
            UPDATE articles 
            SET informational_value = %s 
            WHERE id = %s;
        ''', (label, article_id))
        conn.commit()

        processed += 1
        print(f"\n[Статья ID {article_id}] Успешно обработано. Категория: '{label}' (точность: {score:.2f})")
        print(f"Осталось обработать: {remaining} статей")

    except Exception as e:
        print(f"\n[Статья ID {article_id}] Ошибка при обновлении БД: {e}")
        conn.rollback()

# Итоговая статистика
print("\nОбработка завершена!")
print(f"Всего обработано: {processed}/{total_articles} статей")
print(f"Не удалось обработать: {total_articles - processed} статей")

# Закрытие соединения с базой данных
cur.close()
conn.close()