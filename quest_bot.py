import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, LabeledPrice, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    PreCheckoutQueryHandler,
)
import asyncio
import sqlite3

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота
BOT_TOKEN = "8098378802:AAEqgOriNJlb6wfv91FMtYI1IwAa1bIteus"
# Токен провайдера из ЮKassa
PAYMENT_PROVIDER_TOKEN = "381764678:TEST:119468"

# Список шагов квеста с координатами
quest_steps = [
    {
        "description": "Привет, я очень рад, что ты решил погулять вместе со мной.",
        "question": "Первая точка - памятник изобретателю радио. В каком году он установлен?",
        "answer_type": "text",  # Тип ответа: текст
        "correct_answer": "1975",  # Правильный ответ (в нижнем регистре)
    },
    {
        "description": "Теперь в конце аллеи найди здание с двумя флагами и прочти черную табличку на нем",
        "question": "Кто останавливался там на пути из Сибири?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "декабристы",
    },
    {
        "description": "Развернись на 180. Снова здание, иди к нему",
        "question": "Сколько этажей это здание?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "10",
    },
    {
        "description": "Слева на соседнем здании будет рисунок",
        "question": "Что изображено под числом 24?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "алмазные палки",
    },
    {
        "description": "Иди прямо и найди граффити Мы станем лучше",
        "question": "Какое число есть рядом с надписью на этой же стане?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "180",
    },
    {
        "description": "Идем дальше по улице. По пути будет историческое здание",
        "question": "Кто жил в этом доме?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "мамин-сибиряк",
    },
    {
        "description": "Чуть дальше будят памятник Пушнику",
        "question": "Что написано внизу?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "велению божию, о муза, будь послушна",
    },
    {
        "description": "Не будем уходить далеко. Иди по улице Первомайская до улицы Царская",
        "question": "Ты найдешь афишу. В ней есть название квартила. Напиши его",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "литературный",
    },
    {
        "description": "Если стоять лицом к афише, то слева будет еще одно памятное место. Иди к нему",
        "question": "Какая фамилия написана там?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "егоров",
    },
    {
        "description": "На перекрестке направо. Дорогу не переходи и иди прямо",
        "question": "Вывеска какого бара видна?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "янки",
    },
    {
        "description": "На другой стороне дороги будет объект культорного наследия",
        "question": "Чей дом? Только фамилию",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "селивановой",
    },
    {
        "description": "Иди дальше в сторону проспекта Ленина. Видишь граффити с мистическими существами?",
        "question": "Какого цвета то существо, которое имеет всего две ноги?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "белое",
    },
    {
        "description": "Иди дальше. Ты встретишь много котиков.",
        "question": "Они двух цветов. Но какого цвета больше?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "красный",
    },
    {
        "description": "Знаешь, где находиться академия музыкальной комедии?",
        "question": "Какого цвета кружки на дверях?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "желтый",
    },
    {
        "description": "Квест подходит к концу и тебя ждет сложный вопрос",
        "question": "Готов?",
        "answer_type": "options",  # Тип ответа: варианты
        "options": ["Да", "Нет"],
        "correct": 0,
    },
    {
        "description": "Выбирай, кофе или чебурек?",
        "question": "",
        "answer_type": "options",  # Тип ответа: варианты
        "options": ["Кофе", "Чебурек"],
        "all_correct": True,
    },
]

# Функция для создания клавиатуры с кнопкой "Пропустить"
def create_keyboard(options):
    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(i))] for i, option in enumerate(options)
    ]
    # Добавляем кнопку "Пропустить"
    keyboard.append([InlineKeyboardButton("Пропустить ⏭️", callback_data="skip")])
    return InlineKeyboardMarkup(keyboard)

# Сохранение статуса пользователя в базе данных
def mark_user_as_premium(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, is_premium) VALUES (?, 1)", (user_id,))
    conn.commit()
    conn.close()

# Проверка статуса пользователя
def is_user_premium(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_premium FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else False

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_premium(user_id):
        await update.message.reply_text(
            "🎉 Добро пожаловать! Вы уже имеете доступ к квесту.",
            reply_markup=create_main_keyboard()  # Отправляем клавиатуру
        )
        context.user_data['step'] = 0
        await send_step(update, context)
    else:
        await update.message.reply_text(
            "Добро пожаловать в бот-квест! 🎉\n"
            "Чтобы получить доступ к квесту, нажмите кнопку 'Купить' ниже.",
            reply_markup=create_main_keyboard()  # Отправляем клавиатуру
        )
def create_main_keyboard():
    keyboard = [["Купить доступ 🎟️"]]  # Кнопка "Купить доступ"
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Обработка нажатия на кнопку "Купить доступ"
async def handle_buy_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await buy(update, context)  # Вызываем функцию buy для отправки счета

# Команда /buy для старта покупки
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    title = "Премиум-доступ"
    description = "Получите доступ к квесту!"
    payload = "Custom-Payload"
    currency = "RUB"
    price = 100  # Цена в рублях

    try:
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency=currency,
            prices=[LabeledPrice("Премиум-доступ", 10000)],  # Цена в копейках
            start_parameter="test",  # Уникальный параметр для глубокой ссылки
            need_name=True,  # Запрашивать имя пользователя (опционально)
            need_phone_number=True,  # Запрашивать номер телефона (опционально)
            need_email=True  # Запрашивать email (опционально)
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке инвойса: {e}")
        await update.message.reply_text("Произошла ошибка при отправке платёжного запроса. Пожалуйста, попробуйте позже.")

# Обработка предварительного запроса на платёж
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    await query.answer(ok=True)

# Обработка успешной оплаты
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    mark_user_as_premium(user_id)  # Сохраняем статус в базе данных

    # Обновляем состояние пользователя
    context.user_data['step'] = 0

    # Уведомляем пользователя о покупке
    await update.message.reply_text("🎉 Спасибо за покупку! Теперь у вас есть доступ к квесту.")

    # Автоматически отправляем первый шаг квеста
    await send_step(update, context)

# Отправка текущего шага
async def send_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    step_index = context.user_data.get('step', 0)
    if step_index < len(quest_steps):
        step = quest_steps[step_index]
        message = f"{step['description']}\n{step['question']}"

        if step["answer_type"] == "options":
            # Если вопрос с вариантами ответа, создаем клавиатуру
            reply_markup = create_keyboard(step["options"])
        else:
            # Если вопрос с текстовым ответом, клавиатура не нужна
            reply_markup = None

        # Если это callback-запрос, используем query.message для отправки сообщения
        if update.callback_query:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
        else:
            # Если это команда /start или другой текстовый ответ
            await update.message.reply_text(message, reply_markup=reply_markup)
    else:
        # Если все шаги завершены
        if update.callback_query:
            await update.callback_query.message.reply_text("🎉 Поздравляем! Вы завершили квест! 🎉")
        else:
            await update.message.reply_text("🎉 Поздравляем! Вы завершили квест! 🎉")

# Обработка ответа на загадку
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    step_index = context.user_data.get('step', 0)
    if step_index >= len(quest_steps):
        await update.message.reply_text("🎉 Поздравляем! Вы завершили квест! 🎉")
        return

    step = quest_steps[step_index]

    if step["answer_type"] == "options":
        # Обработка ответа с вариантами
        query = update.callback_query
        await query.answer()
        selected_option = int(query.data)

        if "all_correct" in step and step["all_correct"]:
            await query.message.reply_text("✅ Все варианты правильные! Переходим к следующему шагу...")
            context.user_data['step'] += 1
            await send_step(update, context)
        elif selected_option == step["correct"]:
            await query.message.reply_text("✅ Правильно! Переходим к следующему шагу...")
            context.user_data['step'] += 1
            await send_step(update, context)
        else:
            await query.message.reply_text("❌ Неверный ответ. Попробуйте еще раз!")

    elif step["answer_type"] == "text":
        # Обработка текстового ответа
        user_answer = update.message.text.strip().lower()
        correct_answer = step["correct_answer"].lower()

        if user_answer == correct_answer:
            await update.message.reply_text("✅ Правильно! Переходим к следующему шагу...")
            context.user_data['step'] += 1
            await send_step(update, context)
        else:
            await update.message.reply_text("❌ Неверный ответ. Попробуйте еще раз!")

# Основная функция
def main() -> None:
    # Отключение webhook
    bot = Bot(token=BOT_TOKEN)
    bot.delete_webhook()
    # Создание таблицы в базе данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            is_premium BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

    # Создание приложения
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy))
    # Новый обработчик для кнопки "Купить доступ"
    application.add_handler(MessageHandler(filters.Regex("^Купить доступ 🎟️$"), handle_buy_button))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_handler(CallbackQueryHandler(handle_response))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))  # Для текстовых ответов

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Бот остановлен.")