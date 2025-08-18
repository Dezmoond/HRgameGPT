#!/usr/bin/env python3
"""
Отладочный скрипт для проверки загрузки .env файла
"""

import os
from dotenv import load_dotenv

print("🔍 Отладка загрузки .env файла...")

# Проверяем текущую директорию
print(f"📁 Текущая директория: {os.getcwd()}")

# Проверяем, существует ли файл .env
env_path = os.path.join(os.getcwd(), '.env')
print(f"📄 Путь к .env: {env_path}")
print(f"📄 Файл .env существует: {os.path.exists(env_path)}")

# Пробуем загрузить .env
try:
    load_dotenv('.env')
    print("✅ load_dotenv('.env') выполнен успешно")
except Exception as e:
    print(f"❌ Ошибка при load_dotenv('.env'): {e}")

# Проверяем переменные окружения
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
openai_key = os.getenv('OPENAI_API_KEY')

print(f"🔑 TELEGRAM_BOT_TOKEN: {'Найден' if telegram_token else 'НЕ НАЙДЕН'}")
if telegram_token:
    print(f"   Значение: {telegram_token[:20]}...")

print(f"🔑 OPENAI_API_KEY: {'Найден' if openai_key else 'НЕ НАЙДЕН'}")
if openai_key:
    print(f"   Значение: {openai_key[:20]}...")

# Пробуем прочитать файл напрямую
try:
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"📖 Содержимое .env файла:")
        print(content)
except Exception as e:
    print(f"❌ Ошибка при чтении .env: {e}")
