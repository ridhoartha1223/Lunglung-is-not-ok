import os
import gzip
import json
from io import BytesIO
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# -------------------- UTILITIES --------------------
def generate_tgs(text: str, animation_type="fade_in", size=512) -> BytesIO:
    """
    Generate a simple Lottie JSON animation with text
    Supported animation_type: fade_in, bounce, scale
    """
    # Simplified Lottie structure
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
                    "o": {"a":1, "k":[{"t":0,"s":[0],"e":[100],"i":{"x":[0.667],"y":[1]},"o":{"x":[0.333],"y":[0]}},{"t":30}] if animation_type=="fade_in" else 100},
                    "p": {"a":0, "k":[size/2, size/2,0]},
                    "s": {"a":1, "k":[
                        {"t":0,"s":[0,0,100],"e":[100,100,100],"i":{"x":[0.667,0.667,0.667],"y":[1,1,1]},"o":{"x":[0.333,0.333,0.333],"y":[0,0,0]}}] if animation_type=="scale" else [100,100,100]},
                    "r": {"a":0, "k":0}
                },
                "t": {"d": {"k": [{"s":{"sz":[size,size],"ps":[0,0],"s":50,"f":"Arial","t":text,"j":2,"tr":0,"lh":60,"fc":[1,1,1]},"t":0}]}},
                "ao": 0
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

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("current_step") != "text":
        await update.message.reply_text("❌ Tunggu, wizard masih berjalan.")
        return
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ Kirim teks atau emoji!")
        return
    context.user_data["emoji_text"] = text
    context.user_data["current_step"] = "animation"
    await send_animation_step(update.callback_query if update.callback_query else update, context)

async def send_animation_step(query, context):
    keyboard = [
        [InlineKeyboardButton("Fade In", callback_data="anim_fade_in")],
        [InlineKeyboardButton("Bounce", callback_data="anim_bounce")],
        [InlineKeyboardButton("Scale", callback_data="anim_scale")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_text")]
    ]
    text = f"🎨 Pilih efek animasi:\n`{context.user_data.get('emoji_text','')}`"
    if isinstance(query, Update):
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

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

    # MENU
    if data == "help":
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="start")]]
        await query.edit_message_text("ℹ️ Panduan: Ikuti wizard untuk membuat emoji animasi.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data == "start":
        await start(update, context)
        return
    elif data in ["step_text","back_text"]:
        context.user_data["current_step"]="text"
        await query.edit_message_text("📤 Kirim teks/emoji:")
        return

    # ANIMATION STEP
    elif data.startswith("anim_") and context.user_data.get("current_step")=="animation":
        anim_type = data.split("_")[1]
        context.user_data["animation_type"] = anim_type
        context.user_data["current_step"] = "create"
        await send_create_step(query, context)
    elif data == "back_animation" and context.user_data.get("current_step")=="create":
        context.user_data["current_step"]="animation"
        await send_animation_step(query, context)

    # CREATE STEP
    elif data == "create_emoji" and context.user_data.get("current_step")=="create":
        text = context.user_data.get("emoji_text","")
        anim_type = context.user_data.get("animation_type","fade_in")
        tgs_file = generate_tgs(text, animation_type=anim_type)
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
