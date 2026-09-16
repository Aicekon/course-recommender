from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, AutoModelForSequenceClassification
import os

# Создаем папку для моделей
os.makedirs("../models", exist_ok=True)

# 1. Модель для перевода (рус -> англ)
print("Скачиваю модель перевода...")
translator_model = "Helsinki-NLP/opus-mt-ru-en"
AutoModelForSeq2SeqLM.from_pretrained(translator_model).save_pretrained("models/translator")
AutoTokenizer.from_pretrained(translator_model).save_pretrained("models/translator")

# 2. Модель для классификации
print("Скачиваю модель классификации...")
classifier_model = "facebook/bart-large-mnli"
AutoModelForSequenceClassification.from_pretrained(classifier_model).save_pretrained("models/classifier")
AutoTokenizer.from_pretrained(classifier_model).save_pretrained("models/classifier")


print("Все модели успешно скачаны в папку 'models'!")