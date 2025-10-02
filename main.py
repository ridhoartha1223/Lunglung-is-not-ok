import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = os.environ.get("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Start Command ---
@dp.message(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Create Emoji", callback_data="start_emoji")
    )
    await message.answer("Welcome! Let's create your Telegram emoji.", reply_markup=keyboard)

# --- Inline Handler ---
@dp.callback_query(lambda c: c.data == "start_emoji")
async def start_emoji(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Send me the text you want to convert into an emoji.")
    await callback_query.answer()

# --- Run Bot ---
async def main():
    # register handlers
    dp.include_router(dp)  # include routers if any
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
