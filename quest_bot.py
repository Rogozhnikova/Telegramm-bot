import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


# Список шагов квеста с координатами
quest_steps = [
    {
        "description": "Начинаем наше приключение",
        "question": "Первая точка — памятник изобретателю радио. В каком году он установлен?",
        "answer_type": "text",  # Тип ответа: текст
        "correct_answer": "1975",  # Правильный ответ (в нижнем регистре)
        "hint": "Этот год находится между 1970 и 1980.",  # Подсказка
    },
    {
        "description": "Теперь в конце аллеи найди здание с двумя флагами и прочти черную табличку на нем.",
        "question": "Кто останавливался там на пути из Сибири?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "декабристы",
    },
    {
        "description": "Развернись на 180 градусов. Справа есть здание — иди к нему.",
        "question": "Сколько этажей это здание?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "10",
        "hint": "здание высокое и у него есть табличка, там в первых строчках написан ответ",  # Подсказка
    },
    {
        "description": "Слева на соседнем здании будет рисунок",
        "question": "Что изображено под числом 24?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "алмазные палки",
        "hint": "какие-то палки"
    },
    {
        "description": "Иди прямо и найди граффити 'Мы станем лучше'",
        "question": "Какое число есть рядом с надписью на этой же стене?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "180",
        "hint": "число находится в конце слова 'лучше'",  # Подсказка
    },
    {
        "description": "Идем дальше по улице. По пути будет историческое здание",
        "question": "Кто жил в этом доме?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "мамин-сибиряк",
        "hint": "улица Пушкина, 27",  # Подсказка
    },
    {
        "description": "Чуть дальше будет памятник Пушкину",
        "question": "Что написано внизу?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "веленью божию, о муза, будь послушна...",
        "hint": "это строчка из его стихотворения, обрати внимание на пробелы, запятые и точки",  # Подсказка
    },
    {
        "description": "Не будем уходить далеко. Иди по улице Первомайская до улицы Царская",
        "question": "Ты найдешь афишу. В ней есть название квартала. Напиши его",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "литературный",
    },
    {
        "description": "Если стоять лицом к афише, то слева будет еще одно памятное место. Иди к нему",
        "question": "Какая фамилия написана там?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "егоров",
        "hint": "фамилия написана в левом нижнем углу",  # Подсказка
    },
    {
        "description": "На перекрестке направо. Дорогу не переходи и иди прямо",
        "question": "Вывеска какого бара видна?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "янки",
    },
    {
        "description": "На другой стороне дороги будет объект культурного наследия.Пожалуйста, переходите дорогу по пешеходному переходу",
        "question": "Чей дом? (укажи только фамилию)",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "селивановой",
        "hint": "нужно написать точно так же, как и в табличке на здании",  # Подсказка
    },
    {
        "description": "Иди дальше в сторону проспекта Ленина. Видишь граффити с мистическими существами?",
        "question": "Какого цвета то существо, которое имеет всего две ноги?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "белого",
    },
    {
        "description": "Иди дальше. Ты встретишь много котиков.",
        "question": "Они двух цветов. Но какого цвета больше?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "красного",
        "hint": "котики сидят за окном и машут лапкой, внимательно смотри по сторонам",  # Подсказка
    },
    {
        "description": "Знаешь, где находиться академия музыкальной комедии?",
        "question": "Какого цвета кружки на дверях?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "желтого",
    },
]

# Функция для создания клавиатуры с кнопкой "Подсказка"
def create_keyboard(options=None):
    keyboard = []
    if options:
        keyboard += [[InlineKeyboardButton(option, callback_data=str(i))] for i, option in enumerate(options)]
    keyboard.append([InlineKeyboardButton("Подсказка ❓", callback_data="hint")])
    return InlineKeyboardMarkup(keyboard)

# Главная клавиатура (теперь не нужна, но оставлена для совместимости)
def create_main_keyboard():
    return ReplyKeyboardMarkup([["Начать квест"]], resize_keyboard=True)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📌 Начни свое приключение прямо сейчас и открой для себя мир уличных квестов!\n"
        "💪 Собери своих друзей или отправляйся в путь в одиночку — главное, будь готов к новым открытиям и ярким эмоциям! 💪\n"
        "💰 Стоимость участия всего 100 рублей\n" 
        "(На одного человека)"
        "В этом квесте тебя ждут интересные задания, которые проверят твою смекалку и внимательность.\n"
        "А в конце ты получишь вкусный подарок 🎁 ",
        reply_markup=create_main_keyboard()
    )
    context.user_data['step'] = 0  # Начинаем квест с первого шага

# Обработка нажатия на кнопку "Начать квест"
async def handle_quest_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['step'] = 0
    await send_step(update, context)

# Отправка текущего шага квеста
async def send_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    step_index = context.user_data.get('step', 0)
    if step_index < len(quest_steps):
        step = quest_steps[step_index]
        message = f"{step['description']}\n{step['question']}"
        reply_markup = create_keyboard()
        await update.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            " Поздравляем! Вы успешно завершили квест и раскрыли все его тайны. Надеемся, вам понравилось это приключение! \n"
            "Награду вы можете выбрать сами кофе в Жизньмарт или чебурек в ЧебурекМи, которые находятся рядом - на Карла Либкнехта 22/1")

# Обработка ответа на загадку
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    step_index = context.user_data.get('step', 0)
    if step_index >= len(quest_steps):
        return

    step = quest_steps[step_index]
    query = update.callback_query

    # Обработка подсказки
    if query and query.data == "hint":
        hint = step.get("hint", "Подсказка отсутствует.")
        await query.message.reply_text(f"💡 Подсказка: {hint}")
        return

    # Проверка текстового ответа
    user_answer = update.message.text.strip().lower()
    correct_answer = step["correct_answer"].lower()

    if user_answer == correct_answer:
        await update.message.reply_text("✅ Отлично! Ваш ответ верен. Продолжайте в том же духе и переходите к следующему этапу! ✅")
        context.user_data['step'] += 1
        await send_step(update, context)
    else:
        await update.message.reply_text("❌ Упс! Кажется, этот ответ неверен. Попробуйте еще раз! ❌")

# Основная функция
def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("Начать квест"), handle_quest_start))
    application.add_handler(CallbackQueryHandler(handle_response))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()