import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import gzip
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# -------------------- UTILITIES --------------------
def generate_emoji_image(text: str, size=512, bg_color=(255,223,0), font_color=(0,0,0), font_name="arial.ttf") -> BytesIO:
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(0,0),(size-1,size-1)], fill=bg_color)
    try:
        font_size = int(size*0.5)
        font = ImageFont.truetype(font_name, font_size)
    except:
        font = ImageFont.load_default()
    text_width, text_height = draw.textsize(text, font=font)
    text_x = (size - text_width)/2
    text_y = (size - text_height)/2
    draw.text((text_x,text_y), text, font=font, fill=font_color)
    out = BytesIO()
    out.name = "emoji.png"
    img.save(out, "PNG")
    out.seek(0)
    return out

def convert_png_to_tgs(png_bytes: BytesIO) -> BytesIO:
    out = BytesIO()
    with gzip.GzipFile(fileobj=out, mode="w") as f:
        f.write(png_bytes.getvalue())
    out.seek(0)
    out.name = "emoji.tgs"
    return out

# -------------------- STEP FUNCTIONS --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖌️ Buat Emoji", callback_data="step_text")],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="help")]
    ]
    await update.message.reply_text(
        "✨ *Ultimate Emoji Wizard Bot!* ✨\nBuat emoji custom step-by-step.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("current_step") != "text":
        await update.message.reply_text("❌ Tunggu, wizard masih berjalan. Ikuti instruksi step-by-step.")
        return

    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ Kirim teks atau emoji untuk dijadikan sticker!")
        return

    context.user_data["emoji_text"] = text
    context.user_data["current_step"] = "color"
    await send_color_step(update, context)

async def send_color_step(update, context):
    keyboard = [
        [InlineKeyboardButton("🟡 Kuning", callback_data="color_255_223_0")],
        [InlineKeyboardButton("🔴 Merah", callback_data="color_255_0_0")],
        [InlineKeyboardButton("🔵 Biru", callback_data="color_0_0_255")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_text")]
    ]
    msg_text = f"🎨 Pilih warna background:\n`{context.user_data.get('emoji_text','')}`"
    if isinstance(update, Update):
        await update.message.reply_text(msg_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.edit_message_text(msg_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_font_step(query, context):
    keyboard = [
        [InlineKeyboardButton("Arial", callback_data="font_arial.ttf")],
        [InlineKeyboardButton("Comic Sans", callback_data="font_comic.ttf")],
        [InlineKeyboardButton("Impact", callback_data="font_impact.ttf")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_color")]
    ]
    await query.edit_message_text("🖋️ Pilih font:", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_size_step(query, context):
    keyboard = [
        [InlineKeyboardButton("256 px", callback_data="size_256")],
        [InlineKeyboardButton("512 px", callback_data="size_512")],
        [InlineKeyboardButton("1024 px", callback_data="size_1024")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_font")]
    ]
    await query.edit_message_text("📐 Pilih ukuran emoji:", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_create_step(query, context):
    keyboard = [
        [InlineKeyboardButton("✅ Buat Emoji", callback_data="create_emoji")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_size")]
    ]
    text = context.user_data.get("emoji_text","")
    await query.edit_message_text(f"📌 Semua opsi siap!\nTeks: `{text}`\nTekan ✅ untuk buat emoji.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# -------------------- CALLBACK HANDLER --------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # MENU
    if data == "help":
        help_text = "ℹ️ Panduan: Ikuti wizard step-by-step untuk membuat emoji custom."
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="start")]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data == "start":
        await start(update, context)
        return
    elif data == "step_text":
        context.user_data["current_step"] = "text"
        await query.edit_message_text("📤 Silakan kirim teks/emoji untuk dijadikan sticker:")
        return
    elif data == "back_text":
        context.user_data["current_step"] = "text"
        await query.edit_message_text("📤 Silakan kirim teks/emoji untuk dijadikan sticker:")
        return

    # COLOR STEP
    elif data.startswith("color_") and context.user_data.get("current_step")=="color":
        r,g,b = map(int, data.split("_")[1:])
        context.user_data["bg_color"] = (r,g,b)
        context.user_data["current_step"] = "font"
        await send_font_step(query, context)
    elif data == "back_color" and context.user_data.get("current_step")=="font":
        context.user_data["current_step"] = "color"
        await send_color_step(query, context)

    # FONT STEP
    elif data.startswith("font_") and context.user_data.get("current_step")=="font":
        font_name = data.split("_")[1]
        context.user_data["font_name"] = font_name
        context.user_data["current_step"] = "size"
        await send_size_step(query, context)
    elif data == "back_font" and context.user_data.get("current_step")=="size":
        context.user_data["current_step"] = "font"
        await send_font_step(query, context)

    # SIZE STEP
    elif data.startswith("size_") and context.user_data.get("current_step")=="size":
        size = int(data.split("_")[1])
        context.user_data["size"] = size
        context.user_data["current_step"] = "create"
        await send_create_step(query, context)
    elif data == "back_size" and context.user_data.get("current_step")=="create":
        context.user_data["current_step"] = "size"
        await send_size_step(query, context)

    # CREATE STEP
    elif data == "create_emoji" and context.user_data.get("current_step")=="create":
        text = context.user_data.get("emoji_text","")
        bg_color = context.user_data.get("bg_color",(255,223,0))
        font_color = (0,0,0)
        size = context.user_data.get("size",512)
        font_name = context.user_data.get("font_name","arial.ttf")

        png_file = generate_emoji_image(text, size=size, bg_color=bg_color, font_color=font_color, font_name=font_name)
        tgs_file = convert_png_to_tgs(png_file)
        await query.message.reply_sticker(sticker=InputFile(tgs_file, filename="emoji.tgs"))

        # tetap di create step agar user bisa generate lagi
        await send_create_step(query, context)

# -------------------- MAIN --------------------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()

