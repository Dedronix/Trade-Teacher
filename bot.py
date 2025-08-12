import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = "8203536729:AAFjilpb7lvqS6P6_ltoN73-XQpgvcjzLXQ"
ADMIN_ID = 6370827372  # твой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Клавиатура ---
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📖 Теория")],
        [KeyboardButton(text="📊 Пример")],
        [KeyboardButton(text="✅ Отправить результат")],
        [KeyboardButton(text="Старт")]
    ],
    resize_keyboard=True
)

# --- Хранилище пользователей ---
users = set()

# --- Команда /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    users.add(message.from_user.id)
    await message.answer("Привет, начинающий трейдер! 🚀", reply_markup=keyboard)

# --- Кнопка "Старт" ---
@dp.message(lambda msg: msg.text.lower() == "старт")
async def btn_start(message: types.Message):
    users.add(message.from_user.id)
    await message.answer("Привет, начинающий трейдер! 🚀", reply_markup=keyboard)

# --- Фоновая задача напоминаний ---
async def remind_loop():
    while True:
        now = datetime.now()
        first_reminder = now.replace(hour=20, minute=0, second=0, microsecond=0)

        if now > first_reminder:
            first_reminder += timedelta(days=1)

        await asyncio.sleep((first_reminder - now).total_seconds())

        while datetime.now().hour >= 20:
            for uid in list(users):
                try:
                    await bot.send_message(uid, "⏰ Пора делать задание!")
                except Exception as e:
                    print(f"Ошибка отправки {uid}: {e}")
            await asyncio.sleep(1800)  # каждые 30 минут

# --- Запуск ---
async def main():
    asyncio.create_task(remind_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
