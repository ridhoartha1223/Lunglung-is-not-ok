import json
import asyncio
import subprocess
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8257954018:AAG4mFUjBHJ6ZQTl5b5t6_wZgqeP38oWF6I"
TEMPLATE_PATH = Path("template.json")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🎨 Buat Emoji", callback_data="make_emoji")
    await message.answer("👋 Klik tombol di bawah untuk mulai.", reply_markup=kb.as_markup())

@dp.callback_query(lambda c: c.data == "make_emoji")
async def ask_text(callback: types.CallbackQuery):
    await callback.message.answer("✍️ Kirim teks untuk emoji:")
    await callback.answer()
    dp.message.register(receive_text, lambda m: True, flags={"expecting_text": True})

async def receive_text(message: types.Message):
    text = message.text.strip()
    await message.answer(f"🔄 Membuat emoji untuk: {text}")

    # load template.json
    data = json.loads(TEMPLATE_PATH.read_text())

    # replace text "rensian" → user text
    def replace_text(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and v == "rensian":
                    obj[k] = text
                else:
                    replace_text(v)
        elif isinstance(obj, list):
            for v in obj:
                replace_text(v)
    replace_text(data)

    # simpan hasil edit sementara
    temp_json = Path("out.json")
    temp_json.write_text(json.dumps(data))

    # convert pakai lottie2tgs (NodeJS)
    out_tgs = Path("out.tgs")
    subprocess.run(["lottie2tgs", str(temp_json), str(out_tgs)], check=True)

    await message.answer_document(types.FSInputFile(out_tgs), caption="✅ Emoji jadi!")
    dp.message.unregister(receive_text)

async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
