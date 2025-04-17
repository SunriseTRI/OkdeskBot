import os
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Contact

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

DATABASE_NAME = "bot.db"

# Инициализация БД
def init_db():
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                phone TEXT,
                username TEXT,
                full_name TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT UNIQUE,
                answer TEXT
            )
        """)
        logger.info("Таблицы успешно созданы.")

# Универсальный запрос к БД
def execute_query(query: str, params: tuple = ()):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return cur.fetchall()
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Ошибка базы данных: {e}")

# Клавиатура с кнопкой "Поделиться контактом"
def get_contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я помогу ответить на твои вопросы.\n"
        "Для начала поделись своим контактом:",
        reply_markup=get_contact_keyboard()
    )

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer("Список команд:\n/help - помощь\n/faq - задать вопрос")

@dp.message(Command("faq"))
async def faq_cmd(message: types.Message):
    await message.answer("Введите ваш вопрос, и я постараюсь найти ответ в базе.")

@dp.message(content_types=types.ContentType.CONTACT)
async def handle_contact(message: types.Message):
    contact = message.contact
    try:
        execute_query(
            "INSERT OR REPLACE INTO users (user_id, phone, username, full_name) VALUES (?, ?, ?, ?)",
            (message.from_user.id, contact.phone_number, message.from_user.username, contact.first_name)
        )
        await message.answer("Спасибо! Теперь можешь задавать вопросы.", reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        logger.error(f"Ошибка при сохранении контакта: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@dp.message()
async def handle_question(message: types.Message):
    # Проверяем, зарегистрирован ли пользователь
    user = execute_query(
        "SELECT 1 FROM users WHERE user_id = ?",
        (message.from_user.id,)
    )

    if not user:
        await message.answer("Пожалуйста, сначала поделись контактом!", reply_markup=get_contact_keyboard())
        return

    # Поиск в базе FAQ
    results = execute_query(
        "SELECT answer FROM faq WHERE question LIKE ?",
        (f"%{message.text}%",)
    )

    if results:
        await message.answer(results[0][0])
    else:
        await message.answer("Ответ не найден. Ваш вопрос передан администратору.")

if __name__ == "__main__":
    init_db()
    dp.run_polling(bot)
