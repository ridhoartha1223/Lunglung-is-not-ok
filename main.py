import json
import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lottie.parsers.tgs import parse_tgs
from lottie.exporters.tgs import export_tgs
from lottie.utils.stripper import strip_text_layers

BOT_TOKEN = "8257954018:AAG4mFUjBHJ6ZQTl5b5t6_wZgqeP38oWF6I"
TEMPLATE_PATH = Path("template.json")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- STEP 1: START HANDLER ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🎨 Buat Emoji", callback_data="make_emoji")
    await message.answer(
        "👋 Halo! Aku bisa bikin emoji animasi Telegram Premium.\n"
        "Klik tombol di bawah untuk mulai.",
        reply_markup=kb.as_markup()
    )

# --- STEP 2: INLINE BUTTON HANDLER ---
@dp.callback_query(lambda c: c.data == "make_emoji")
async def ask_text(callback: types.CallbackQuery):
    await callback.message.answer("✍️ Tulis teks yang ingin dijadikan emoji:")
    await callback.answer()
    dp.message.register(receive_text, lambda m: True, flags={"expecting_text": True})

# --- STEP 3: RECEIVE USER TEXT ---
async def receive_text(message: types.Message):
    text = message.text.strip()
    await message.answer(f"🔄 Membuat emoji untuk teks: **{text}**")

    # load template json
    data = json.loads(TEMPLATE_PATH.read_text())

    # --- replace "rensian" with user text ---
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

    # --- convert text to shapes ---
    anim = parse_tgs(json.dumps(data).encode())
    strip_text_layers(anim)  # penting: bikin text jadi vector shapes

    # --- export ke TGS ---
    out_path = Path(f"{text}.tgs")
    with out_path.open("wb") as f:
        export_tgs(anim, f, frame_rate=30, width=512, height=512)

    # kirim preview
    await message.answer_document(types.FSInputFile(out_path), caption="✅ Emoji jadi!")

    # TODO: setelah ini user bisa pilih warna/font/ukuran → update preview
    dp.message.unregister(receive_text)

# --- RUN ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
