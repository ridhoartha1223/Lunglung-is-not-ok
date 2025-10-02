import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import gzip
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# -------------------- UTILITIES --------------------
def generate_emoji_image(text: str, size=512, bg_color=(255,223,0), font_color=(0,0,0), font_name="arial.ttf") -> BytesIO:
    img = Image.new("RGBA", (size,size), (0,0,0,0))
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

# -------------------- HANDLERS --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖌️ Buat Emoji", callback_data="create")],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="help")]
    ]
    await update.message.reply_text(
        "✨ *Ultimate Emoji Creator Bot!* ✨\n"
        "Buat emoji custom dengan font, warna, size, dan langsung jadi sticker Telegram!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ Kirim teks atau emoji untuk dijadikan sticker!")
        return
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    context.user_data["emoji_texts"] = lines
    context.user_data["bg_color"] = (255,223,0)
    context.user_data["font_color"] = (0,0,0)
    context.user_data["size"] = 512
    context.user_data["font_name"] = "arial.ttf"
    await send_preview_menu(update, context)

async def send_preview_menu(update, context):
    lines = context.user_data.get("emoji_texts", ["Tidak Ada Teks"])
    keyboard = [
        [InlineKeyboardButton("🎨 Pilih Warna", callback_data="choose_color")],
        [InlineKeyboardButton("🖋️ Pilih Font", callback_data="choose_font")],
        [InlineKeyboardButton("📐 Pilih Ukuran", callback_data="choose_size")],
        [InlineKeyboardButton("✅ Buat Emoji", callback_data="create_emoji")],
        [InlineKeyboardButton("❌ Batal", callback_data="reset")]
    ]
    text_preview = f"📝 Teks: `{', '.join(lines)}`\nPilih opsi untuk menyesuaikan emoji:"
    if isinstance(update, Update):
        await update.message.reply_text(text_preview, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.edit_message_text(text_preview, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "help":
        help_text = (
            "ℹ️ *Panduan Ultimate Emoji Creator*\n\n"
            "1. Klik 🖌️ Buat Emoji\n"
            "2. Kirim teks / emoji (multi line untuk multi sticker)\n"
            "3. Pilih warna, font, size\n"
            "4. Klik ✅ Buat Emoji → semua emoji dikirim sebagai sticker .tgs"
        )
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="main")]]
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data == "main":
        keyboard = [
            [InlineKeyboardButton("🖌️ Buat Emoji", callback_data="create")],
            [InlineKeyboardButton("ℹ️ Bantuan", callback_data="help")]
        ]
        await query.edit_message_text("👋 Kembali ke Menu Utama", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data == "create":
        await query.edit_message_text("📤 Silakan kirim teks yang ingin dijadikan sticker (multi line untuk multi sticker).")
        return
    elif data == "reset":
        context.user_data.clear()
        await query.edit_message_text("✅ Semua data direset. Kirim teks baru untuk mulai lagi.")
        return
    elif data == "choose_color":
        keyboard = [
            [InlineKeyboardButton("🟡 Kuning", callback_data="color_255_223_0")],
            [InlineKeyboardButton("🔴 Merah", callback_data="color_255_0_0")],
            [InlineKeyboardButton("🔵 Biru", callback_data="color_0_0_255")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_customize")]
        ]
        await query.edit_message_text("🎨 Pilih warna background:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data.startswith("color_"):
        _, r, g, b = data.split("_")
        context.user_data["bg_color"] = (int(r), int(g), int(b))
        await send_back_to_preview(query, context, f"✅ Warna diubah ke RGB({r},{g},{b})")
        return
    elif data == "choose_size":
        keyboard = [
            [InlineKeyboardButton("256 px", callback_data="size_256")],
            [InlineKeyboardButton("512 px", callback_data="size_512")],
            [InlineKeyboardButton("1024 px", callback_data="size_1024")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_customize")]
        ]
        await query.edit_message_text("📐 Pilih ukuran emoji:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data.startswith("size_"):
        size = int(data.split("_")[1])
        context.user_data["size"] = size
        await send_back_to_preview(query, context, f"✅ Ukuran diubah menjadi {size} px")
        return
    elif data == "choose_font":
        keyboard = [
            [InlineKeyboardButton("Arial", callback_data="font_arial.ttf")],
            [InlineKeyboardButton("Comic Sans", callback_data="font_comic.ttf")],
            [InlineKeyboardButton("Impact", callback_data="font_impact.ttf")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_customize")]
        ]
        await query.edit_message_text("🖋️ Pilih font:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data.startswith("font_"):
        font_name = data.split("_")[1]
        context.user_data["font_name"] = font_name
        await send_back_to_preview(query, context, f"✅ Font diubah menjadi {font_name}")
        return
    elif data == "back_customize":
        await send_back_to_preview(query, context)
        return
    elif data == "create_emoji":
        lines = context.user_data.get("emoji_texts", ["A"])
        bg_color = context.user_data.get("bg_color", (255,223,0))
        font_color = context.user_data.get("font_color", (0,0,0))
        size = context.user_data.get("size", 512)
        font_name = context.user_data.get("font_name", "arial.ttf")
        for text in lines:
            png_file = generate_emoji_image(text, size=size, bg_color=bg_color, font_color=font_color, font_name=font_name)
            tgs_file = convert_png_to_tgs(png_file)
            await query.message.reply_sticker(sticker=InputFile(tgs_file, filename=f"{text}.tgs"))
        await send_back_to_preview(query, context, "✅ Semua emoji berhasil dibuat!")

async def send_back_to_preview(query, context, msg_extra=""):
    lines = context.user_data.get("emoji_texts", ["Tidak Ada Teks"])
    keyboard = [
        [InlineKeyboardButton("🎨 Pilih Warna", callback_data="choose_color")],
        [InlineKeyboardButton("🖋️ Pilih Font", callback_data="choose_font")],
        [InlineKeyboardButton("📐 Pilih Ukuran", callback_data="choose_size")],
        [InlineKeyboardButton("✅ Buat Emoji", callback_data="create_emoji")],
        [InlineKeyboardButton("❌ Batal", callback_data="reset")]
    ]
    await query.edit_message_text(
        f"{msg_extra}\n📝 Teks: `{', '.join(lines)}`\nPilih opsi lain atau buat emoji:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------------------- MAIN --------------------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
