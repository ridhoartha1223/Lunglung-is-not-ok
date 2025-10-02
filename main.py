import asyncio
import json
import copy
import os
from subprocess import run

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

API_TOKEN = os.environ.get("API_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Load template JSON
with open("template.json", "r") as f:
    template_json = json.load(f)

# Load shapes library
with open("shapes_library.json", "r") as f:
    shapes_library = json.load(f)

# Temporary state per user
user_states = {}

# --- Step 1: /start command ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Create Emoji", callback_data="start_emoji")]
        ]
    )
    await message.answer("Welcome! Let's create your Telegram emoji.", reply_markup=keyboard)

# --- Step 2: Inline button pressed ---
@dp.callback_query(lambda c: c.data == "start_emoji")
async def start_emoji(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {"step": "await_text", "data": {}}
    await callback.message.answer("Send me the text you want to convert into an emoji.")
    await callback.answer()

# --- Step 3: Receive text from user ---
@dp.message(lambda m: m.from_user.id in user_states)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    state = user_states[user_id]

    if state["step"] == "await_text":
        text = message.text.upper()
        state["data"]["text"] = text
        state["step"] = "choose_color"

        # Generate preview with default color/font
        tgs_file = generate_tgs(text, color="#FFFFFF", font="Arial")
        await message.answer_document(
            FSInputFile(tgs_file),
            caption="Preview of your emoji text"
        )

        # Ask color
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="#FF0000", callback_data="color_#FF0000"),
                    InlineKeyboardButton(text="#00FF00", callback_data="color_#00FF00"),
                    InlineKeyboardButton(text="#0000FF", callback_data="color_#0000FF"),
                ]
            ]
        )
        await message.answer("Choose a color:", reply_markup=keyboard)

# --- Step 4: Choose color ---
@dp.callback_query(lambda c: c.data.startswith("color_"))
async def choose_color(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    color = callback.data.replace("color_", "")
    state = user_states[user_id]
    state["data"]["color"] = color
    state["step"] = "choose_font"

    # Generate preview with chosen color
    tgs_file = generate_tgs(
        state["data"]["text"],
        color=color,
        font="Arial"
    )
    await callback.message.answer_document(
        FSInputFile(tgs_file),
        caption="Preview with chosen color"
    )

    # Ask font
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Arial", callback_data="font_Arial"),
                InlineKeyboardButton(text="Roboto", callback_data="font_Roboto"),
                InlineKeyboardButton(text="ComicSans", callback_data="font_ComicSans"),
            ]
        ]
    )
    await callback.message.answer("Choose font:", reply_markup=keyboard)
    await callback.answer()

# --- Step 5: Choose font ---
@dp.callback_query(lambda c: c.data.startswith("font_"))
async def choose_font(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    font = callback.data.replace("font_", "")
    state = user_states[user_id]
    state["data"]["font"] = font
    state["step"] = "done"

    # Generate final .tgs
    tgs_file = generate_tgs(
        state["data"]["text"],
        color=state["data"].get("color", "#FFFFFF"),
        font=font
    )
    await callback.message.answer_document(
        FSInputFile(tgs_file),
        caption="Here is your final emoji .tgs!"
    )
    await callback.answer()

# --- Function to generate .tgs ---
def generate_tgs(text, color="#FFFFFF", font="Arial"):
    data = copy.deepcopy(template_json)

    # Remove existing text layers
    data["layers"] = [layer for layer in data.get("layers", []) if layer.get("ty") != 5]

    # Add shapes for each letter
    x_offset = 0
    letter_spacing = 60  # adjust spacing between letters
    for char in text:
        if char in shapes_library:
            for layer_shape in shapes_library[char]:
                layer = copy.deepcopy(layer_shape)
                # Apply color
                if "shapes" in layer:
                    for shape in layer["shapes"]:
                        if "ks" in shape and "k" in shape["ks"]:
                            for k in shape["ks"]["k"]:
                                if "i" in k:  # sanity check
                                    k["fillColor"] = hex_to_rgb(color)  # custom field for convert script
                # Apply horizontal offset
                if "shapes" in layer:
                    for shape in layer["shapes"]:
                        if "ks" in shape and "k" in shape["ks"]:
                            for k in shape["ks"]["k"]:
                                if "v" in k:
                                    k["v"] = [[x + x_offset, y] for x, y in k["v"]]
                data["layers"].append(layer)
            x_offset += letter_spacing

    tmp_json = f"tmp_{text}.json"
    with open(tmp_json, "w") as f:
        json.dump(data, f)

    tgs_file = f"{text}.tgs"
    run(["python3", "lottie_convert.py", tmp_json, tgs_file])

    return tgs_file

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2],16)/255 for i in (0,2,4)]

# --- Run bot ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
