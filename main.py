import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from lottie_convert import convert

# ---------- CONFIG ----------
BOT_TOKEN = "YOUR_BOT_TOKEN"
TEMPLATE_JSON = "template.json"
dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)

# ---------- FSM STATES ----------
class EmojiWizard(StatesGroup):
    waiting_text = State()
    waiting_font = State()
    waiting_color = State()
    preview_ready = State()

# ---------- INLINE KEYBOARD ----------
def next_button():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Next ➡️", callback_data="next")]])

def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("⬅️ Back", callback_data="back")]])

# ---------- TGS GENERATOR ----------
async def generate_emoji_tgs(user_text: str, font: str, color: list, output_file: str):
    with open(TEMPLATE_JSON, "r") as f:
        template = json.load(f)

    for layer in template["layers"]:
        if layer.get("ty") == 5:  # text layer
            layer["t"]["d"]["k"][0]["s"]["t"] = user_text
            layer["t"]["d"]["k"][0]["s"]["f"] = font
            layer["t"]["d"]["k"][0]["s"]["fc"] = color

    tmp_json = "tmp.json"
    with open(tmp_json, "w") as f:
        json.dump(template, f)

    convert(tmp_json, output_file)
    return output_file

# ---------- START COMMAND ----------
@dp.message(commands=["start"])
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Welcome! Send the text for your emoji:", reply_markup=next_button())
    await state.set_state(EmojiWizard.waiting_text)

# ---------- HANDLE TEXT ----------
@dp.message(EmojiWizard.waiting_text)
async def handle_text(message: types.Message, state: FSMContext):
    user_text = message.text.strip()
    await state.update_data(text=user_text)
    await message.answer("Choose font (Arial / ComicSans / Impact):", reply_markup=next_button())
    await state.set_state(EmojiWizard.waiting_font)

# ---------- HANDLE FONT ----------
@dp.message(EmojiWizard.waiting_font)
async def handle_font(message: types.Message, state: FSMContext):
    font_choice = message.text.strip()
    await state.update_data(font=font_choice)
    await message.answer("Send color in RGB format like 1,0,0 (red):", reply_markup=next_button())
    await state.set_state(EmojiWizard.waiting_color)

# ---------- HANDLE COLOR ----------
@dp.message(EmojiWizard.waiting_color)
async def handle_color(message: types.Message, state: FSMContext):
    try:
        r, g, b = [float(x) for x in message.text.strip().split(",")]
        await state.update_data(color=[r, g, b, 1])
    except:
        await message.answer("Invalid color format! Use R,G,B like 1,0,0")
        return

    data = await state.get_data()
    tgs_file = await generate_emoji_tgs(data["text"], data["font"], data["color"], f"{message.from_user.id}.tgs")
    await message.answer_sticker(FSInputFile(tgs_file), reply_markup=back_button())
    await state.clear()

# ---------- RUN BOT ----------
async def main():
    try:
        print("Bot started...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
