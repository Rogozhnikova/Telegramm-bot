import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, LabeledPrice
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
BOT_TOKEN = "8098378802:AAGfRVTtIkt5r0nNnfrxTjxt5Aeo65tTzKo"
# Токен провайдера из ЮKassa
PAYMENT_PROVIDER_TOKEN = "YOUR_PAYMENT_PROVIDER_TOKEN"

# Список шагов квеста с координатами
quest_steps = [
    {
        "description": "Ну что, готов погулять?\n",
        "question": "Для кого-то паспорт просто документ, но для него - дубликат бесценного груза",
        "options": ["парк Энгельса", "Парк Маяковского"],
        "correct": 1,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.81725294217953, "longitude": 60.63811311028618},  # Парк Маяковского 1
        "radius": 250,  # Радиус в метрах 
    },
    {
        "description": "Отлично) Погуляем по парку? Погода такая хорошая",
        "question": "Иди прямо от входа, вдоль широкой аллеи, что ты увидишь?",
        "options": ["Ларьки с едой", "Аттракционы", "Фонтан"],
        "correct": 2,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.814653571759216, "longitude": 60.639271652060046},  # фонтан 2
        "radius": 150,
    },
    {
        "description": "Теперь найди детскую площадку, рядом с ней в лес идет тропинка. Иди по ней",
        "question": "Пришел?",
        "options": ["Да", "Нет"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.816177960357756, "longitude": 60.63191510363299},  # клевер парк 3
        "radius": 150,
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
        await update.message.reply_text("🎉 Добро пожаловать! Вы уже имеете доступ к квесту.")
        context.user_data['step'] = 0
        await send_step(update, context)
    else:
        await update.message.reply_text(
            "Добро пожаловать в бот-квест! 🎉\n"
            "Чтобы получить доступ к квесту, купите премиум-доступ через /buy."
        )

# Команда /buy для старта покупки
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    title = "Премиум-доступ"
    description = "Получите доступ к квесту!"
    payload = "Custom-Payload"
    currency = "RUB"
    price = 500  # Цена в рублях

    await context.bot.send_invoice(
        chat_id,
        title,
        description,
        payload,
        PAYMENT_PROVIDER_TOKEN,
        currency,
        [LabeledPrice("Премиум-доступ", price)]
    )

# Обработка предварительного запроса на платёж
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    await query.answer(ok=True)

# Обработка успешной оплаты
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text("🎉 Спасибо за покупку! Теперь у вас есть доступ к квесту.")
    mark_user_as_premium(user_id)  # Сохраняем статус в базе данных

# Отправка текущего шага
async def send_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    step_index = context.user_data.get('step', 0)
    if step_index < len(quest_steps):
        step = quest_steps[step_index]
        reply_markup = create_keyboard(step["options"])
        
        # Если это callback-запрос, используем query.message для отправки сообщения
        if update.callback_query:
            message = update.callback_query.message
            await message.reply_text(
                f"{step['description']}\n\n{step['question']}",
                reply_markup=reply_markup
            )
        else:
            # Если это команда /start, используем update.message
            await update.message.reply_text(
                f"{step['description']}\n\n{step['question']}",
                reply_markup=reply_markup
            )
    else:
        # Если все шаги завершены
        if update.callback_query:
            await update.callback_query.message.reply_text("🎉 Поздравляем! Вы завершили квест! 🎉")
        else:
            await update.message.reply_text("🎉 Поздравляем! Вы завершили квест! 🎉")

# Обработка ответа на загадку
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    step_index = context.user_data.get('step', 0)
    if step_index < len(quest_steps):
        step = quest_steps[step_index]
        selected_option = query.data

        # Проверяем, была ли нажата кнопка "Пропустить"
        if selected_option == "skip":
            await query.message.reply_text("➡️ Точка пропущена. Переходим к следующей!")
            context.user_data['step'] += 1  # Переходим к следующему шагу
            await send_step(update, context)
            return

        # Преобразуем выбранный вариант в число (если это не "skip")
        selected_option = int(selected_option)

        if "all_correct" in step and step["all_correct"]:
            # Все ответы правильные
            await query.message.reply_text("✅ Отлично! Теперь подтверди своё местоположение.")
        else:
            if selected_option == step["correct"]:
                # Правильный ответ
                await asyncio.sleep(1)
                await query.message.reply_text("✅ Правильно! Теперь подтверди своё местоположение.")
            else:
                # Неправильный ответ
                await asyncio.sleep(1)
                await query.message.reply_text("Ты меня не проведешь, хуй на ландыш не похож 😜")
                return  # Не переходим к следующему шагу

        # Создаем клавиатуру для отправки геолокации
        location_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("Подтвердить местоположение", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await query.message.reply_text(
            "Нажми кнопку ниже, чтобы подтвердить, что ты на месте:",
            reply_markup=location_keyboard
        )
    else:
        # Все шаги завершены
        await query.message.reply_text("🎉 Поздравляем! Вы завершили квест! 🎉")

# Обработка геолокации
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_location = update.message.location
    step_index = context.user_data.get('step', 0)
    
    if step_index < len(quest_steps):
        step = quest_steps[step_index]
        target_location = step["coordinates"]
        radius = step["radius"]

        # Вычисляем расстояние между точками (в метрах)
        distance = calculate_distance(
            user_location.latitude, user_location.longitude,
            target_location["latitude"], target_location["longitude"]
        )

        if distance <= radius:
            # Пользователь в нужной точке
            await update.message.reply_text("✅ Вы на месте! Переходим к следующему шагу...")
            context.user_data['step'] += 1
            await send_step(update, context)
        else:
            # Пользователь далеко от цели
            await update.message.reply_text(f"❌ Вы ещё не на месте. Подойди ближе! (До цели {distance:.0f} метров)")
    else:
        # Все шаги завершены
        await update.message.reply_text("🎉 Поздравляю! Вы завершили квест! 🎉")

# Вычисление расстояния между двумя точками (в метрах)
def calculate_distance(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2

    # Преобразуем координаты в радианы
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Формула гаверсинусов
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371000 * c  # Расстояние в метрах
    return distance

# Основная функция
def main() -> None:
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
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_handler(CallbackQueryHandler(handle_response))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Бот остановлен.")