from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
import psycopg2

# Список возможных тегов
TAGS = [
    'Python', 'JavaScript', 'Java', 'C#', 'C++', 'Операционные системы',
    'Тестирование', 'Системное администрирование', 'DevOps',
    'Data Science', 'Базы данных', 'Web-разработка', 'Информационная безопасность', 'Мобильная разработка',
    'Искусственный интеллект', 'Веб-дизайн', 'Робототехника', 'Figma', 'Blockchain'
]

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

# Определяем устройство для расчёта
device = "cuda" if torch.cuda.is_available() else "cpu"

# Загружаем наши локальные модели
translator_model_path = "models/translator"
classifier_model_path = "models/classifier"

# Конвейеры для обработки
translator = pipeline(
    task="translation",
    model=AutoModelForSeq2SeqLM.from_pretrained(translator_model_path),
    tokenizer=AutoTokenizer.from_pretrained(translator_model_path),
    device=device
)

classifier = pipeline(
    task="zero-shot-classification",
    model=AutoModelForSequenceClassification.from_pretrained(classifier_model_path),
    tokenizer=AutoTokenizer.from_pretrained(classifier_model_path),
    device=device
)

# Функция для обработки текста
def process_text(full_text):
    # Переводим текст на английский
    translation_result = translator(full_text, max_length=512)
    translated_text = translation_result[0]["translation_text"]

    # Оцениваем соответствие тегам
    result = classifier(translated_text, TAGS)

    # Фильтруем теги с высокой точностью (>= 0.5)
    filtered_tags = [(label, score) for label, score in zip(result['labels'], result['scores']) if score >= 0.3]

    return {"original": full_text, "filtered_tags": filtered_tags, "all_results": dict(zip(result['labels'], result['scores']))}

# Извлечение заголовков и описаний из базы данных
cur.execute('''
    SELECT id, название, краткое_описание, полное_описание FROM курсы WHERE тег IS NULL OR тег='';
''')
rows = cur.fetchall()

# Обработка каждого курса и обновление базы данных
for row in rows:
    course_id, title, short_desc, full_desc = row
    # Собираем полный текст для анализа
    full_text = f"{title}. {short_desc}. {full_desc}"

    # Анализируем текст
    result = process_text(full_text)

    # Преобразуем список тегов в строку, разделённую запятыми
    final_tags = ', '.join(tag for tag, _ in result['filtered_tags'])

    # Обновляем запись в базе данных
    cur.execute('''
        UPDATE курсы SET тег = %s WHERE id = %s;
    ''', (final_tags, course_id))
    conn.commit()  # Немедленно фиксируем изменения

    # Выводим промежуточные результаты
    print(f"\nОбработано: Курс '{title}'.")
    print("Присвоенные теги:", final_tags)
    print("\nПромежуточные результаты:")
    for label, score in sorted(result['all_results'].items(), key=lambda x: x[1], reverse=True):
        print(f"- {label}: {score:.3f}")

# Закрываем соединение с базой данных
cur.close()
conn.close()