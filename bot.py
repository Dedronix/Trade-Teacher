import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

TOKEN = '8203536729:AAFjilpb7lvqS6P6_ltoN73-XQpgvcjzLXQ'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

USER_ID_FILE = 'user_id.txt'

# Функции для сохранения и загрузки user_id
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

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('📖 Теория'))
keyboard.add(KeyboardButton('📊 Пример'))
keyboard.add(KeyboardButton('✅ Отправить результат'))

user_responded = False

async def send_task():
    global user_responded
    user_responded = False
    if USER_ID:
        await bot.send_message(USER_ID,
            "Йо, трейдер 📈, пора выполнить задание по BTC на Bybit.\n"
            "Сегодня разбираем уровень поддержки на 1h графике.\n"
            "Найди его, сделай скрин и пришли сюда.\n"
            "📖 Нажми «Теория» или 📊 «Пример» для подсказки.",
            reply_markup=keyboard)
    else:
        print("USER_ID не задан!")

async def remind_loop():
    global user_responded
    while True:
        now = datetime.now()
        target_time = now.replace(hour=20, minute=0, second=0, microsecond=0)
        if now > target_time:
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        await send_task()

        for _ in range(48):  # Проверять в течение 24 часов (каждые 30 мин)
            if user_responded:
                break
            await asyncio.sleep(1800)  # 30 минут
            if not user_responded and USER_ID:
                await bot.send_message(USER_ID, "Эй, брат, рынок не ждёт. Сделал задание? 📉📈")

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    global USER_ID
    USER_ID = message.from_user.id
    save_user_id(USER_ID)
    await message.answer("Бро, бот запущен и готов тебя долбить по крипте. Жди в 20:00 первое задание!", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == '📖 Теория')
async def theory(message: types.Message):
    await message.answer(
        "Уровень поддержки — это ценовая зона, где спрос превышает предложение, и цена перестаёт падать.\n"
        "На графике выглядит как горизонтальная линия по минимумам свечей, где был отскок.\n"
        "Чем больше раз цена отталкивалась от этого уровня, тем он сильнее.")

@dp.message_handler(lambda message: message.text == '📊 Пример')
async def example(message: types.Message):
    await message.answer(
        "Представь, что график BTC падает, но дважды дотрагивается до одной линии и отскакивает вверх — вот это и есть уровень поддержки.")

@dp.message_handler(lambda message: message.text == '✅ Отправить результат')
async def send_result(message: types.Message):
    await message.answer("Жду твой скрин прямо здесь! 📤")

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_any(message: types.Message):
    global user_responded
    if message.from_user.id == USER_ID:
        if not user_responded:
            user_responded = True
            await message.answer("Отлично, бро! Задание за сегодня засчитано. Завтра будет новое 🔥")
        else:
            await message.answer("Ты уже ответил сегодня, жди следующего задания.")
    else:
        await message.answer("Я работаю только с хозяином этого бота.")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(remind_loop())
    executor.start_polling(dp, skip_updates=True)
