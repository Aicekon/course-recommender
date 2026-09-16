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
        # Объединяем название и описание для более точной классификации
        combined_text = text['название'] + ". " + (text['краткое_описание'] or "") + " " + (
                    text['полное_описание'] or "")

        # Перевод текста (если нужно)
        translated = translator(combined_text, max_length=512)[0]['translation_text']

        # Категории сложности
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
            "classification": {
                "label": complexity_mapping.get(best_label, "normal"),  # default to normal
                "score": best_score
            }
        }
    except Exception as e:
        print(f"Ошибка при обработке текста: {e}")
        return None


# Извлечение курсов с пустым уровнем сложности
cur.execute('''
    SELECT id, название, краткое_описание, полное_описание 
    FROM курсы 
    WHERE уровень_сложности IS NULL OR уровень_сложности = '';
''')
rows = cur.fetchall()

total_courses = len(rows)
print(f"Найдено курсов для обработки: {total_courses}")

if total_courses == 0:
    print("Нет курсов для обработки. Выход.")
    cur.close()
    conn.close()
    exit()

# Обработка курсов с прогресс-баром
processed = 0
for row in tqdm(rows, desc="Оценка сложности курсов"):
    course_id, title, short_desc, full_desc = row
    remaining = total_courses - processed - 1

    try:
        # Подготовка текста для анализа
        text_data = {
            'название': title,
            'краткое_описание': short_desc,
            'полное_описание': full_desc
        }

        # Обработка текста
        result = process_complexity(text_data)

        if result is None:
            print(f"\n[Курс ID {course_id}] Ошибка обработки, пропуск")
            continue

        complexity = result['classification']['label']
        score = result['classification']['score']

        # Обновление записи в базе данных
        cur.execute('''
            UPDATE курсы 
            SET уровень_сложности = %s 
            WHERE id = %s;
        ''', (complexity, course_id))
        conn.commit()

        processed += 1
        print(f"\n[Курс ID {course_id}] Успешно обработано. Сложность: '{complexity}' (точность: {score:.2f})")
        print(f"Осталось обработать: {remaining} курсов")

    except Exception as e:
        print(f"\n[Курс ID {course_id}] Ошибка при обновлении БД: {e}")
        conn.rollback()

# Итоговая статистика
print("\nОбработка завершена!")
print(f"Всего обработано: {processed}/{total_courses} курсов")
print(f"Не удалось обработать: {total_courses - processed} курсов")

# Закрытие соединения с базой данных
cur.close()
conn.close()