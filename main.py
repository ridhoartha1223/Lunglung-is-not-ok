import os
import json
import copy
from subprocess import run
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Load template json
with open("template.json", "r") as f:
    template_json = json.load(f)


class Form(StatesGroup):
    waiting_for_text = State()


@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await message.answer("Kirim teks yang mau dijadikan .tgs 🚀")
    await state.set_state(Form.waiting_for_text)


@dp.message(Form.waiting_for_text)
async def handle_text(message: types.Message, state: FSMContext):
    text = message.text.strip()
    await message.answer(f"Sedang membuat emoji '{text}' ...")

    try:
        tgs_file = generate_tgs(text, color="#FFFFFF", font="Arial")
        await message.answer_document(FSInputFile(tgs_file))
    except Exception as e:
        await message.answer(f"❌ Gagal convert: {e}")

    await state.clear()


def generate_tgs(text, color="#FFFFFF", font="Arial"):
    data = copy.deepcopy(template_json)

    for layer in data.get("layers", []):
        if layer.get("ty") == 5:  # Text layer
            try:
                layer["t"]["d"]["k"][0]["s"]["t"] = text
                layer["t"]["d"]["k"][0]["s"]["fc"] = hex_to_rgb(color)
                layer["t"]["d"]["k"][0]["s"]["f"] = font
            except Exception as e:
                print("⚠️ gagal update text:", e)

        elif layer.get("ty") == 4:  # Shape layer
            for shape in layer.get("shapes", []):
                if shape.get("ty") == "fl":  # Fill
                    try:
                        shape["c"]["k"] = hex_to_rgb(color)
                    except Exception as e:
                        print("⚠️ gagal update fill:", e)

                if shape.get("ty") == "st":  # Stroke
                    try:
                        shape["c"]["k"] = hex_to_rgb(color)
                    except Exception as e:
                        print("⚠️ gagal update stroke:", e)

                if shape.get("ty") == "sh":  # Path
                    if "ks" in shape:
                        ks = shape["ks"]
                        if "k" in ks:
                            pass  # biarkan path apa adanya

    tmp_json = f"tmp_{text}.json"
    with open(tmp_json, "w") as f:
        json.dump(data, f)

    tgs_file = f"{text}.tgs"
    run(["python3", "lottie_convert.py", tmp_json, tgs_file])

    return tgs_file


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4)]


if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
