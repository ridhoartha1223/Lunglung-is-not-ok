import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
import logging
import os
import io
import json
import gzip

# --- Konfigurasi dan Setup ---
# Ganti dengan token bot Anda
TOKEN = "GANTI_DENGAN_TOKEN_BOT_ANDA"

# Aktifkan logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Definisikan 'states' untuk ConversationHandler
TEXT, COLOR, SIZE, FONT = range(4)

# Data default untuk TGS
TGS_CONFIG = {
    "width": 512,
    "height": 512,
    "duration": 3,   # Durasi 3 detik
    "frame_rate": 30 # Frame rate 30 FPS
}

# Data Warna & Font yang bisa dipilih (Contoh)
COLORS = {
    "Merah": "#FF0000",
    "Biru": "#0000FF",
    "Hijau": "#00FF00",
    "Hitam": "#000000"
}

FONTS = {
    "Arial": "arial.ttf",
    "Roboto": "roboto.ttf",
    "Monospace": "monospace.ttf"
}

# --- Fungsi Inti Pembuatan TGS (Simulasi) ---

def generate_lottie_json(text, color, size, font_path, config):
    """
    SIMULASI fungsi untuk menghasilkan Lottie JSON dari teks.
    ***INI ADALAH BAGIAN PALING KOMPLEKS YANG HARUS ANDA KEMBANGKAN***
    Anda harus menggunakan pustaka Lottie (misalnya python-lottie) untuk
    merender teks dan menghasilkan JSON yang sesuai dengan spesifikasi TGS.
    """
    logging.info(f"Generating Lottie for: {text}, Color: {color}, Size: {size}, Font: {font_path}")
    
    # --- CONTOH SANGAT SEDERHANA LOTTIE JSON DENGAN TEXT (TIDAK VALID UNTUK TGS NYATA) ---
    # Struktur TGS JSON nyata SANGAT panjang dan detail
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
                "ty": 5, # Teks Layer
                "t": {
                    "d": {
                        "k": [
                            {
                                "s": {
                                    "t": text,
                                    "s": size,
                                    "f": font_path.split('.')[0], # Nama Font
                                    "fc": [
                                        int(color[1:3], 16) / 255.0,
                                        int(color[3:5], 16) / 255.0,
                                        int(color[5:7], 16) / 255.0
                                    ]
                                }
                            }
                        ]
                    }
                },
                "nm": "Teks Stiker"
            }
        ],
        "meta": {"tgs": 1} # Penanda TGS
    }
    
    # Konversi ke string JSON dan kompresi GZIP
    json_string = json.dumps(lottie_json)
    tgs_bytes = gzip.compress(json_string.encode('utf-8'))
    
    return io.BytesIO(tgs_bytes)

# --- Fungsi Handler Bot ---

# Handler Inline (Bot Welcome)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan selamat datang dengan tombol inline."""
    keyboard = [
        [
            InlineKeyboardButton("✨ Mulai Buat Emoji TGS ✨", callback_data='start_creation')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'Halo! Saya adalah Bot Pembuat Emoji TGS. Mari kita buat stiker teks animasi Anda!',
        reply_markup=reply_markup
    )
    # Tidak menggunakan ConversationHandler di sini, hanya memulai dengan inline.

# Handler Callback Query dari tombol inline
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menangani klik tombol inline dan memulai proses konversi."""
    query = update.callback_query
    await query.answer() # Hilangkan notifikasi loading
    
    if query.data == 'start_creation':
        # Mengatur data pengguna default
        context.user_data['tgs_data'] = {
            'text': None,
            'color': COLORS['Hitam'], # Default
            'size': 100,             # Default
            'font': FONTS['Arial'],  # Default
            'font_name': 'Arial'
        }
        
        # Meminta teks dari pengguna
        await query.edit_message_text(
            'Silakan kirimkan **TEKS** yang ingin Anda jadikan emoji TGS. (Contoh: WAHH!)\n\n*(Maksimal 20 Karakter untuk hasil terbaik)*',
            parse_mode='Markdown'
        )
        return TEXT
    
    # Logika untuk memilih opsi (warna, ukuran, font)
    elif query.data.startswith('set_color_'):
        _, color_name = query.data.split('_', 2)
        context.user_data['tgs_data']['color'] = COLORS[color_name]
        context.user_data['current_step'] = COLOR # Menyimpan langkah terakhir untuk kembali
        await query.edit_message_text(f"Warna diatur ke **{color_name}**.", parse_mode='Markdown')
        return await preview_and_options(update, context)

    elif query.data.startswith('set_size_'):
        _, new_size = query.data.split('_')
        context.user_data['tgs_data']['size'] = int(new_size)
        context.user_data['current_step'] = SIZE
        await query.edit_message_text(f"Ukuran diatur ke **{new_size}**.", parse_mode='Markdown')
        return await preview_and_options(update, context)

    elif query.data.startswith('set_font_'):
        _, font_name = query.data.split('_', 2)
        context.user_data['tgs_data']['font'] = FONTS[font_name]
        context.user_data['tgs_data']['font_name'] = font_name
        context.user_data['current_step'] = FONT
        await query.edit_message_text(f"Font diatur ke **{font_name}**.", parse_mode='Markdown')
        return await preview_and_options(update, context)
    
    elif query.data == 'choose_color':
        return await choose_color_step(update, context)
    elif query.data == 'choose_size':
        return await choose_size_step(update, context)
    elif query.data == 'choose_font':
        return await choose_font_step(update, context)

    return ConversationHandler.WAITING # Tetap di WAITING jika tidak ada state yang berubah

# Langkah 1: Menerima Teks
async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menerima teks dari pengguna dan menyimpan state."""
    text = update.message.text
    context.user_data['tgs_data']['text'] = text
    
    await update.message.reply_text(f'Teks diatur: **{text}**.', parse_mode='Markdown')
    context.user_data['current_step'] = TEXT
    return await preview_and_options(update, context)

# Langkah Lanjutan: Tampilkan Preview dan Pilihan Opsi
async def preview_and_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Membuat preview TGS dan menampilkan pilihan kustomisasi."""
    data = context.user_data['tgs_data']
    
    if not data['text']:
        await update.effective_message.reply_text("Teks belum diatur. Silakan kirimkan teks terlebih dahulu.")
        return TEXT
        
    try:
        # 1. GENERATE TGS (Simulasi)
        tgs_file = generate_lottie_json(
            text=data['text'],
            color=data['color'],
            size=data['size'],
            font_path=data['font'],
            config=TGS_CONFIG
        )
        tgs_file.seek(0)
        
        # 2. KIRIM PREVIEW
        caption = (
            "**PREVIEW EMOJI TGS ANDA**\n\n"
            f"Teks: `{data['text']}`\n"
            f"Warna: `{data['color']}` ({list(COLORS.keys())[list(COLORS.values()).index(data['color'])]})\n"
            f"Ukuran: `{data['size']}`\n"
            f"Font: `{data['font_name']}`\n\n"
            "Pilih opsi di bawah untuk mengubah:"
        )
        
        # 3. KIRIM OPSI KUSTOMISASI
        keyboard = [
            [InlineKeyboardButton("🎨 Pilih Warna", callback_data='choose_color'),
             InlineKeyboardButton("📏 Pilih Ukuran", callback_data='choose_size')],
            [InlineKeyboardButton("🔠 Pilih Font", callback_data='choose_font')],
            [InlineKeyboardButton("✅ Selesai (Tambahkan ke Set Stiker)", callback_data='finish')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Menggunakan send_sticker untuk mengirim file TGS
        # File harus berupa input stream
        await update.effective_message.reply_sticker(
            sticker=tgs_file,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.WAITING # Kembali ke state WAITING (untuk menunggu callback)
    
    except Exception as e:
        logging.error(f"Error creating TGS: {e}")
        await update.effective_message.reply_text(
            f"❌ Terjadi kesalahan saat membuat TGS: {e}. Pastikan teks valid."
        )
        return ConversationHandler.WAITING

# Langkah Opsi: Pilih Warna
async def choose_color_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tampilkan opsi pilihan warna."""
    keyboard = []
    for name, code in COLORS.items():
        keyboard.append([InlineKeyboardButton(f"Color: {name} ({code})", callback_data=f'set_color_{name}')])
    
    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Preview", callback_data='preview_back')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "Pilih salah satu warna di bawah:",
        reply_markup=reply_markup
    )
    return COLOR # Tetap di state Color

# Langkah Opsi: Pilih Ukuran
async def choose_size_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tampilkan opsi pilihan ukuran."""
    sizes = [50, 80, 100, 120, 150]
    keyboard = []
    row = []
    for size in sizes:
        row.append(InlineKeyboardButton(f"{size} px", callback_data=f'set_size_{size}'))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Preview", callback_data='preview_back')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "Pilih ukuran teks:",
        reply_markup=reply_markup
    )
    return SIZE # Tetap di state Size

# Langkah Opsi: Pilih Font
async def choose_font_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tampilkan opsi pilihan font."""
    keyboard = []
    for name in FONTS.keys():
        keyboard.append([InlineKeyboardButton(f"Font: {name}", callback_data=f'set_font_{name}')])
    
    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Preview", callback_data='preview_back')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "Pilih jenis font:",
        reply_markup=reply_markup
    )
    return FONT # Tetap di state Font

# Kembali ke Preview
async def back_to_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mengembalikan pengguna ke langkah preview setelah memilih opsi."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Memperbarui preview...")
    return await preview_and_options(update, context)

# Menangani Callback Finish (Selesai)
async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mengakhiri konversasi dan memberikan instruksi terakhir."""
    query = update.callback_query
    await query.answer()
    
    # Logic untuk membuat set stiker (biasanya lewat @Stickers bot) 
    # atau mengirim file TGS final
    
    await query.edit_message_text(
        "✅ **Proses Selesai!**\n\n"
        "TGS Anda sudah dibuat. Anda bisa menyimpan file stiker animasi di atas dan "
        "menggunakannya untuk membuat set stiker baru melalui @Stickers."
    )
    
    # Hapus data pengguna setelah selesai
    if 'tgs_data' in context.user_data:
        del context.user_data['tgs_data']
        
    return ConversationHandler.END # Mengakhiri ConversationHandler

# Fallback untuk membatalkan
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Membatalkan dan mengakhiri konversasi."""
    await update.message.reply_text('Pembuatan emoji dibatalkan. Silakan mulai lagi dengan /start.')
    if 'tgs_data' in context.user_data:
        del context.user_data['tgs_data']
    return ConversationHandler.END


# --- Fungsi Utama (Main) ---

def main() -> None:
    """Menjalankan bot."""
    application = Application.builder().token(TOKEN).build()

    # ConversationHandler untuk mengelola alur langkah demi langkah
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(handle_callback, pattern='^start_creation$')
        ],
        states={
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)],
            COLOR: [
                CallbackQueryHandler(handle_callback, pattern='^set_color_'),
                CallbackQueryHandler(back_to_preview, pattern='^preview_back$'),
            ],
            SIZE: [
                CallbackQueryHandler(handle_callback, pattern='^set_size_'),
                CallbackQueryHandler(back_to_preview, pattern='^preview_back$'),
            ],
            FONT: [
                CallbackQueryHandler(handle_callback, pattern='^set_font_'),
                CallbackQueryHandler(back_to_preview, pattern='^preview_back$'),
            ],
            ConversationHandler.WAITING: [ # State umum untuk menunggu callback setelah preview
                CallbackQueryHandler(handle_callback, pattern='^choose_color$'),
                CallbackQueryHandler(handle_callback, pattern='^choose_size$'),
                CallbackQueryHandler(handle_callback, pattern='^choose_font$'),
                CallbackQueryHandler(finish, pattern='^finish$'),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_preview, pattern='^preview_back$') # Fallback kembali dari menu pilihan
        ]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
