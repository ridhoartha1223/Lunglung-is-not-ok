import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
import logging
import io
import json
import gzip

# --- KONFIGURASI BOT ---
TOKEN = "8257954018:AAG4mFUjBHJ6ZQTl5b5t6_wZgqeP38oWF6I"

# Aktifkan logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Definisikan 'states'
TEXT, COLOR, SIZE, FONT, WAITING_OPTIONS = range(5)

# Data default untuk TGS
TGS_CONFIG = {
    "width": 512,
    "height": 512,
    "duration": 3,
    "frame_rate": 30
}

# Pilihan warna & font
COLORS = {
    "Merah": "#FF0000",
    "Biru": "#0000FF",
    "Kuning": "#FFFF00",
    "Putih": "#FFFFFF",
    "Hitam": "#000000"
}

FONTS = {
    "Arial": "arial.ttf",
    "Roboto": "roboto.ttf",
    "Monospace": "monospace.ttf",
    "Impact": "impact.ttf"
}

# --- FUNGSI PEMBUATAN LOTTIE JSON ---
def generate_lottie_json(text, color, size, font_path, config):
    """Generate file .tgs (Lottie JSON + gzip) dari teks sederhana"""
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
                    "o": {"a": 0, "k": 100},             # opacity full
                    "p": {"a": 0, "k": [256, 256, 0]},   # posisi tengah
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]}  # scale 100%
                },
                "t": {
                    "d": {
                        "k": [
                            {
                                "s": {
                                    "t": text,                      # teks
                                    "f": font_path.split('.')[0],   # font name
                                    "s": size,                      # font size
                                    "fc": [r, g, b]                 # warna RGB
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("✨ Mulai Buat Emoji TGS ✨", callback_data="start_creation")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Halo! Saya adalah Bot Pembuat Emoji TGS. Klik tombol di bawah untuk memulai.",
        reply_markup=reply_markup,
    )

async def handle_callback_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["tgs_data"] = {
        "text": None,
        "color": COLORS["Hitam"],
        "size": 100,
        "font": FONTS["Arial"],
        "font_name": "Arial",
    }

    await query.edit_message_text(
        "Silakan kirimkan **TEKS** yang ingin Anda jadikan emoji TGS.\n\n*(Maksimal 20 Karakter)*",
        parse_mode="Markdown",
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
        await update.effective_message.reply_text("Teks belum diatur.")
        return TEXT

    try:
        tgs_file = generate_lottie_json(
            text=data["text"],
            color=data["color"],
            size=data["size"],
            font_path=data["font"],
            config=TGS_CONFIG,
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
            [
                InlineKeyboardButton("🎨 Pilih Warna", callback_data="choose_color"),
                InlineKeyboardButton("📏 Pilih Ukuran", callback_data="choose_size"),
            ],
            [InlineKeyboardButton("🔠 Pilih Font", callback_data="choose_font")],
            [InlineKeyboardButton("✅ Selesai", callback_data="finish")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.effective_message.reply_sticker(sticker=tgs_file)
        await update.effective_message.reply_text(caption, reply_markup=reply_markup, parse_mode="Markdown")

        return WAITING_OPTIONS

    except Exception as e:
        logging.error(f"Error creating TGS: {e}")
        await update.effective_message.reply_text(f"❌ Terjadi kesalahan: {e}")
        return TEXT

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
    keyboard = [[InlineKeyboardButton(f"🎨 {name} ({code})", callback_data=f"set_color_{name}")] for name, code in COLORS.items()]
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="preview_back")])
    await update.callback_query.edit_message_text("Pilih salah satu warna:", reply_markup=InlineKeyboardMarkup(keyboard))
    return COLOR

async def choose_size_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sizes = [50, 80, 100, 120, 150]
    keyboard = [[InlineKeyboardButton(f"📏 {s}px", callback_data=f"set_size_{s}")] for s in sizes]
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="preview_back")])
    await update.callback_query.edit_message_text("Pilih ukuran:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SIZE

async def choose_font_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton(f"🔠 {name}", callback_data=f"set_font_{name}")] for name in FONTS.keys()]
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="preview_back")])
    await update.callback_query.edit_message_text("Pilih font:", reply_markup=InlineKeyboardMarkup(keyboard))
    return FONT

async def back_to_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)
    return await preview_and_options(update, context)

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✅ **Proses Selesai!**\n\n"
        "Silakan gunakan stiker TGS di atas untuk membuat set stiker baru via @Stickers."
    )
    if "tgs_data" in context.user_data:
        del context.user_data["tgs_data"]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Pembuatan emoji dibatalkan. Gunakan /start untuk mulai lagi.")
    if "tgs_data" in context.user_data:
        del context.user_data["tgs_data"]
    return ConversationHandler.END

# --- MAIN ---
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback_entry, pattern="^start_creation$")],
        states={
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)],
            COLOR: [
                CallbackQueryHandler(handle_setting_change, pattern="^set_color_"),
                CallbackQueryHandler(back_to_preview, pattern="^preview_back$"),
            ],
            SIZE: [
                CallbackQueryHandler(handle_setting_change, pattern="^set_size_"),
                CallbackQueryHandler(back_to_preview, pattern="^preview_back$"),
            ],
            FONT: [
                CallbackQueryHandler(handle_setting_change, pattern="^set_font_"),
                CallbackQueryHandler(back_to_preview, pattern="^preview_back$"),
            ],
            WAITING_OPTIONS: [
                CallbackQueryHandler(handle_options_selection, pattern="^choose_(color|size|font|finish)$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    print("Bot berjalan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
