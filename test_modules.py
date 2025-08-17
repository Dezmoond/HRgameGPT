#!/usr/bin/env python3
"""
Тестовый файл для проверки работы модулей без токенов
"""

import os
import sys

# Временно устанавливаем тестовые значения
os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
os.environ['OPENAI_API_KEY'] = 'test_key'

def test_imports():
    """Тестирует импорт всех модулей"""
    try:
        print("Тестирование импорта модулей...")
        
        # Тестируем импорт конфига
        import config
        print("✓ config.py импортируется успешно")
        
        # Тестируем импорт OpenAI клиента
        from openai_client import OpenAIClient
        print("✓ openai_client.py импортируется успешно")
        
        # Тестируем импорт генератора документов
        from document_generator import DocumentGenerator
        print("✓ document_generator.py импортируется успешно")
        
        # Тестируем создание экземпляров классов
        openai_client = OpenAIClient()
        doc_generator = DocumentGenerator()
        print("✓ Экземпляры классов создаются успешно")
        
        print("\n🎉 Все модули работают корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def test_document_generator():
    """Тестирует генератор документов"""
    try:
        print("\nТестирование генератора документов...")
        
        from document_generator import DocumentGenerator
        from datetime import datetime
        
        # Создаем тестовые данные
        user_id = 12345
        conversation_history = [
            {
                "text": "Привет!",
                "is_bot": True,
                "timestamp": datetime.now()
            },
            {
                "text": "Здравствуйте!",
                "is_bot": False,
                "timestamp": datetime.now()
            }
        ]
        analytics_report = "Тестовый аналитический отчет"
        
        # Создаем документ
        doc_generator = DocumentGenerator()
        doc_generator.generate_report(user_id, conversation_history, analytics_report)
        
        # Сохраняем документ
        doc_path = doc_generator.save_document(user_id)
        print(f"✓ Документ создан и сохранен: {doc_path}")
        
        # Проверяем, что файл существует
        if os.path.exists(doc_path):
            print("✓ Файл документа существует")
            # Удаляем тестовый файл
            os.remove(doc_path)
            print("✓ Тестовый файл удален")
        else:
            print("❌ Файл документа не найден")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании генератора документов: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Запуск тестирования модулей...\n")
    
    # Тестируем импорты
    imports_ok = test_imports()
    
    # Тестируем генератор документов
    if imports_ok:
        doc_ok = test_document_generator()
    else:
        doc_ok = False
    
    print(f"\n📊 Результаты тестирования:")
    print(f"Импорты: {'✅' if imports_ok else '❌'}")
    print(f"Генератор документов: {'✅' if doc_ok else '❌'}")
    
    if imports_ok and doc_ok:
        print("\n🎯 Все тесты пройдены! Бот готов к настройке.")
    else:
        print("\n⚠️  Некоторые тесты не пройдены. Проверьте код.")

