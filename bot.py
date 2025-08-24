from flask import Flask

# Добавь в начало файла
app = Flask(__name__)

@app.route('/')
def home():
    return "Трейд-бот работает! 🔥"
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import DAY_DATA, TERMS, TIMEZONE
from database import init_db, get_user, create_user, update_user_day, add_completed_lesson, get_all_users, get_user_progress

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
init_db()

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Клавиатуры
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📖 Теория", callback_data="theory"),
         InlineKeyboardButton("📊 Прогресс", callback_data="progress")],
        [InlineKeyboardButton("🖼️ Примеры", callback_data="examples"),
         InlineKeyboardButton("📚 Термины", callback_data="terms")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def lesson_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Всё понял! 💪", callback_data="start_quiz")]])

def quiz_keyboard(options):
    keyboard = []
    for option in options:
        keyboard.append([InlineKeyboardButton(option, callback_data=f"answer_{option[0]}")])
    return InlineKeyboardMarkup(keyboard)

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user(user.id)
    
    if not user_data:
        create_user(user.id, user.username)
        await update.message.reply_text(
            f"Привет, {user.first_name}! 🚀\n"
            "Я твой трейд-наставник. Каждый день в 19:00 МСК присылаю новый урок.\n"
            "Используй меню для навигации:",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            f"С возвращением, {user.first_name}! Ты на дне {user_data['current_day']}. Продолжаем! 🎯",
            reply_markup=main_menu_keyboard()
        )

async def day_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user(user.id)
    
    if not user_data:
        await update.message.reply_text("Сначала напиши /start")
        return
    
    day = user_data['current_day']
    if day > len(DAY_DATA):
        await update.message.reply_text("Ты прошёл все дни! Курс завершён! 🎉")
        return
    
    lesson = DAY_DATA[day]
    message = f"День {day}. {lesson['topic']}\n\n{lesson['theory']}"
    
    if lesson.get('image_url'):
        await update.message.reply_photo(lesson['image_url'], caption=message, reply_markup=lesson_keyboard())
    else:
        await update.message.reply_text(message, reply_markup=lesson_keyboard())

# Обработчики кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_data = get_user(user.id)
    day = user_data['current_day'] if user_data else 1
    
    data = query.data
    
    if data == 'start_quiz':
        quiz = DAY_DATA[day]['quiz']
        question = f"🎯 Вопрос дня {day}:\n{quiz['question']}\n\n" + "\n".join(quiz['options'])
        await query.edit_message_text(question, reply_markup=quiz_keyboard(quiz['options']))
    
    elif data.startswith('answer_'):
        selected = data.split('_')[1]
        quiz = DAY_DATA[day]['quiz']
        
        if selected == quiz['correct_answer']:
            add_completed_lesson(user.id, day)
            update_user_day(user.id, day + 1)
            await query.edit_message_text(f"✅ Верно! {quiz['explanation']}\n\nПереходи к следующему дню! 🚀")
        else:
            await query.edit_message_text(f"❌ Неа. Попробуй ещё раз!\n\n{quiz['question']}", reply_markup=quiz_keyboard(quiz['options']))
    
    elif data == 'theory':
        theory_text = "\n\n".join([f"День {d}: {data['topic']}\n{data['theory']}" for d, data in DAY_DATA.items()])
        await query.edit_message_text(f"📖 Вся теория:\n\n{theory_text[:4000]}...")
    
    elif data == 'progress':
        progress = get_user_progress(user.id)
        if progress:
            await query.edit_message_text(
                f"📊 Твой прогресс:\n"
                f"Пройдено дней: {progress['completed']}/{progress['total']}\n"
                f"Текущий день: {progress['current_day']}\n"
                f"Осталось: {progress['total'] - progress['completed']} дней"
            )
        else:
            await query.edit_message_text("Напиши /start чтобы начать обучение")
    
    elif data == 'examples':
        examples = "\n".join([f"День {d}: {data['topic']}" for d, data in DAY_DATA.items() if data.get('image_url')])
        await query.edit_message_text(f"🖼️ Примеры:\n\n{examples}\n\nИспользуй /day чтобы посмотреть примеры")
    
    elif data == 'terms':
        terms_text = "\n\n".join([f"• {term}: {desc}" for term, desc in TERMS.items()])
        await query.edit_message_text(f"📚 Термины:\n\n{terms_text[:4000]}...")
    
    elif data == 'help':
        help_text = (
            "❓ Помощь:\n"
            "/start - начать обучение\n"
            "/day - текущий урок\n"
            "Меню:\n"
            "📖 Теория - вся теория курса\n"
            "📊 Прогресс - твои результаты\n"
            "🖼️ Примеры - примеры графиков\n"
            "📚 Термины - словарь терминов"
        )
        await query.edit_message_text(help_text)

# Напоминалки
async def send_daily_lessons(context: ContextTypes.DEFAULT_TYPE):
    try:
        users = get_all_users()
        for user_id, current_day in users:
            if current_day <= len(DAY_DATA):
                lesson = DAY_DATA[current_day]
                message = f"📅 День {current_day}. {lesson['topic']}\n\n{lesson['theory']}"
                
                try:
                    if lesson.get('image_url'):
                        await context.bot.send_photo(user_id, lesson['image_url'], caption=message, reply_markup=lesson_keyboard())
                    else:
                        await context.bot.send_message(user_id, message, reply_markup=lesson_keyboard())
                except Exception as e:
                    logger.error(f"Ошибка отправки пользователю {user_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка в send_daily_lessons: {e}")

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    try:
        users = get_all_users()
        for user_id, current_day in users:
            if current_day <= len(DAY_DATA):
                try:
                    await context.bot.send_message(
                        user_id,
                        f"👋 Не пропускай обучение! День {current_day} ждёт тебя!\n"
                        f"Используй /day чтобы начать урок 🚀",
                        reply_markup=main_menu_keyboard()
                    )
                except Exception as e:
                    logger.error(f"Ошибка напоминания пользователю {user_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка в send_reminders: {e}")

# Запуск бота
def main():
    if not BOT_TOKEN:
        logger.error("Не задан BOT_TOKEN! Проверь переменные окружения.")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("day", day_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Настраиваем планировщик
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(send_daily_lessons, CronTrigger(hour=19, minute=0), args=[application])  # 19:00 МСК
    scheduler.add_job(send_reminders, CronTrigger(hour=21, minute=0), args=[application])      # 21:00 МСК
    scheduler.start()
    
    # Запускаем бота
    logger.info("Бот запущен! 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    # Для локального запуска
    from threading import Thread
    Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000}).start()
    main()
