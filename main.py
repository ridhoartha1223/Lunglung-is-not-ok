import io
import json
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

API_TOKEN = "YOUR_BOT_TOKEN"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# User state
user_data = {}

# Options
colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
fonts = ["fonts/Arial-Bold.ttf", "fonts/Verdana.ttf", "fonts/TimesNewRoman.ttf"]
animations = ["fade", "scale", "bounce", "slide", "rotate"]

# --- Handlers ---

@dp.message(commands=["start"])
async def start(message: types.Message):
    await message.reply("Halo! Kirim teks yang ingin dijadikan emoji animasi:")

@dp.message()
async def get_text(message: types.Message):
    if message.from_user.id not in user_data:
        user_data[message.from_user.id] = {"text": message.text}
        # Color selection inline
        keyboard = InlineKeyboardMarkup(row_width=3)
        keyboard.add(*[InlineKeyboardButton(text=c, callback_data=f"color|{c}") for c in colors])
        await message.reply("Pilih warna teks:", reply_markup=keyboard)

@dp.callback_query()
async def callback_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data_cb = callback_query.data

    if user_id not in user_data:
        await callback_query.answer("Kirim teks dulu dengan /start")
        return

    if data_cb.startswith("color|"):
        user_data[user_id]["color"] = data_cb.split("|")[1]
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(*[InlineKeyboardButton(text=f, callback_data=f"font|{f}") for f in fonts])
        await callback_query.message.edit_text(f"Warna dipilih: {data_cb.split('|')[1]}\nPilih font:", reply_markup=keyboard)

    elif data_cb.startswith("font|"):
        user_data[user_id]["font"] = data_cb.split("|")[1]
        await callback_query.message.edit_text(f"Font dipilih: {data_cb.split('|')[1]}\nMasukkan ukuran teks (contoh: 64):")

    elif data_cb.startswith("anim|"):
        user_data[user_id]["animation"] = data_cb.split("|")[1]
        await generate_tgs(callback_query.message, user_id)

@dp.message()
async def get_size(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data and "size" not in user_data[user_id]:
        try:
            size = int(message.text)
            user_data[user_id]["size"] = size
            keyboard = InlineKeyboardMarkup(row_width=3)
            keyboard.add(*[InlineKeyboardButton(text=a.capitalize(), callback_data=f"anim|{a}") for a in animations])
            await message.reply("Pilih animasi teks:", reply_markup=keyboard)
        except:
            await message.reply("Ukuran tidak valid, masukkan angka.")

# --- Generate TGS ---
async def generate_tgs(message, user_id):
    data = user_data[user_id]
    text = data["text"]
    color = data["color"]
    font_path = data["font"]
    size = data["size"]
    animation = data["animation"]

    # --- Preview GIF ---
    frames = []
    for i in range(5):
        img = Image.new("RGBA", (256, 256), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font_path, size)
        x, y = 128, 128
        if animation == "fade":
            alpha = int(255*(i+1)/5)
        elif animation == "scale":
            scale = 0.5 + 0.5*(i+1)/5
            font = ImageFont.truetype(font_path, int(size*scale))
            alpha = 255
        elif animation == "bounce":
            y += (-1)**i * 20
            alpha = 255
        elif animation == "slide":
            x += int(-50 + 25*i)
            alpha = 255
        elif animation == "rotate":
            img = img.rotate(i*15, expand=1)
            alpha = 255
        draw.text((x, y), text, font=font, fill=color)
        frames.append(img)

    preview_bytes = io.BytesIO()
    frames[0].save(preview_bytes, format="GIF", save_all=True, append_images=frames[1:], duration=200, loop=0)
    preview_bytes.seek(0)
    await message.reply_document(types.InputFile(preview_bytes, filename="preview.gif"), caption="Preview animasi")

    # --- Generate TGS JSON ---
    tgs = {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 60,
        "w": 256,
        "h": 256,
        "nm": "text_emoji",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 5,
                "nm": text,
                "sr": 1,
                "ks": {
                    "o": {"a":1,"k":[{"t":0,"s":[0],"e":[100]},{"t":30}]},
                    "p":{"a":0,"k":[128,128,0]},
                    "s":{"a":1,"k":[{"t":0,"s":[50,50,100],"e":[100,100,100]},{"t":30}]}
                },
                "t": {
                    "d":{"k":[{"s":{"sz":[256,256],"ps":[0,0],"s":size,"f":font_path,"t":text,"j":0,"tr":0,"lh":int(size*1.2),"fc":[int(color[1:3],16)/255,int(color[3:5],16)/255,int(color[5:7],16)/255]},"t":0}]},
                    "p":{},
                    "m":{"g":0,"a":0}
                },
                "ao":0
            }
        ]
    }

    tgs_bytes = io.BytesIO()
    tgs_bytes.write(json.dumps(tgs).encode())
    tgs_bytes.seek(0)
    await message.reply_document(types.InputFile(tgs_bytes, filename="emoji.tgs"), caption="🎉 TGS siap kirim ke @sikers!")
    del user_data[user_id]

# --- Run Bot ---
async def main():
    try:
        print("Bot is starting...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
