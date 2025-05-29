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
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import sqlite3

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

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
        "correct_answer": "декабрь",
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
        "correct_answer": "какие-то палки",
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
    },
    {
        "description": "Чуть дальше будет памятник Пушкину",
        "question": "Что написано внизу?",
        "answer_type": "text",  # Тип ответа: варианты
        "correct_answer": "веленью божию, о муза, будь послушна...",
        "hint": "это строчка из его стихотворения, обрати внимание на пробелы и запятые",  # Подсказка
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
    {
        "description": "Ура!\n"
        "Финальный и самый сложный вопрос",
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
def create_keyboard(options=None):
    keyboard = []
    if options:
        # Если есть варианты ответов, добавляем их в клавиатуру
        keyboard += [[InlineKeyboardButton(option, callback_data=str(i))] for i, option in enumerate(options)]
    # Добавляем кнопку "Подсказка"
    keyboard.append([InlineKeyboardButton("Подсказка ❓", callback_data="hint")])
    return InlineKeyboardMarkup(keyboard)

# Сохранение статуса пользователя в базе данных
def mark_user_as_premium(user_id, duration_hours=2.5):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Вычисляем дату окончания подписки
    premium_until = datetime.now() + timedelta(hours=duration_hours)
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, is_premium, premium_until) VALUES (?, 1, ?)",
        (user_id, premium_until.strftime("%Y-%m-%d %H:%M:%S.%f"))
    )
    conn.commit()
    conn.close()

# Проверка статуса пользователя
def is_user_premium(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_premium, premium_until FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        is_premium, premium_until = result
        logger.info(f"Данные пользователя {user_id}: is_premium={is_premium}, premium_until={premium_until}")
        if is_premium and premium_until:
            try:
                premium_until_dt = datetime.strptime(premium_until, "%Y-%m-%d %H:%M:%S.%f")
                logger.info(f"Текущее время: {datetime.now()}, Время окончания подписки: {premium_until_dt}")
                return datetime.now() < premium_until_dt
            except ValueError:
                logger.error(f"Ошибка при обработке даты для пользователя {user_id}: {premium_until}")
    return False

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Команда /start вызвана.")
    user_id = update.message.from_user.id
    if is_user_premium(user_id):
        await update.message.reply_text(
            "📌 Начни свое приключение прямо сейчас и открой для себя мир уличных квестов!\n"
            "💪 Собери своих друзей или отправляйся в путь в одиночку — главное, будь готов к новым открытиям и ярким эмоциям! 💪\n"
            "💰 Стоимость участия всего 100 рублей\n" 
            "(На одного человека)"
            "В этом квесте тебя ждут интересные задания, которые проверят твою смекалку и внимательность.\n"
            "А в конце ты получишь вкусный подарок 🎁 ",
            reply_markup=create_main_keyboard()  # Отправляем клавиатуру
        )
        context.user_data['step'] = 0
        await send_step(update, context)
    else:
        await update.message.reply_text(
            "😔 Ваш доступ к квесту истек. Чтобы получить доступ снова, нажмите кнопку '🔒Активировать доступ? 🔒' ниже.",
            reply_markup=create_main_keyboard()  # Отправляем клавиатуру
        )
def create_main_keyboard():
    keyboard = [["🔒Активировать доступ? 🔒"]]  # Кнопка "Купить доступ"
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
    mark_user_as_premium(user_id, duration_hours=1.5)  # Подписка на 1,5 часа
    await update.message.reply_text("🔒 Доступ к квесту активирован! 🔓\n"
                                    "💡 Внимание! Ваш доступ к квесту ограничен по времени. У вас есть 1,5 часа, чтобы пройти все испытания и получить приз."
                                    "Используйте свое время мудро! 🕒")
    # Обновляем состояние пользователя
    context.user_data['step'] = 0
    # Отправляем первый шаг квеста
    await send_step(update, context)
    # Инициализируем состояние пользователя
    context.user_data['step'] = 0

    # Отправляем первый шаг квеста
    await send_step(update, context)

# Отправка текущего шага
async def send_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    step_index = context.user_data.get('step', 0)
    user_id = update.message.from_user.id
    if not is_user_premium(user_id):
        await update.message.reply_text(
            "😔 Ваш доступ к квесту истек. Чтобы продолжить, нажмите кнопку '🔒Активировать доступ? 🔒' ниже.",
            reply_markup=create_main_keyboard()
        )
        return
    if step_index < len(quest_steps):
        step = quest_steps[step_index]
        message = f"{step['description']}\n{step['question']}"
        if step["answer_type"] == "options":
            # Если вопрос с вариантами ответа, создаем клавиатуру
            reply_markup = create_keyboard(step["options"])
        else:
            # Если вопрос с текстовым ответом, клавиатура всё равно нужна (для "Пропустить" и "Подсказка")
            reply_markup = create_keyboard()
        if update.callback_query:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text("🎉 Поздравляем! Вы успешно завершили квест и раскрыли все его тайны. Надеемся, вам понравилось это приключение! 🎉")

# Обработка ответа на загадку
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    step_index = context.user_data.get('step', 0)
    if step_index >= len(quest_steps):
        await update.message.reply_text("🎉 Поздравляем! Вы успешно завершили квест и раскрыли все его тайны. Надеемся, вам понравилось это приключение! 🎉")
        return

    step = quest_steps[step_index]

    # Обработка callback-запросов (кнопки "Пропустить", "Подсказка" или варианты ответа)
    query = update.callback_query
    if query:
        await query.answer()
        selected_option = query.data

        # Если нажата кнопка "Подсказка"
        if selected_option == "hint":
            hint = step.get("hint", "Подсказка отсутствует.")
            await query.message.reply_text(f"💡 Подсказка: {hint}")
            return

        # Преобразуем выбранный вариант в число (если это не "skip" или "hint")
        if step["answer_type"] == "options":
            selected_option = int(selected_option)

            # Проверяем ответ для вариантов
            if "all_correct" in step and step["all_correct"]:
                await query.message.reply_text("✅ Отлично! Ваш ответ верен. Продолжайте в том же духе и переходите к следующему этапу! ✅")
                context.user_data['step'] += 1
                await send_step(update, context)
            elif selected_option == step["correct"]:
                await query.message.reply_text("✅ Отлично! Ваш ответ верен. Продолжайте в том же духе и переходите к следующему этапу! ✅")
                context.user_data['step'] += 1
                await send_step(update, context)
            else:
                await query.message.reply_text("❌ Упс! Кажется, этот ответ неверен. Попробуйте еще раз! ❌")
            return

    # Обработка текстового ответа
    elif step["answer_type"] == "text":
        user_answer = update.message.text.strip().lower()
        correct_answer = step["correct_answer"].lower()

        if user_answer == correct_answer:
            await update.message.reply_text("✅ Отлично! Ваш ответ верен. Продолжайте в том же духе и переходите к следующему этапу! ✅")
            context.user_data['step'] += 1
            await send_step(update, context)
        else:
            await update.message.reply_text("❌ Упс! Кажется, этот ответ неверен. Попробуйте еще раз! ❌")

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Произошла ошибка: %s", context.error)

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📌 Начни свое приключение прямо сейчас и открой для себя мир уличных квестов!\n"
            "💪 Собери своих друзей или отправляйся в путь в одиночку — главное, будь готов к новым открытиям и ярким эмоциям! 💪\n"
            "💰 Стоимость участия всего 100 рублей\n" 
            "(На одного человека)"
            "В этом квесте тебя ждут интересные задания, которые проверят твою смекалку и внимательность.\n"
            "А в конце ты получишь вкусный подарок 🎁 ",
        reply_markup=create_main_keyboard()
    )

# Основная функция
def main() -> None:
    # Отключение webhook
    bot = Bot(token=BOT_TOKEN)
    bot.delete_webhook()
    logger.info("Webhook успешно удален.")
     # Создание таблицы в базе данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Удаляем старую таблицу (если она существует)
    cursor.execute("DROP TABLE IF EXISTS users")

    # Создаем новую таблицу с обновленной структурой
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            is_premium BOOLEAN DEFAULT 0,
            premium_until TIMESTAMP,
            balance INTEGER DEFAULT 0
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
    application.add_handler(MessageHandler(filters.Regex("🔒Активировать доступ? 🔒"), handle_buy_button))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_handler(CallbackQueryHandler(handle_response))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))  # Для текстовых ответов
    application.add_handler(CommandHandler("welcome", welcome))
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Бот остановлен.")