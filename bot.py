import asyncio
import logging
import os
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

from openai_client import OpenAIClient
from document_generator import DocumentGenerator

# Загружаем переменные окружения
load_dotenv('.env')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не найден в переменных окружения")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Инициализация клиентов
openai_client = OpenAIClient()
doc_generator = DocumentGenerator()

# Словарь для хранения состояния пользователей
user_states = {}

def create_mode_keyboard():
    """Создает клавиатуру для выбора режима собеседования"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤝 Миссис Хоуп (дружелюбный менеджер)", callback_data="mode_hope")
        ],
        [
            InlineKeyboardButton(text="👨‍🏫 Преподаватель английского (для уровня A1)", callback_data="mode_teacher")
        ]
    ])
    return keyboard

def create_language_keyboard():
    """Создает клавиатуру для выбора языка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_russian")
        ],
        [
            InlineKeyboardButton(text="🇬🇧 Английский", callback_data="lang_english")
        ]
    ])
    return keyboard

def create_interview_type_keyboard():
    """Создает клавиатуру для выбора типа собеседования"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Soft Skills (мягкие навыки)", callback_data="type_soft")
        ],
        [
            InlineKeyboardButton(text="💻 Hard Skills (технические навыки)", callback_data="type_hard")
        ],
        [
            InlineKeyboardButton(text="📋 Experience (опыт работы)", callback_data="type_experience")
        ]
    ])
    return keyboard

async def set_commands():
    """Устанавливает команды бота в главное меню"""
    commands = [
        BotCommand(command="start", description="Начать собеседование"),
        BotCommand(command="stop", description="Завершить собеседование"),
        BotCommand(command="help", description="Справка")
    ]
    await bot.set_my_commands(commands)

class UserState:
    def __init__(self, user_id):
        self.user_id = user_id
        self.conversation_history = []
        self.is_interview_active = False
        self.prompt = None
        self.interview_mode = None  # "hope" или "teacher"
        self.language = None  # "russian" или "english"
        self.interview_type = None  # "soft", "hard", "experience"
        self.name = None
        self.is_setup_complete = False
    
    def add_message(self, text, is_bot=False):
        """Добавляет сообщение в историю диалога"""
        self.conversation_history.append({
            "text": text,
            "is_bot": is_bot,
            "timestamp": datetime.now()
        })
    
    def get_conversation_history(self):
        """Возвращает историю диалога для OpenAI API"""
        return self.conversation_history
    
    def filter_technical_info(self, response):
        """Убирает техническую информацию из ответа AI для пользователя"""
        # Всегда удаляем все блоки в фигурных скобках для Telegram
        filtered_response = re.sub(r'\{[^}]*\}', '', response)
        
        # Убираем лишние пустые строки
        lines = filtered_response.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Добавляем только непустые строки
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines).strip()



@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    # Инициализируем состояние пользователя
    if user_id not in user_states:
        user_states[user_id] = UserState(user_id)
    
    user_state = user_states[user_id]
    
    # Проверяем, есть ли уже выбранные параметры
    if (user_state.interview_mode and user_state.language and 
        user_state.interview_type and user_state.name and 
        user_state.is_setup_complete and not user_state.is_interview_active):
        # Если параметры выбраны, но собеседование не активно - продолжаем
        user_state.is_interview_active = True
        
        # Убираем приветственное сообщение - сразу начинаем собеседование
        
        # Отправляем сообщение "Бот думает..."
        thinking_message = await message.answer("🤔 Бот думает...")
        
        # Получаем первое сообщение от AI
        try:
            first_message = await openai_client.get_response(
                user_state.prompt,
                f"Начало собеседования с {user_state.name}",
                [],
                user_state.interview_mode,
                user_state.language,
                user_state.name,
                user_state.interview_type
            )
            
            # Удаляем сообщение "Бот думает..."
            await thinking_message.delete()
            
            # Добавляем полный ответ в историю (для DOCX)
            user_state.add_message(first_message, is_bot=True)
            
            # Фильтруем техническую информацию для пользователя
            filtered_first_message = user_state.filter_technical_info(first_message)
            await message.answer(filtered_first_message)
            
        except Exception as e:
            # Удаляем сообщение "Бот думает..." в случае ошибки
            await thinking_message.delete()
            logger.error(f"Ошибка при получении первого сообщения: {e}")
            await message.answer("Извините, произошла ошибка при инициализации собеседования.")
        return
    
    # Если параметры не выбраны или нужно начать заново - сбрасываем состояние
    user_state.is_interview_active = False
    user_state.is_setup_complete = False
    user_state.interview_mode = None
    user_state.language = None
    user_state.interview_type = None
    user_state.name = None
    user_state.conversation_history = []
    
    # Промт будет загружен после выбора типа собеседования
    # Пока оставляем None - загрузим позже
    
    # Показываем выбор режима собеседования
    welcome_text = """🤖 Добро пожаловать в бот для проведения собеседований!

Выберите режим собеседования:

🤝 **Миссис Хоуп** - дружелюбный менеджер по персоналу
• Можно выбрать русский или английский язык
• Поддерживающая атмосфера
• Помощь с переводом слов

👨‍🏫 **Преподаватель английского** - для студентов уровня A1
• Только английский язык
• Анализ грамматических и лексических ошибок
• Исправленная версия ответов после каждого сообщения
• Рекомендуется для начинающих изучать английский

Выберите режим:"""
    
    await message.answer(welcome_text, reply_markup=create_mode_keyboard())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = """🤖 **Доступные команды:**
/start - Начать собеседование
/stop - Завершить собеседование
/help - Показать эту справку

📋 **Во время собеседования вы можете:**
• Отвечать на вопросы рекрутера
• Задавать уточняющие вопросы
• Просить перевести английские слова
• Завершить собеседование командой /stop или написав "стоп"

📄 **После завершения вы получите аналитический отчет в формате DOCX**"""
    
    await message.answer(help_text)

@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    """Обработчик команды /stop для завершения собеседования"""
    user_id = message.from_user.id
    
    if user_id not in user_states or not user_states[user_id].is_interview_active:
        await message.answer("Собеседование не активно. Используйте /start для начала.")
        return
    
    user_state = user_states[user_id]
    
    # Отправляем сообщение о завершении
    await message.answer("Завершаю собеседование...")
    
    # Генерируем аналитический отчет
    await message.answer("Генерирую аналитический отчет...")
    
    try:
        analytics_report = await openai_client.generate_analytics_report(
            user_state.get_conversation_history()
        )
        
        # Создаем документ
        doc_generator.generate_report(
            user_id, 
            user_state.get_conversation_history(), 
            analytics_report
        )
        
        # Сохраняем документ
        doc_path = doc_generator.save_document(user_id)
        
        # Отправляем документ пользователю
        with open(doc_path, 'rb') as doc_file:
            await message.answer_document(
                types.BufferedInputFile(
                    doc_file.read(),
                    filename=f"interview_report_{user_id}.docx"
                ),
                caption="Ваш отчет по собеседованию готов!"
            )
        
        # Полностью сбрасываем состояние пользователя для нового собеседования
        user_state.is_interview_active = False
        user_state.is_setup_complete = False
        user_state.interview_mode = None
        user_state.language = None
        user_state.interview_type = None
        user_state.name = None
        user_state.conversation_history = []
        user_state.prompt = None
        
        await message.answer("Собеседование завершено. Спасибо за участие!")
        await message.answer("Для начала нового собеседования нажмите /start")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации отчета: {e}")
        await message.answer("Извините, произошла ошибка при генерации отчета.")


@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    """Обработчик инлайн-кнопок"""
    user_id = callback.from_user.id
    
    if user_id not in user_states:
        await callback.answer("Пожалуйста, начните с команды /start")
        return
    
    user_state = user_states[user_id]
    
    if callback.data == "mode_hope":
        user_state.interview_mode = "hope"
        await callback.message.edit_text(
            "🤝 Выбран режим: Миссис Хоуп\n\n"
            "Теперь выберите язык собеседования:",
            reply_markup=create_language_keyboard()
        )
        await callback.answer()
        
    elif callback.data == "mode_teacher":
        user_state.interview_mode = "teacher"
        user_state.language = "english"  # Преподаватель только на английском
        await callback.message.edit_text(
            "👨‍🏫 Выбран режим: Преподаватель английского\n\n"
            "Язык собеседования: Английский\n\n"
            "Теперь выберите тип собеседования:",
            reply_markup=create_interview_type_keyboard()
        )
        await callback.answer()
        
    elif callback.data == "lang_russian":
        user_state.language = "russian"
        await callback.message.edit_text(
            "🇷🇺 Выбран язык: Русский\n\n"
            "Теперь выберите тип собеседования:",
            reply_markup=create_interview_type_keyboard()
        )
        await callback.answer()
        
    elif callback.data == "lang_english":
        user_state.language = "english"
        await callback.message.edit_text(
            "🇬🇧 Выбран язык: Английский\n\n"
            "Теперь выберите тип собеседования:",
            reply_markup=create_interview_type_keyboard()
        )
        await callback.answer()
        
    elif callback.data == "type_soft":
        user_state.interview_type = "soft"
        # Загружаем правильный промт для Soft Skills
        try:
            user_state.prompt = await openai_client.load_prompt("Промт Soft Skills нейро-рекрутера для собеседований.txt")
        except Exception as e:
            logger.error(f"Ошибка загрузки промта Soft Skills: {e}")
            user_state.prompt = await openai_client.load_prompt("prompt.txt")  # Fallback
        
        await callback.message.edit_text(
            "💬 Выбран тип: Soft Skills (мягкие навыки)\n\n"
            "Как я могу к вам обращаться? (Введите ваше имя)"
        )
        await callback.answer()
        
    elif callback.data == "type_hard":
        user_state.interview_type = "hard"
        # Загружаем правильный промт для Hard Skills
        try:
            user_state.prompt = await openai_client.load_prompt("Промт Hard Skills нейро-рекрутера для собеседований.txt")
        except Exception as e:
            logger.error(f"Ошибка загрузки промта Hard Skills: {e}")
            user_state.prompt = await openai_client.load_prompt("prompt.txt")  # Fallback
        
        await callback.message.edit_text(
            "💻 Выбран тип: Hard Skills (технические навыки)\n\n"
            "Как я могу к вам обращаться? (Введите ваше имя)"
        )
        await callback.answer()
        
    elif callback.data == "type_experience":
        user_state.interview_type = "experience"
        # Загружаем правильный промт для Experience
        try:
            user_state.prompt = await openai_client.load_prompt("prompt.txt")
        except Exception as e:
            logger.error(f"Ошибка загрузки промта Experience: {e}")
            user_state.prompt = await openai_client.load_prompt("prompt.txt")  # Fallback
        
        await callback.message.edit_text(
            "📋 Выбран тип: Experience (опыт работы)\n\n"
            "Как я могу к вам обращаться? (Введите ваше имя)"
        )
        await callback.answer()


@dp.message()
async def handle_message(message: types.Message):
    """Обработчик всех текстовых сообщений"""
    user_id = message.from_user.id
    user_text = message.text.strip().lower()
    
    # Проверяем, есть ли пользователь в системе
    if user_id not in user_states:
        await message.answer("Пожалуйста, начните собеседование командой /start")
        return
    
    user_state = user_states[user_id]
    
    # Если настройка не завершена, обрабатываем ввод имени
    if not user_state.is_setup_complete and user_state.interview_type and user_state.interview_mode and user_state.language:
        user_state.name = message.text.strip()
        user_state.is_setup_complete = True
        user_state.is_interview_active = True
        
        # Убираем приветственное сообщение - сразу начинаем собеседование
        
        # Получаем первое сообщение от AI
        try:
            first_message = await openai_client.get_response(
                user_state.prompt,
                f"Начало собеседования с {user_state.name}",
                [],
                user_state.interview_mode,
                user_state.language,
                user_state.name,
                user_state.interview_type
            )
            
            # Добавляем полный ответ в историю (для DOCX)
            user_state.add_message(first_message, is_bot=True)
            
            # Фильтруем техническую информацию для пользователя
            filtered_first_message = user_state.filter_technical_info(first_message)
            await message.answer(filtered_first_message)
            
        except Exception as e:
            logger.error(f"Ошибка при получении первого сообщения: {e}")
            await message.answer("Извините, произошла ошибка при инициализации собеседования.")
        return
    
    # Проверяем, есть ли активное собеседование
    if not user_state.is_interview_active:
        # Если настройка завершена, но собеседование не активно - активируем его
        if user_state.is_setup_complete and user_state.name:
            user_state.is_interview_active = True
            
            # Убираем приветственное сообщение - сразу начинаем собеседование
            
            # Отправляем сообщение "Бот думает..."
            thinking_message = await message.answer("🤔 Бот думает...")
            
            # Получаем первое сообщение от AI
            try:
                first_message = await openai_client.get_response(
                    user_state.prompt,
                    f"Начало собеседования с {user_state.name}",
                    [],
                    user_state.interview_mode,
                    user_state.language,
                    user_state.name,
                    user_state.interview_type
                )
                
                # Удаляем сообщение "Бот думает..."
                await thinking_message.delete()
                
                # Добавляем полный ответ в историю (для DOCX)
                user_state.add_message(first_message, is_bot=True)
                
                # Фильтруем техническую информацию для пользователя
                filtered_first_message = user_state.filter_technical_info(first_message)
                await message.answer(filtered_first_message)
                
            except Exception as e:
                # Удаляем сообщение "Бот думает..." в случае ошибки
                await thinking_message.delete()
                logger.error(f"Ошибка при получении первого сообщения: {e}")
                await message.answer("Извините, произошла ошибка при инициализации собеседования.")
            return
        else:
            # Если настройка не завершена, показываем инструкцию
            await message.answer("Пожалуйста, завершите настройку собеседования, выбрав режим, язык и тип собеседования.")
            return
    
    # Проверяем, не хочет ли пользователь завершить собеседование
    if user_text in ["стоп", "stop", "завершить", "конец", "закончить"]:
        await message.answer("Завершаю собеседование...")
        
        # Генерируем аналитический отчет
        await message.answer("Генерирую аналитический отчет...")
        
        try:
            analytics_report = await openai_client.generate_analytics_report(
                user_state.get_conversation_history()
            )
            
            # Создаем документ
            doc_generator.generate_report(
                user_id, 
                user_state.get_conversation_history(), 
                analytics_report
            )
            
            # Сохраняем документ
            doc_path = doc_generator.save_document(user_id)
            
            # Отправляем документ пользователю
            with open(doc_path, 'rb') as doc_file:
                await message.answer_document(
                    types.BufferedInputFile(
                        doc_file.read(),
                        filename=f"interview_report_{user_id}.docx"
                    ),
                    caption="Ваш отчет по собеседованию готов!"
                )
            
            # Полностью сбрасываем состояние пользователя для нового собеседования
            user_state.is_interview_active = False
            user_state.is_setup_complete = False
            user_state.interview_mode = None
            user_state.language = None
            user_state.interview_type = None
            user_state.name = None
            user_state.conversation_history = []
            user_state.prompt = None
            
            await message.answer("Собеседование завершено. Спасибо за участие!")
            await message.answer("Для начала нового собеседования нажмите /start")
            return
            
        except Exception as e:
            logger.error(f"Ошибка при генерации отчета: {e}")
            await message.answer("Извините, произошла ошибка при генерации отчета.")
            return
    
    # Добавляем сообщение пользователя в историю (используем оригинальный текст)
    user_state.add_message(message.text, is_bot=False)
    
    # Отправляем сообщение "Бот думает..."
    thinking_message = await message.answer("🤔 Бот думает...")
    
    try:
        # Получаем ответ от AI
        bot_response = await openai_client.get_response(
            user_state.prompt,
            message.text,
            user_state.get_conversation_history()[:-1],  # Исключаем текущее сообщение
            user_state.interview_mode,
            user_state.language,
            user_state.name,
            user_state.interview_type
        )
        
        # Удаляем сообщение "Бот думает..."
        await thinking_message.delete()
        
        # Добавляем полный ответ бота в историю (для DOCX)
        user_state.add_message(bot_response, is_bot=True)
        
        # Фильтруем техническую информацию для пользователя
        filtered_response = user_state.filter_technical_info(bot_response)
        
        # Отправляем отфильтрованный ответ пользователю
        await message.answer(filtered_response)
        
    except Exception as e:
        # Удаляем сообщение "Бот думает..." в случае ошибки
        await thinking_message.delete()
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await message.answer(
            "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз."
        )

async def main():
    """Главная функция"""
    logger.info("Запуск бота...")
    
    # Устанавливаем команды бота
    await set_commands()

    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

