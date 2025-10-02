import json
import copy
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from subprocess import run

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Load template JSON
with open("template.json", "r") as f:
    template_json = json.load(f)

# Simpan state user sementara
user_states = {}

# --- Step 1: Start / Welcome with Inline Button ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Create Emoji", callback_data="start_emoji")
    )
    await message.answer("Welcome! Let's create your Telegram emoji.", reply_markup=keyboard)

# --- Step 2: Handle Inline Button Press ---
@dp.callback_query_handler(lambda c: c.data == "start_emoji")
async def start_emoji(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_states[user_id] = {"step": "await_text", "data": {}}
    await bot.send_message(user_id, "Send me the text you want to convert into an emoji.")
    await callback_query.answer()

# --- Step 3: Receive text and generate preview ---
@dp.message_handler(lambda message: message.from_user.id in user_states)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    state = user_states[user_id]

    if state["step"] == "await_text":
        text = message.text
        state["data"]["text"] = text
        state["step"] = "choose_color"

        # Generate preview .tgs with default settings
        tgs_file_path = generate_tgs(text, color="#FFFFFF", size=512, font="Arial")
        await bot.send_document(user_id, open(tgs_file_path, "rb"), caption="Preview of your emoji text")

        # Ask for color
        keyboard = InlineKeyboardMarkup(row_width=3)
        for color in ["#FF0000", "#00FF00", "#0000FF"]:
            keyboard.insert(InlineKeyboardButton(color, callback_data=f"color_{color}"))
        await bot.send_message(user_id, "Choose color:", reply_markup=keyboard)

# --- Step 4: Handle color selection ---
@dp.callback_query_handler(lambda c: c.data.startswith("color_"))
async def choose_color(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    color = callback_query.data.replace("color_", "")
    state = user_states[user_id]
    state["data"]["color"] = color
    state["step"] = "choose_font"

    # Generate preview with new color
    tgs_file_path = generate_tgs(
        state["data"]["text"],
        color=color,
        size=512,
        font="Arial"  # default
    )
    await bot.send_document(user_id, open(tgs_file_path, "rb"), caption="Preview with chosen color")

    # Ask for font
    keyboard = InlineKeyboardMarkup(row_width=2)
    for font in ["Arial", "Roboto", "ComicSans"]:
        keyboard.insert(InlineKeyboardButton(font, callback_data=f"font_{font}"))
    await bot.send_message(user_id, "Choose font:", reply_markup=keyboard)
    await callback_query.answer()

# --- Step 5: Handle font selection ---
@dp.callback_query_handler(lambda c: c.data.startswith("font_"))
async def choose_font(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    font = callback_query.data.replace("font_", "")
    state = user_states[user_id]
    state["data"]["font"] = font
    state["step"] = "done"

    # Generate final .tgs
    tgs_file_path = generate_tgs(
        state["data"]["text"],
        color=state["data"].get("color", "#FFFFFF"),
        size=512,
        font=font
    )
    await bot.send_document(user_id, open(tgs_file_path, "rb"), caption="Here is your final emoji .tgs!")
    await callback_query.answer()

# --- Function to generate .tgs ---
def generate_tgs(text, color="#FFFFFF", size=512, font="Arial"):
    """
    Menggunakan template JSON, mengganti text dan properties, lalu simpan menjadi .tgs
    """
    data = copy.deepcopy(template_json)

    # Ubah text di JSON ke vector shapes
    for layer in data.get("layers", []):
        if layer.get("ty") == 5:  # Text layer
            layer["t"]["d"]["k"][0]["s"]["t"] = text
            layer["t"]["d"]["k"][0]["s"]["fc"] = hex_to_rgb(color)
            layer["t"]["d"]["k"][0]["s"]["f"] = font

    # Simpan sebagai .json sementara
    tmp_json = f"tmp_{text}.json"
    with open(tmp_json, "w") as f:
        json.dump(data, f)

    # Convert JSON to .tgs menggunakan lottie_convert.py
    tgs_file = f"{text}.tgs"
    run(["python3", "lottie_convert.py", tmp_json, tgs_file])

    return tgs_file

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)]

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
