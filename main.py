import os
import gzip
import json
from io import BytesIO
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# -------------------- UTILITIES --------------------
def generate_tgs(text: str, font_color, font_name, size, animation_type="fade_in") -> BytesIO:
    """
    Generate a Lottie (.tgs) with transparent background
    text: emoji/text
    font_color: (r,g,b) 0-1
    font_name: string (Telegram font, e.g., NotoColorEmoji)
    size: canvas size in px
    animation_type: fade_in / bounce / scale
    """
    r,g,b = font_color
    # Minimal text layer
    o_anim = [{"t":0,"s":[0],"e":[100],"i":{"x":[0.667],"y":[1]},"o":{"x":[0.333],"y":[0]}},{"t":30}] if animation_type=="fade_in" else 100
    s_anim = [{"t":0,"s":[0,0,100],"e":[100,100,100],"i":{"x":[0.667,0.667,0.667],"y":[1,1,1]},"o":{"x":[0.333,0.333,0.333],"y":[0,0,0]}}] if animation_type=="scale" else [100,100,100]

    lottie_json = {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": 60,
        "w": size,
        "h": size,
        "nm": "emoji_animation",
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
                    "o": {"a":1, "k": o_anim},
                    "p": {"a":0, "k":[size/2, size/2,0]},
                    "s": {"a":1, "k": s_anim},
                    "r": {"a":0,"k":0}
                },
                "t": {
                    "d": {"k":[{"s":{"sz":[size,size],"ps":[0,0],"s":int(size*0.5),
                                    "f":font_name,"t":text,"j":2,"tr":0,"lh":int(size*0.5),"fc":[r,g,b]},
                               "t":0}]}
                },
                "ao":0
            }
        ]
    }

    out = BytesIO()
    with gzip.GzipFile(fileobj=out, mode='w') as f:
        f.write(json.dumps(lottie_json).encode('utf-8'))
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
        "✨ *Ultimate Animated Emoji Bot!* ✨\nBuat emoji custom step-by-step dengan animasi.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---- TEXT STEP ----
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("current_step") != "text":
        await update.message.reply_text("❌ Tunggu, wizard masih berjalan.")
        return
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ Kirim teks atau emoji!")
        return
    context.user_data["emoji_text"] = text
    context.user_data["current_step"] = "color"
    await send_color_step(update, context)

# ---- COLOR STEP ----
async def send_color_step(update, context):
    keyboard = [
        [InlineKeyboardButton("⬛ Hitam", callback_data="color_0_0_0"),
         InlineKeyboardButton("⬜ Putih", callback_data="color_1_1_1")],
        [InlineKeyboardButton("🔴 Merah", callback_data="color_1_0_0"),
         InlineKeyboardButton("🟢 Hijau", callback_data="color_0_1_0")],
        [InlineKeyboardButton("🔵 Biru", callback_data="color_0_0_1")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_text")]
    ]
    if isinstance(update, Update):
        await update.message.reply_text("🎨 Pilih warna teks:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.edit_message_text("🎨 Pilih warna teks:", reply_markup=InlineKeyboardMarkup(keyboard))

# ---- FONT STEP ----
async def send_font_step(query, context):
    keyboard = [
        [InlineKeyboardButton("NotoColorEmoji", callback_data="font_NotoColorEmoji"),
         InlineKeyboardButton("Arial", callback_data="font_Arial")],
        [InlineKeyboardButton("Comic Sans", callback_data="font_ComicSans"),
         InlineKeyboardButton("Impact", callback_data="font_Impact")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_color")]
    ]
    await query.edit_message_text("🖋️ Pilih font:", reply_markup=InlineKeyboardMarkup(keyboard))

# ---- SIZE STEP ----
async def send_size_step(query, context):
    keyboard = [
        [InlineKeyboardButton("256 px", callback_data="size_256"),
         InlineKeyboardButton("512 px", callback_data="size_512"),
         InlineKeyboardButton("1024 px", callback_data="size_1024")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_font")]
    ]
    await query.edit_message_text("📐 Pilih ukuran canvas:", reply_markup=InlineKeyboardMarkup(keyboard))

# ---- ANIMATION STEP ----
async def send_animation_step(query, context):
    keyboard = [
        [InlineKeyboardButton("Fade In", callback_data="anim_fade_in"),
         InlineKeyboardButton("Bounce", callback_data="anim_bounce"),
         InlineKeyboardButton("Scale", callback_data="anim_scale")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_size")]
    ]
    await query.edit_message_text("🎬 Pilih efek animasi:", reply_markup=InlineKeyboardMarkup(keyboard))

# ---- CREATE STEP ----
async def send_create_step(query, context):
    keyboard = [
        [InlineKeyboardButton("✅ Buat Emoji Animasi", callback_data="create_emoji")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_animation")]
    ]
    text = context.user_data.get("emoji_text","")
    await query.edit_message_text(f"📌 Semua opsi siap!\nTeks: `{text}`\nTekan ✅ untuk buat emoji animasi.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# -------------------- CALLBACK HANDLER --------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    current = context.user_data.get("current_step","text")

    # MENU
    if data == "help":
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="start")]]
        await query.edit_message_text("ℹ️ Panduan wizard.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data == "start":
        await start(update, context)
        return

    # TEXT
    elif data in ["step_text","back_text"]:
        context.user_data["current_step"]="text"
        await query.edit_message_text("📤 Kirim teks/emoji:")
        return

    # COLOR
    elif data.startswith("color_") and current=="color":
        r,g,b = map(float, data.split("_")[1:])
        context.user_data["font_color"] = (r,g,b)
        context.user_data["current_step"]="font"
        await send_font_step(query, context)
    elif data=="back_color" and current=="font":
        context.user_data["current_step"]="color"
        await send_color_step(query, context)

    # FONT
    elif data.startswith("font_") and current=="font":
        font_name = data.split("_")[1]
        context.user_data["font_name"] = font_name
        context.user_data["current_step"]="size"
        await send_size_step(query, context)
    elif data=="back_font" and current=="size":
        context.user_data["current_step"]="font"
        await send_font_step(query, context)

    # SIZE
    elif data.startswith("size_") and current=="size":
        size = int(data.split("_")[1])
        context.user_data["size"] = size
        context.user_data["current_step"]="animation"
        await send_animation_step(query, context)
    elif data=="back_size" and current=="animation":
        context.user_data["current_step"]="size"
        await send_size_step(query, context)

    # ANIMATION
    elif data.startswith("anim_") and current=="animation":
        anim_type = data.split("_")[1]
        context.user_data["animation_type"]=anim_type
        context.user_data["current_step"]="create"
        await send_create_step(query, context)
    elif data=="back_animation" and current=="create":
        context.user_data["current_step"]="animation"
        await send_animation_step(query, context)

    # CREATE
    elif data=="create_emoji" and current=="create":
        text = context.user_data.get("emoji_text","")
        font_color = context.user_data.get("font_color",(0,0,0))
        font_name = context.user_data.get("font_name","NotoColorEmoji")
        size = context.user_data.get("size",512)
        anim_type = context.user_data.get("animation_type","fade_in")

        tgs_file = generate_tgs(text, font_color, font_name, size, anim_type)
        await query.message.reply_sticker(sticker=InputFile(tgs_file, filename="emoji.tgs"))
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
