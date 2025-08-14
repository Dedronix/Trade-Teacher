import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, BotCommand,
    InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
)
import aiosqlite

# ---------- CONFIG ----------
MSK_TZ = ZoneInfo("Europe/Moscow")
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or "PUT_YOUR_TOKEN_HERE"

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "content"
DB_PATH = BASE_DIR / "bot.db"

# Напоминания: каждые 30 минут с 19:00 до 23:59 по МСК
REM_START = time(19, 0)
REM_END = time(23, 59)
REM_DELTA = timedelta(minutes=30)

# ---------- CONTENT ----------
@dataclass
class Lesson:
    day: int
    title: str
    theory: str
    task: str
    images: list[str]
    examples: list[str]
    quiz_question: str
    quiz_options: list[str]  # ["A) ...", "B) ...", ...]
    quiz_correct: str        # "A"/"B"/"C"/"D"

def load_lesson(day: int) -> Lesson:
    fp = DATA_DIR / f"day{day:02d}.json"
    if not fp.exists():
        return Lesson(
            day=day,
            title=f"День {day}: Заглушка",
            theory="Теория появится завтра 🔧",
            task="Пока просто напиши /progress.",
            images=[],
            examples=[],
            quiz_question="Заглушка-квиз: выбери A",
            quiz_options=["A) A", "B) B", "C) C", "D) D"],
            quiz_correct="A"
        )
    with open(fp, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return Lesson(
        day=day,
        title=raw["title"],
        theory=raw["theory"],
        task=raw["task"],
        images=raw.get("images", []),
        examples=raw.get("examples", []),
        quiz_question=raw["quiz"]["question"],
        quiz_options=raw["quiz"]["options"],
        quiz_correct=raw["quiz"]["correct"],
    )

# ---------- DB ----------
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    current_day INTEGER NOT NULL DEFAULT 1,
    last_started TEXT,        -- YYYY-MM-DD по МСК
    last_answered TEXT,
    last_reminder_ts TEXT     -- ISO по МСК
);

CREATE TABLE IF NOT EXISTS day_status (
    user_id INTEGER NOT NULL,
    ymd TEXT NOT NULL,        -- YYYY-MM-DD по МСК
    started INTEGER NOT NULL DEFAULT 0,
    answered INTEGER NOT NULL DEFAULT 0,
    missed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, ymd)
);
"""

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()

async def upsert_user(db, user_id: int):
    await db.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (user_id,))

async def set_last_reminder(db, user_id: int, when_iso: str):
    await db.execute("UPDATE users SET last_reminder_ts=? WHERE user_id=?", (when_iso, user_id))

async def get_user_row(db, user_id: int):
    cur = await db.execute(
        "SELECT user_id, current_day, last_started, last_answered, last_reminder_ts FROM users WHERE user_id=?",
        (user_id,))
    return await cur.fetchone()

async def set_started_today(db, user_id: int, ymd: str):
    await db.execute(
        "INSERT INTO day_status(user_id, ymd, started) VALUES (?, ?, 1) "
        "ON CONFLICT(user_id, ymd) DO UPDATE SET started=1",
        (user_id, ymd)
    )
    await db.execute("UPDATE users SET last_started=? WHERE user_id=?", (ymd, user_id))

async def set_answered_today(db, user_id: int, ymd: str):
    await db.execute(
        "INSERT INTO day_status(user_id, ymd, answered) VALUES (?, ?, 1) "
        "ON CONFLICT(user_id, ymd) DO UPDATE SET answered=1",
        (user_id, ymd)
    )
    await db.execute("UPDATE users SET last_answered=? WHERE user_id=?", (ymd, user_id))

async def mark_missed(db, user_id: int, ymd: str):
    await db.execute(
        "INSERT INTO day_status(user_id, ymd, missed) VALUES (?, ?, 1) "
        "ON CONFLICT(user_id, ymd) DO UPDATE SET missed=1",
        (user_id, ymd)
    )

async def inc_day_if_completed(db, user_id: int):
    # Продвигаем день только если сегодня answered=1
    today = datetime.now(MSK_TZ).date().isoformat()
    cur = await db.execute(
        "SELECT answered FROM day_status WHERE user_id=? AND ymd=?", (user_id, today))
    row = await cur.fetchone()
    if row and row[0] == 1:
        await db.execute(
            "UPDATE users SET current_day = MIN(current_day + 1, 30) WHERE user_id=?", (user_id,))

async def get_day_status(db, user_id: int, ymd: str):
    cur = await db.execute(
        "SELECT started, answered, missed FROM day_status WHERE user_id=? AND ymd=?",
        (user_id, ymd))
    row = await cur.fetchone()
    return row or (0, 0, 0)

# ---------- BOT ----------
bot = Bot(TOKEN)
dp = Dispatcher()

MAIN_MENU: list[BotCommand] = [
    BotCommand(command="start", description="Запуск"),
    BotCommand(command="begin", description="Начать учёбу"),
    BotCommand(command="terms", description="Термины"),
    BotCommand(command="examples", description="Примеры"),
    BotCommand(command="progress", description="Прогресс"),
    BotCommand(command="help", description="Помощь"),
]

def kb_lesson(day: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Теория", callback_data=f"theory:{day}")],
        [InlineKeyboardButton(text="📊 Примеры", callback_data=f"examples:{day}")],
        [InlineKeyboardButton(text="📝 Пройти квиз", callback_data=f"quiz:{day}")],
    ])

def kb_quiz(day: int, options: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for opt in options:
        # ожидаем формат "A) Текст", "B) ...", ...
        letter = opt.split(")")[0].strip()
        rows.append([InlineKeyboardButton(text=opt, callback_data=f"ans:{day}:{letter}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- HANDLERS ----------
@dp.message(Command("start"))
async def cmd_start(m: Message):
    await db_init()
    async with aiosqlite.connect(DB_PATH) as db:
        await upsert_user(db, m.from_user.id)
        await db.commit()
    await bot.set_my_commands(MAIN_MENU)
    await m.answer(
        "Йо, трейдер! 👋 30 дней на Bybit, дружеский режим.\n"
        "С 19:00 (МСК) пингану и буду дёргать до 23:59, пока не нажмёшь /begin.\n"
        "Команды: /begin /terms /examples /progress /help"
    )

@dp.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer(
        "Как работаем:\n"
        "• 19:00–23:59 МСК — напоминалки раз в 30 мин до /begin.\n"
        "• /begin даст урок: теория, примеры, квиз.\n"
        "• День засчитывается только при верном ответе в квизе.\n"
        "• Пропустил до 23:59 — день помечаем как пропуск, завтра догоняем."
    )

@dp.message(Command("progress"))
async def cmd_progress(m: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        row = await get_user_row(db, m.from_user.id)
        if not row:
            await m.answer("Нажми /start, чтобы зарегистрироваться.")
            return
        _, current_day, last_started, last_answered, _ = row
        cur = await db.execute(
            "SELECT COUNT(*) FROM day_status WHERE user_id=? AND missed=1", (m.from_user.id,))
        missed_total = (await cur.fetchone())[0]
    await m.answer(
        f"Текущий день: {current_day}\n"
        f"Последний старт: {last_started or '—'}\n"
        f"Последний верный ответ: {last_answered or '—'}\n"
        f"Пропусков всего: {missed_total}"
    )

@dp.message(Command("terms"))
async def cmd_terms(m: Message):
    text = (
        "Мини-глоссарий:\n"
        "• Spot — покупка/продажа монет без плеча.\n"
        "• Futures — контракты с плечом (риск выше).\n"
        "• Market ордер — исполнение по рынку.\n"
        "• Limit ордер — заявка по твоей цене.\n"
        "• SL/TP — стоп-лосс и тейк-профит.\n"
        "• SMA — простая скользящая средняя.\n"
        "• RSI — индикатор относительной силы."
    )
    await m.answer(text)

@dp.message(Command("examples"))
async def cmd_examples(m: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        row = await get_user_row(db, m.from_user.id)
    day = row[1] if row else 1
    lesson = load_lesson(day)
    if lesson.examples:
        await m.answer("Примеры:\n" + "\n".join("• " + x for x in lesson.examples))
    else:
        await m.answer("Пока без примеров для этого дня.")

@dp.message(Command("begin"))
async def cmd_begin(m: Message):
    today = datetime.now(MSK_TZ).date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await upsert_user(db, m.from_user.id)
        row = await get_user_row(db, m.from_user.id)
        day = row[1] if row else 1
        await set_started_today(db, m.from_user.id, today)
        await db.commit()

    lesson = load_lesson(day)
    await m.answer(
        f"🚦 День {day}: {lesson.title}\n\n"
        f"Задача: {lesson.task}\n\n"
        f"Жми кнопки ниже, чтобы читать теорию/примеры и пройти квиз.",
        reply_markup=kb_lesson(day)
    )
    if lesson.images:
        if len(lesson.images) == 1:
            await m.answer_photo(lesson.images[0], caption=f"Иллюстрация к дню {day}")
        else:
            media = [InputMediaPhoto(url) for url in lesson.images[:10]]
            await m.answer_media_group(media)

# ---------- CALLBACKS ----------
@dp.callback_query(F.data.startswith("theory:"))
async def cb_theory(cq: CallbackQuery):
    day = int(cq.data.split(":")[1])
    lesson = load_lesson(day)
    await cq.message.answer(f"📖 Теория (День {day})\n\n{lesson.theory}")
    await cq.answer()

@dp.callback_query(F.data.startswith("examples:"))
async def cb_examples(cq: CallbackQuery):
    day = int(cq.data.split(":")[1])
    lesson = load_lesson(day)
    if lesson.examples:
        await cq.message.answer("📊 Примеры:\n" + "\n".join("• " + x for x in lesson.examples))
    else:
        await cq.message.answer("Пока без примеров для этого дня.")
    await cq.answer()

@dp.callback_query(F.data.startswith("quiz:"))
async def cb_quiz(cq: CallbackQuery):
    day = int(cq.data.split(":")[1])
    lesson = load_lesson(day)
    await cq.message.answer(
        f"📝 Квиз (День {day})\n{lesson.quiz_question}",
        reply_markup=kb_quiz(day, lesson.quiz_options)
    )
    await cq.answer()

@dp.callback_query(F.data.startswith("ans:"))
async def cb_answer(cq: CallbackQuery):
    # format: ans:{day}:{letter}
    _, day_s, letter = cq.data.split(":")
    day = int(day_s)
    lesson = load_lesson(day)
    today = datetime.now(MSK_TZ).date().isoformat()

    if letter == lesson.quiz_correct:
        async with aiosqlite.connect(DB_PATH) as db:
            await set_answered_today(db, cq.from_user.id, today)
            await inc_day_if_completed(db, cq.from_user.id)
            await db.commit()
        await cq.message.answer("✅ Верно! Задание засчитано. Увидимся завтра в 19:00 🔥")
    else:
        await cq.message.answer("❌ Не то. Подумай ещё и выбери другой вариант.")
    await cq.answer()

# ---------- REMINDER LOOP ----------
async def reminder_loop():
    await db_init()
    while True:
        now = datetime.now(MSK_TZ)
        ymd = now.date().isoformat()
        in_window = REM_START <= now.time() <= REM_END

        if in_window:
            async with aiosqlite.connect(DB_PATH) as db:
                cur = await db.execute("SELECT user_id, current_day, last_started, last_reminder_ts FROM users")
                rows = await cur.fetchall()
                for user_id, cur_day, last_started, last_reminder_ts in rows:
                    st, ans, mis = await get_day_status(db, user_id, ymd)
                    if st == 1:
                        continue  # уже нажал /begin — не дёргаем

                    # не чаще 1 раза в 30 минут
                    can_send = True
                    if last_reminder_ts:
                        try:
                            prev = datetime.fromisoformat(last_reminder_ts)
                            if now - prev < REM_DELTA:
                                can_send = False
                        except Exception:
                            pass

                    if can_send:
                        try:
                            await bot.send_message(
                                user_id,
                                "⏰ 19:00–23:59 МСК — время учёбы!\nНажми /begin, чтобы начать задание за сегодня."
                            )
                            await set_last_reminder(db, user_id, now.isoformat())
                            await db.commit()
                        except Exception as e:
                            print(f"reminder error for {user_id}: {e}")

        # по окончании окна — отметим пропуск тем, кто не начинал
        if now.time() > REM_END:
            async with aiosqlite.connect(DB_PATH) as db:
                cur = await db.execute("SELECT user_id FROM users")
                users = [r[0] for r in await cur.fetchall()]
                for uid in users:
                    st, ans, mis = await get_day_status(db, uid, ymd)
                    if st == 0 and mis == 0 and ans == 0:
                        await mark_missed(db, uid, ymd)
                await db.commit()

            # спим до завтра 19:00
            tomorrow_19 = datetime.combine(now.date() + timedelta(days=1), REM_START, tzinfo=MSK_TZ)
            await asyncio.sleep((tomorrow_19 - now).total_seconds())
        else:
            await asyncio.sleep(60)  # тик раз в минуту

# ---------- RUN ----------
async def main():
    await db_init()
    await bot.set_my_commands(MAIN_MENU)
    asyncio.create_task(reminder_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    if TOKEN.startswith("PUT_") or not TOKEN:
        raise RuntimeError("Укажи токен в переменной окружения BOT_TOKEN или TOKEN.")
    asyncio.run(main())
