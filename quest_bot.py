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
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
    {
        "description": "У нас недавно построили новую арену, оценишь?",
        "question": "Жду твоей оценки",
        "options": ["Классно", "Ну пойдет", "Могли сделать куда лучше"],
        "all_correct": True,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.82536932398083, "longitude": 60.6089099514688},  # арена 4
        "radius": 300,
    },
    {
        "description": "Ты молодец, идем дальше",
        "question": "Помнишь, как по Пьяне ты оскорбил культуру, где это было?",
        "options": ["Аллея Культуры", "Плотинка", "Зеленая роща"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.8279239568393, "longitude": 60.606024383620074},  # аллея культуры 5
        "radius": 200,
    },
    {
        "description": "Теперь иди по набережной. Ты найдешь некую площадь. Как она называется?",
        "question": "Нажимай на кнопку, когда будешь на месте",
        "options": ["Площадь труда", "Парк Турбомоторного завода", "Сад центра современного искусства"],
        "correct": 2,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.83052850713148, "longitude": 60.60522957388492},  # сад 6
        "radius": 250,
    },
    {
        "description": "Двигайся туда, где собраны множество растений, этот парк - оазис для любителей природы и уток",
        "question": "Что за парк?",
        "options": ["Дендропарк", "Зеленая роща", "Шувакишский лесопарк"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.8298411621838, "longitude": 60.60321206494298},  # дендропарк 7
        "radius": 300,
    },
    {
        "description": "В названии какого парка есть римские цифры X и I?",
        "question": "Ищи Памятник ликвидаторам ядерных катастроф",
        "options": ["Я на месте"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.83895002771718, "longitude": 60.57757973425552},  # дворец молодежи 8
        "radius": 300,
    },
    {
        "description": "Воспоминания из прошлого, что за место?",
        "question": "Там были морские бои, многих пытался там утопить, а после наслаждался травой",
        "options": ["Фонтан в дендропарке","Фонтан на Октябрьской площади(театр драмы)","Пруд в Харитоновском парке"],
        "correct": 1,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.84305256141213, "longitude": 60.59566955665332},  # драма 9
        "radius": 250,
    },
    {
        "description": "Вопрос по-сложнее",
        "question": "Где ты отдыхал в компании без лишних и А2",
        "options": ["Около Драм театра", "Возле храма на крови", "Плотинка"],
        "correct": 2,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.83640928155525, "longitude": 60.603043725537916},  # плотинка 10
        "radius": 100,
    },
    {
        "description": "Вспомни, где ты аплодировал Годзилле?",
        "question": "Нажимай на кнопку, когда будешь на месте",
        "options": ["Салют", "Гринвич", "Дом Кино"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.83830678810221, "longitude": 60.60981671700091},  # салют 11
        "radius": 250,
    },
    {
        "description": "Помнишь место, где ты познакомился с Юлей?",
        "question": "Нажимай на кнопку, когда будешь на месте",
        "options": ["Я на месте"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.839636118131665, "longitude": 60.609439723520865},  # работа 12
        "radius": 150,
    },
    {
        "description": "Иди туда, где тебе больше всего нравится Симпл",
        "question": "Нажимай на кнопку, когда будешь на месте",
        "options": ["ТЮЗ", "Филармония", "Оперный театр"],
        "correct": 2,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.83931101728423, "longitude": 60.615465468757094},  # оперный театр 13
        "radius": 250,
    },
    {
        "description": "Следующий парк назван в честь великого ученого. Который, кстати, дружил с Карлом Марксом",
        "question": "Как называется парк?",
        "options": ["Парк Блюхера", "Парк Энгельса", "Парк Чкалова"],
        "correct": 1,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.836355625113484, "longitude":  60.62604560809884},  # Энгельса 14
        "radius": 300,
    },
    {
        "description": "Взбирайся на самую высокую точку в городе и насладись потрясающим видом",
        "question": "Там получишь следующую точку",
        "options": ["Я на месте", "Не пойду"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.82706540885552, "longitude": 60.63350818626051},  # метеогорка 15
        "radius": 250,
    },
    {
        "description": "Следующий вопрос - цитата, тебе нужно понять, о каком месте идет речь",
        "question": "Сан Саныча не забудь, он то тебя помнит",
        "options": ["Я на месте", "Не пойду"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.82567542511831, "longitude": 60.62550118762154},  # галерка 16
        "radius": 150,
    },
    {
        "description": "Знаешь какую-нибудь кофейню тут с приятной атмосферой и интересными напитками?",
        "question": "Заходить не обязательно",
        "options": ["Я на месте", "Не пойду"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.82613205504469, "longitude": 60.62471978505706},  # Вереск 17
        "radius": 150,
    },
    {
        "description": "А как насчет заданий? Найди турники и покажи, что умеешь)",
        "question": "Сделал?",
        "options": ["Да", "Нет"],
        "correct": 0,
        "location_hint": "https://maps.app.goo.gl/your_location_link",
        "coordinates": {"latitude": 56.82584260801992, "longitude": 60.61945054483495},  # турники 19
        "radius": 200,
    },
    # Добавьте больше шагов...
]

# Функция для создания клавиатуры с кнопкой "Пропустить"
def create_keyboard(options):
    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(i))] for i, option in enumerate(options)
    ]
    # Добавляем кнопку "Пропустить"
    keyboard.append([InlineKeyboardButton("Пропустить ⏭️", callback_data="skip")])
    return InlineKeyboardMarkup(keyboard)

# Приветственное сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['step'] = 0  # Инициализация первого шага
    await update.message.reply_text(
        "Добро пожаловать в бот-квест! 🎉\n"
        "Немного о квесте:\n"
        "После ответа тебе надо предоставить свои координаты, чтобы получить следующую точку\n"
        "Используй кнопки ниже, чтобы начать."
    )
    await asyncio.sleep(1)
    await send_step(update, context)

# Отправка текущего шага
async def send_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await asyncio.sleep(1)
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
        await query.message.reply_text("🎉 Поздравляем! Ты завершил квест! 🎉")

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
    application = ApplicationBuilder().token("8098378802:AAGFwNfTKeg73gySuQYMVRbhd0xBgyOs1yA").build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_response))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))  # Обработка геолокации

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Бот остановлен.")