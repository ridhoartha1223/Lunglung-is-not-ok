import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler
)
import logging
import io
import json
import gzip

# --- KONFIGURASI BOT ---
TOKEN = "8257954018:AAG4mFUjBHJ6ZQTl5b5t6_wZgqeP38oWF6I"

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# States
TEXT, COLOR, SIZE, FONT, WAITING_OPTIONS = range(5)

# Konfigurasi default TGS
TGS_CONFIG = {
    "width": 512,
    "height": 512,
    "duration": 3,
    "frame_rate": 30
}

# Pilihan warna
COLORS = {
    "Merah": "#FF0000",
    "Biru": "#0000FF",
    "Kuning": "#FFFF00",
    "Putih": "#FFFFFF",
    "Hitam": "#000000"
}

# Pilihan font → pakai font yang Telegram kenal
FONTS = {
    "Roboto": "Roboto-Regular",
    "NotoSans": "NotoSans-Regular",
    "Monospace": "CourierNewPSMT"
}

# --- FUNGSI PEMBUATAN TGS ---

def generate_lottie_json(text, color, size, font_name, config):
    r = int(color[1:3], 16) / 255.0
    g = int(color[3:5], 16) / 255.0
    b = int(color[5:7], 16) / 255.0

    lottie_json = {
        "v": "5.5.2",
        "fr": config["frame_rate"],
        "w": config["width"],
        "h": config["height"],
        "ip": 0,
        "op": config["duration"] * config["frame_rate"],
        "assets": [],
        "layers": [
            {
                "ty": 5,
                "nm": "Text Layer",
                "ip": 0,
                "op": config["duration"] * config["frame_rate"],
                "st": 0,
                "ks": {
                    "o": {"a": 0, "k": 100},
                    "p": {"a": 0, "k": [256, 256, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]}
                },
                "t": {
                    "d": {
                        "k": [
                            {
                                "s": {
                                    "t": text,
                                    "f": font_name,
                                    "s": size,
                                    "j": 2,
                                    "tr": 0,
                                    "lh": size * 1.2,
                                    "ls": 0,
                                    "fc": [r, g, b]
                                },
                                "t": 0
                            }
                        ]
                    },
                    "p": {},
                    "m": {}
                }
            }
        ],
        "meta": {"tgs": 1}
    }

    json_string = json.dumps(lottie_json)
    tgs_bytes = gzip.compress(json_string.encode("utf-8"))
    return io.BytesIO(tgs_bytes)

# --- HANDLER BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✨ Mulai Buat Emoji TGS ✨", callback_data="start_creation")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Halo! Saya bot pembuat emoji TGS.\nKlik tombol di bawah untuk memulai.",
        reply_markup=reply_markup
    )

async def handle_callback_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["tgs_data"] = {
        "text": None,
        "color": COLORS["Hitam"],
        "size": 100,
        "font": "Roboto-Regular",
        "font_name": "Roboto"
    }

    await query.edit_message_text(
        "Silakan kirimkan **TEKS** yang ingin dijadikan emoji (maks 20 karakter).",
        parse_mode="Markdown"
    )
    return TEXT

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["tgs_data"]["text"] = text
    await update.message.reply_text(f"Teks diatur: **{text}**.", parse_mode="Markdown")
    return await preview_and_options(update, context)

async def preview_and_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("tgs_data")

    if not data or not data.get("text"):
        await update.effective_message.reply_text("Teks belum diatur. Silakan kirim teks terlebih dahulu.")
        return TEXT

    try:
        tgs_file = generate_lottie_json(
            text=data["text"],
            color=data["color"],
            size=data["size"],
            font_name=data["font"],
            config=TGS_CONFIG
        )
        tgs_file.seek(0)

        color_name = next(k for k, v in COLORS.items() if v == data["color"])
        caption = (
            "**PREVIEW EMOJI TGS ANDA**\n\n"
            f"Teks: `{data['text']}`\n"
            f"Warna: `{data['color']}` ({color_name})\n"
            f"Ukuran: `{data['size']}`\n"
            f"Font: `{data['font_name']}`\n\n"
            "Pilih opsi di bawah untuk mengubah:"
        )

        keyboard = [
            [InlineKeyboardButton("🎨 Warna", callback_data="choose_color"),
             InlineKeyboardButton("📏 Ukuran", callback_data="choose_size")],
            [InlineKeyboardButton("🔠 Font", callback_data="choose_font")],
            [InlineKeyboardButton("✅ Selesai", callback_data="finish")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.effective_message.reply_sticker(sticker=tgs_file)
        await update.effective_message.reply_text(text=caption, reply_markup=reply_markup, parse_mode="Markdown")

        return WAITING_OPTIONS

    except Exception as e:
        logging.error(f"Error creating TGS: {e}")
        await update.effective_message.reply_text(f"❌ Terjadi kesalahan: {e}")
        return TEXT

# Handler opsi
async def handle_options_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "choose_color":
        return await choose_color_step(update, context)
    elif data == "choose_size":
        return await choose_size_step(update, context)
    elif data == "choose_font":
        return await choose_font_step(update, context)
    elif data == "finish":
        await query.edit_message_reply_markup(reply_markup=None)
        return await finish(update, context)

    return WAITING_OPTIONS

async def handle_setting_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data.split("_", 2)
    action = data[1]
    value = data[2]

    if action == "color":
        context.user_data["tgs_data"]["color"] = COLORS[value]
        context.user_data["tgs_data"]["color_name"] = value
        await query.edit_message_text(f"Warna diatur ke **{value}**.", parse_mode="Markdown")
    elif action == "size":
        context.user_data["tgs_data"]["size"] = int(value)
        await query.edit_message_text(f"Ukuran diatur ke **{value}**.", parse_mode="Markdown")
    elif action == "font":
        context.user_data["tgs_data"]["font"] = FONTS[value]
        context.user_data["tgs_data"]["font_name"] = value
        await query.edit_message_text(f"Font diatur ke **{value}**.", parse_mode="Markdown")

    return await preview_and_options(update, context)

async def choose_color_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton(f"🎨 {name}", callback_data=f"set_color_{name}")]
                for name in COLORS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Pilih warna:", reply_markup=reply_markup)
    return COLOR

async def choose_size_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sizes = [50, 80, 100, 120, 150]
    keyboard = [[InlineKeyboardButton(f"📏 {s}px", callback_data=f"set_size_{s}")] for s in sizes]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Pilih ukuran:", reply_markup=reply_markup)
    return SIZE

async def choose_font_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton(f"🔠 {name}", callback_data=f"set_font_{name}")] for name in FONTS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Pilih font:", reply_markup=reply_markup)
    return FONT

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Selesai! Anda bisa simpan file TGS di atas dan buat set stiker baru via @Stickers.")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Pembuatan emoji dibatalkan. Jalankan /start lagi untuk memulai.")
    context.user_data.clear()
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback_entry, pattern="^start_creation$")],
        states={
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)],
            COLOR: [CallbackQueryHandler(handle_setting_change, pattern="^set_color_")],
            SIZE: [CallbackQueryHandler(handle_setting_change, pattern="^set_size_")],
            FONT: [CallbackQueryHandler(handle_setting_change, pattern="^set_font_")],
            WAITING_OPTIONS: [CallbackQueryHandler(handle_options_selection, pattern="^(choose_|finish)")],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)

    print("Bot berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
