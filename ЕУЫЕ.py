import os
import sqlite3
import logging
import sqlite3
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# ENV
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Настройки прокси (раскомментировать при необходимости)
# from aiogram.client.session.aiohttp import AiohttpSession
# session = AiohttpSession(proxy='http://proxy:port')
# bot = Bot(token=os.getenv("BOT_TOKEN"), session=session)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


def init_db():
    with sqlite3.connect("bot.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE,
                phone TEXT,
                username TEXT,
                full_name TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY,
                question TEXT UNIQUE,
                answer TEXT
            )
        """)


def get_contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]],
        resize_keyboard=True
    )


@dp.message(Command("start"))
async def start(message: types.Message):
    try:
        with sqlite3.connect("bot.db") as conn:
            user = conn.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (message.from_user.id,)
            ).fetchone()

        if not user:
            await message.answer(
                "Для работы бота поделитесь контактом:",
                reply_markup=get_contact_keyboard()
            )
        else:
            await message.answer(
                "Вы уже зарегистрированы! Задайте вопрос:",
                reply_markup=ReplyKeyboardRemove()
            )
    except Exception as e:
        logger.error(f"Start error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")


@dp.message(F.content == "contact")
async def handle_contact(message: types.Message):
    try:
        with sqlite3.connect("bot.db") as conn:
            conn.execute(
                """INSERT OR REPLACE INTO users 
                (user_id, phone, username, full_name) 
                VALUES (?, ?, ?, ?)""",
                (
                    message.from_user.id,
                    message.contact.phone_number,
                    message.from_user.username,
                    message.contact.first_name or ""
                )
            )
        await message.answer(
            "✅ Регистрация завершена! Задайте вопрос:",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"User {message.from_user.id} registered")
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await message.answer("❌ Ошибка регистрации")


@dp.message()
async def handle_question(message: types.Message):
    try:
        # Проверка регистрации
        with sqlite3.connect("bot.db") as conn:
            user = conn.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (message.from_user.id,)
            ).fetchone()

        if not user:
            await message.answer(
                "❌ Сначала пройдите регистрацию!",
                reply_markup=get_contact_keyboard()
            )
            return

        # Поиск в FAQ
        with sqlite3.connect("bot.db") as conn:
            answer = conn.execute(
                "SELECT answer FROM faq WHERE question LIKE ?",
                (f"%{message.text}%",)
            ).fetchone()

        response = answer[0] if answer else "📨 Вопрос передан администратору"
        await message.answer(response)

    except TelegramNetworkError as e:
        logger.error(f"Network error: {e}")
        await message.answer("⌛ Не удалось отправить ответ. Попробуйте позже.")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте еще раз.")


if __name__ == "__main__":
    init_db()
    try:
        logger.info("Starting bot...")
        dp.run_polling(bot)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.critical(f"Fatal error: {e}")
        logger.critical(f"Fatal error: {e}")