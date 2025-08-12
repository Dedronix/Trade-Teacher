import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

TOKEN = "8203536729:AAFjilpb7lvqS6P6_ltoN73-XQpgvcjzLXQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

USER_ID_FILE = 'user_id.txt'

# --- Функции для сохранения/загрузки user_id ---
def save_user_id(user_id):
    with open(USER_ID_FILE, 'w') as f:
        f.write(str(user_id))

def load_user_id():
    try:
        with open(USER_ID_FILE, 'r') as f:
            return int(f.read())
    except:
        return None

USER_ID = load_user_id()

# --- Клавиатура ---
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('📖 Теория'))
keyboard.add(KeyboardButton('📊 Пример'))
keyboard.add(KeyboardButton('✅ Отправить результат'))
keyboard.add(KeyboardButton('Старт'))

# --- Флаг ответа ---
user_responded = False

# --- Отправка задания ---
async def send_task():
    global user_responded
    user_responded = False
    if USER_ID:
        await bot.send_message(
            USER_ID,
            "Йо, трейдер 📈, пора выполнить задание по BTC на Bybit.\n"
            "Сегодня разбираем уровень поддержки на 1h графике.\n"
            "Найди его, сделай скрин и пришли сюда.\n"
            "📖 Нажми «Теория» или 📊 «Пример» для подсказки.",
            reply_markup=keyboard
        )
    else:
        print("USER_ID не задан!")

# --- Цикл напоминаний ---
async def remind_loop():
    global user_responded
    while True:
        now = datetime.now()
        target_time = now.replace(hour=20, minute=0, second=0, microsecond=0)

        # Если время уже прошло сегодня — ждём завтра
        if now >= target_time:
            target_time += timedelta(days=1)

        # Ждём до 20:00
        await asyncio.sleep((target_time - now).total_seconds())

        # Отправляем задание
        await send_task()

        # Напоминания до полуночи каждые 30 минут
        while True:
            if user_responded:
                break
            now = datetime.now()
            if now.hour == 23 and now.minute >= 59:
                break
            await asyncio.sleep(1800)
            if not user_responded and USER_ID:
                await bot.send_message(USER_ID, "Эй, брат, рынок не ждёт. Сделал задание? 📉📈")

# --- Старт: /start и кнопка "Старт" ---
@dp.message(F.text.in_({"/start", "Старт", "старт"}))
async def start_handler(message: Message):
    global USER_ID
    USER_ID = message.from_user.id
    save_user_id(USER_ID)
    await message.answer(
        "Привет, начинающий трейдер! 🚀\n"
        "Бот запущен и готов напоминать тебе о заданиях.\n"
        "Жди в 20:00 первое задание!",
        reply_markup=keyboard
    )

# --- Кнопка "📖 Теория" ---
@dp.message(F.text == "📖 Теория")
async def theory(message: Message):
    await message.answer(
        "Уровень поддержки — это ценовая зона, где спрос превышает предложение, и цена перестаёт падать.\n"
        "На графике выглядит как горизонтальная линия по минимумам свечей, где был отскок.\n"
        "Чем больше раз цена отталкивалась от этого уровня, тем он сильнее."
    )

# --- Кнопка "📊 Пример" ---
@dp.message(F.text == "📊 Пример")
async def example(message: Message):
    await message.answer(
        "Представь, что график BTC падает, но дважды дотрагивается до одной линии и отскакивает вверх — вот это и есть уровень поддержки."
    )

# --- Кнопка "✅ Отправить результат" ---
@dp.message(F.text == "✅ Отправить результат")
async def send_result(message: Message):
    await message.answer("Жду твой скрин прямо здесь! 📤")

# --- Любое сообщение ---
@dp.message()
async def handle_any(message: Message):
    global user_responded
    if message.from_user.id == USER_ID:
        if not user_responded:
            user_responded = True
            await message.answer("Отлично, бро! Задание за сегодня засчитано. Завтра будет новое 🔥")
        else:
            await message.answer("Ты уже ответил сегодня, жди следующего задания.")
    else:
        await message.answer("Я работаю только с хозяином этого бота.")

# --- Запуск ---
async def main():
    asyncio.create_task(remind_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
