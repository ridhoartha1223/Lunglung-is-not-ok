import json
import subprocess
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Path file
TEMPLATE_FILE = "template.json"
TEMP_JSON = "output.json"
TEMP_TGS = "output.tgs"

# ========== START HANDLER ==========
@dp.message(commands=["start"])
async def start_cmd(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Buat Emoji", switch_inline_query_current_chat="")

    await message.answer(
        "👋 Selamat datang di Emoji Generator Bot!\n\nKlik tombol di bawah untuk mulai membuat emoji:",
        reply_markup=kb.as_markup()
    )

# ========== INLINE HANDLER ==========
@dp.inline_query()
async def inline_query(inline_query: types.InlineQuery):
    results = [
        InlineQueryResultArticle(
            id="create",
            title="Buat Emoji Premium",
            input_message_content=InputTextMessageContent(
                message_text="✍️ Kirim teks yang mau kamu jadikan emoji."
            )
        )
    ]
    await inline_query.answer(results, cache_time=1)

# ========== TEXT HANDLER ==========
@dp.message()
async def handle_text(message: types.Message):
    user_text = message.text.strip()

    # 1. Baca template.json
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Cari teks "rensian" dan ganti
    def replace_text(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "t" and v == "rensian":
                    obj[k] = user_text
                else:
                    replace_text(v)
        elif isinstance(obj, list):
            for item in obj:
                replace_text(item)

    replace_text(data)

    # 3. Simpan output.json
    with open(TEMP_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    # 4. Convert ke .tgs pakai lottie2tgs
    try:
        subprocess.run(["lottie2tgs", TEMP_JSON, TEMP_TGS], check=True)
    except subprocess.CalledProcessError:
        await message.answer("❌ Gagal konversi JSON ke TGS.")
        return

    # 5. Kirim preview .tgs
    await message.answer_document(types.FSInputFile(TEMP_TGS), caption="✨ Ini preview emoji kamu!")

    # 6. Info step selanjutnya (warna, ukuran, font)
    await message.answer("👉 Sekarang pilih warna, ukuran, atau font. (fitur ini bisa ditambahkan step by step)")

# ========== RUN ==========
async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
