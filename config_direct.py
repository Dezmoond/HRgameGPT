import os

# Конфигурация бота - используем переменные окружения напрямую
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Проверяем наличие необходимых токенов
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не найден в переменных окружения")

print(f"✅ TELEGRAM_BOT_TOKEN найден: {TELEGRAM_BOT_TOKEN[:10]}...")
print(f"✅ OPENAI_API_KEY найден: {OPENAI_API_KEY[:10]}...")

