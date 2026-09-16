from transformers import pipeline
import torch
import psycopg2
from tqdm import tqdm

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


# Функция для обработки текста и определения сложности
def process_complexity(text):
    try:
        # Перевод заголовка (если нужно)
        translated = translator(text, max_length=512)[0]['translation_text']

        # Категории сложности на английском (для лучшего понимания моделью)
        complexity_categories = [
            "for beginners",  # -> easy
            "for intermediate level",  # -> normal
            "for experts"  # -> hard
        ]

        # Классификация
        result = classifier(translated, complexity_categories)

        # Выбираем категорию с наивысшей вероятностью
        best_label = result['labels'][0]
        best_score = float(result['scores'][0])

        # Преобразуем в наши стандартные значения
        complexity_mapping = {
            "for beginners": "easy",
            "for intermediate level": "normal",
            "for experts": "hard"
        }

        return {
            "original": text,
            "translation": translated,
            "classification": {
                "label": complexity_mapping.get(best_label, "normal"),  # default to normal
                "score": best_score
            }
        }
    except Exception as e:
        print(f"Ошибка при обработке текста: {e}")
        return None


# Извлечение технических статей с пустым complexity_level
cur.execute('''
    SELECT id, title FROM articles 
    WHERE informational_value = 'technical tutorial' 
    AND (complexity_level IS NULL OR complexity_level = '');
''')
rows = cur.fetchall()

total_articles = len(rows)
print(f"Найдено технических статей для обработки: {total_articles}")

if total_articles == 0:
    print("Нет статей для обработки. Выход.")
    cur.close()
    conn.close()
    exit()

# Обработка статей с прогресс-баром
processed = 0
for row in tqdm(rows, desc="Оценка сложности статей"):
    article_id, title = row
    remaining = total_articles - processed - 1

    try:
        # Обработка текста
        result = process_complexity(title)

        if result is None:
            print(f"\n[Статья ID {article_id}] Ошибка обработки, пропуск")
            continue

        complexity = result['classification']['label']
        score = result['classification']['score']

        # Обновление записи в базе данных
        cur.execute('''
            UPDATE articles 
            SET complexity_level = %s 
            WHERE id = %s;
        ''', (complexity, article_id))
        conn.commit()

        processed += 1
        print(f"\n[Статья ID {article_id}] Успешно обработано. Сложность: '{complexity}' (точность: {score:.2f})")
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