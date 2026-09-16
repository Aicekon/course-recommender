from sentence_transformers import SentenceTransformer
import os

# Путь к папке, куда сохраним модель
model_dir = "../models/correlation"
model_name = "all-MiniLM-L6-v2"

# Создаем папку, если её нет
os.makedirs(model_dir, exist_ok=True)

# Загружаем модель и сохраняем локально
print(f"Скачивание модели {model_name}...")
model = SentenceTransformer(model_name)
model.save(os.path.join(model_dir, model_name))

print(f"Модель сохранена в папку: {os.path.abspath(model_dir)}")