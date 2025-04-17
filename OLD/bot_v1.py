# bot.py
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from database import create_tables, execute_query, update_faq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Добро пожаловать! Используйте /help для списка команд")


@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    text = (
        "Список команд:\n"
        "/reg - Регистрация\n"
        "/faq - Поиск в базе знаний\n"
        "/update_faq - Обновить FAQ"
    )
    await message.answer(text)


@dp.message(Command("reg"))
async def registration(message: types.Message):
    await message.answer("Введите ваш телефон в формате +71234567890:")


@dp.message(Command("update_faq"))
async def update_faq_handler(message: types.Message):
    try:
        new, updated = update_faq("faq.xlsx")
        await message.answer(f"Обновлено: {new} новых, {updated} измененных")
    except Exception as e:
        logger.error(f"FAQ update failed: {e}")
        await message.answer("Ошибка обновления")


@dp.message()
async def handle_message(message: types.Message):
    question = message.text.strip()

    # Поиск в FAQ
    faq_results = execute_query(
        "SELECT answer FROM faq WHERE question LIKE ?",
        (f"%{question}%",)
    )

    if faq_results:
        await message.answer(f"Ответ: {faq_results[0][0]}")
    else:
        await message.answer("Ответ не найден. Вопрос передан администратору.")


if __name__ == "__main__":
    create_tables()
    dp.run_polling(bot)