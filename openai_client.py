import openai
import aiofiles
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Инициализация OpenAI клиента
openai.api_key = OPENAI_API_KEY

class OpenAIClient:
    def __init__(self):
        try:
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        except TypeError as e:
            if 'proxies' in str(e):
                # Исправление для старых версий openai
                import httpx
                self.client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    http_client=httpx.Client()
                )
            else:
                raise e
    
    async def load_prompt(self, filename):
        """Загружает промт из файла"""
        async with aiofiles.open(filename, 'r', encoding='utf-8') as file:
            return await file.read()
    
    async def get_response(self, prompt, user_message, conversation_history=None, interview_mode="hope", language="russian", name="Кандидат", interview_type="soft"):
        """Получает ответ от GPT на основе промта и сообщения пользователя"""
        try:
            # Формируем краткий дополнительный промт в зависимости от режима (как в блокноте)
            if interview_mode == "hope":
                if language == "russian":
                    user_prompt = f"""Агента-генератора вопросов зовут миссис Хоуп.
Роль агента: Ты - менеджер по персоналу в компании "Пегий дудочник"
Твоя задача: От ИМЕНИ МИСИС ХОУП проведи первичное собеседование (интервью) с претендентом (соискателем) на должность дата-сайентиста на русском языке.
Будь максимально дружелюбным интервьером для кандидата {name} и попытайся максимально раскрыть его потенциал своими вопросами.
Стремись максимально расположить к себе претендента и раскачать его на полноценный диалог, в котором он может полностью раскрыться.
Обращайся по имени {name}. Язык собеседования: Русский. Все вопросы кандидату задаются на языке собеседования.

Тип собеседования: {self._get_interview_type_description(interview_type, "russian")}"""
                else:  # english
                    user_prompt = f"""Агента-генератора вопросов зовут миссис Хоуп.
Роль агента: Ты - менеджер по персоналу в компании "Пегий дудочник"
Твоя задача: От ИМЕНИ МИСИС ХОУП проведи первичное собеседование (интервью) с претендентом (соискателем) на должность дата-сайентиста на английском языке.
Будь максимально дружелюбным интервьером для кандидата {name} и попытайся максимально раскрыть его потенциал своими вопросами.
Стремись максимально расположить к себе претендента и раскачать его на полноценный диалог, в котором он может полностью раскрыться.
Обращайся по имени {name}. Язык собеседования: Английский. Все вопросы кандидату задаются на языке собеседования.

Тип собеседования: {self._get_interview_type_description(interview_type, "english")}"""
            else:  # teacher
                user_prompt = f"""Агента-генератора вопросов зовут "Преподаватель".
Роль агента: Ты - преподаватель английского языка в компании "Пегий дудочник" и ты хочешь проверить уровень английского соискателя на должность в Вашей компании.
Твоя задача: ОТ ИМЕНИ ПРЕПОДАВАТЕЛЯ проведи первичное собеседование (интервью) с претендентом (соискателем) на должность дата-сайентиста на английском языке. Язык собеседования: английский
Все вопросы кандидату {name} должны быть заданы на английском языке и если в ответе кандидата содержатся грамматические или лексические ошибки,
то указывай каждую грамматическую и лексическую ошибку в ответе кандидата. Выдавай исправленную версию ответа кандидата без ошибок.
Обращайся по имени {name}

Тип собеседования: {self._get_interview_type_description(interview_type, "english")}

ВАЖНО: После каждого ответа кандидата сразу разбирай все ошибки и выдавай исправленную версию."""
            
            # Формируем сообщения для API (как в блокноте)
            messages = [
                {"role": "system", "content": prompt},  # Основной мега-промт
                {"role": "user", "content": user_prompt + f"\n\nИстория диалога (раннее заданные вопросы не должны повторяться):{' '.join([msg['text'] for msg in conversation_history]) if conversation_history else ''}\nСообщение от студента: {user_message}"}
            ]
            
            # История диалога уже добавлена в user_prompt
            
            # Отправляем запрос к API
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Ошибка при обращении к OpenAI API: {e}")
            return "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз."
    
    async def generate_analytics_report(self, conversation_history):
        """Генерирует аналитический отчет на основе истории диалога"""
        try:
            # Загружаем промт для аналитики
            analytics_prompt = await self.load_prompt("analytics_prompt.txt")
            
            # Формируем текст диалога для анализа
            dialog_text = "Диалог между рекрутером и кандидатом:\n\n"
            for msg in conversation_history:
                speaker = "Рекрутер" if msg["is_bot"] else "Кандидат"
                dialog_text += f"{speaker}: {msg['text']}\n\n"
            
            # Получаем аналитический отчет
            messages = [
                {"role": "system", "content": analytics_prompt},
                {"role": "user", "content": f"Проанализируй следующий диалог и создай отчет:\n\n{dialog_text}"}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                max_tokens=3000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Ошибка при генерации аналитического отчета: {e}")
            return "Не удалось сгенерировать аналитический отчет."

    def _get_interview_type_description(self, interview_type, language):
        """Возвращает описание типа собеседования на указанном языке"""
        if language == "russian":
            descriptions = {
                "soft": "Soft Skills (мягкие навыки) - коммуникация, лидерство, работа в команде, решение конфликтов",
                "hard": "Hard Skills (технические навыки) - программирование, анализ данных, машинное обучение, статистика",
                "experience": "Experience (опыт работы) - предыдущие проекты, достижения, карьерный путь"
            }
        else:  # english
            descriptions = {
                "soft": "Soft Skills - communication, leadership, teamwork, conflict resolution",
                "hard": "Hard Skills - programming, data analysis, machine learning, statistics",
                "experience": "Experience - previous projects, achievements, career path"
            }
        
        return descriptions.get(interview_type, descriptions["soft"])

