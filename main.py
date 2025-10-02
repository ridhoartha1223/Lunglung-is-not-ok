import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from lottie.utils import script
from lottie.exporters.tgs import export_tgs
from lottie.importers import import_json

TOKEN = "YOUR_BOT_TOKEN"  # ganti sama token kamu
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== STEP 1: /start =====
@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Buat Emoji", callback_data="buat_emoji")]
    ])
    await message.answer("Selamat datang di Emoji Generator Bot!\nKlik tombol di bawah untuk mulai:", reply_markup=kb)

# ===== STEP 2: user klik tombol =====
@dp.callback_query(lambda c: c.data == "buat_emoji")
async def process_callback(callback: types.CallbackQuery):
    await callback.message.answer("Silakan kirim teks yang ingin dijadikan emoji:")
    await callback.answer()

# ===== STEP 3: user kirim teks =====
@dp.message()
async def handle_text(message: types.Message):
    user_text = message.text.strip()

    # Baca template JSON
    with open("template.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ganti semua instance text 'rensian' dengan input user
    def replace_text(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and "rensian" in v:
                    obj[k] = v.replace("rensian", user_text)
                else:
                    replace_text(v)
        elif isinstance(obj, list):
            for i in v:
                replace_text(i)

    replace_text(data)

    # Simpan JSON baru
    with open("temp.json", "w", encoding="utf-8") as f:
        json.dump(data, f)

    # Convert JSON → TGS
    animation = import_json("temp.json")
    with open("output.tgs", "wb") as f:
        export_tgs(animation, f)

    # Kirim balik ke user
    await message.answer_document(types.FSInputFile("output.tgs"), caption="✨ Ini preview emoji kamu!")

async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
