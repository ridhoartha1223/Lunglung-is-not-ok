import os
import json
import gzip
from io import BytesIO
from PIL import ImageFont, ImageDraw
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# -------------------- UTILITY: TEXT → SHAPE --------------------
def text_to_shape_placeholder(text, size=512):
    """
    Placeholder: convert text to simple rectangle path.
    For production, replace with vector paths from font/emoji.
    """
    half = size/2
    path = {
        "i": [[0,0]]*4,
        "o": [[0,0]]*4,
        "v": [[-half,-half],[half,-half],[half,half],[-half,half]],
        "c": True
    }
    return path

def generate_lottie_shape(text, font_color=(0,0,0), size=512, animation_type="fade_in"):
    r,g,b = [c/255 for c in font_color]
    shape_path = text_to_shape_placeholder(text, size=size)

    # layer
    layer = {
        "ddd":0,
        "ind":1,
        "ty":4,
        "nm":text,
        "sr":1,
        "ks":{
            "o":{"a":1,"k":[{"t":0,"s":[0],"e":[100]},{"t":90}]} if animation_type=="fade_in" else 100,
            "p":{"a":0,"k":[size/2,size/2,0]},
            "s":{"a":1,"k":[{"t":0,"s":[0,0,100],"e":[100,100,100]},{"t":90}]} if animation_type=="scale" else [100,100,100],
            "r":{"a":0,"k":0}
        },
        "shapes":[{"ty":"gr","it":[{"ty":"sh","ks":{"k":shape_path}},{"ty":"fl","c":[r,g,b,1]}]}]
    }

    lottie = {
        "v":"5.7.4",
        "fr":30,
        "ip":0,
        "op":90,
        "w":size,
        "h":size,
        "nm":"emoji_animation",
        "ddd":0,
        "assets":[],
        "layers":[layer]
    }
    return lottie

def generate_tgs(lottie_json):
    out = BytesIO()
    with gzip.GzipFile(fileobj=out, mode="w") as f:
        f.write(json.dumps(lottie_json).encode("utf-8"))
    out.seek(0)
    out.name="emoji.tgs"
    return out

# -------------------- WIZARD --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🖌️ Buat Emoji TGS", callback_data="step_text")]]
    await update.message.reply_text("✨ Wizard Animated Emoji `.tgs` ✨", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["emoji_text"] = update.message.text.strip()
    context.user_data["current_step"]="color"
    keyboard = [
        [InlineKeyboardButton("⬛ Hitam", callback_data="color_0_0_0"),
         InlineKeyboardButton("⬜ Putih", callback_data="color_255_255_255")],
        [InlineKeyboardButton("🔴 Merah", callback_data="color_255_0_0")]
    ]
    await update.message.reply_text("🎨 Pilih warna:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    current = context.user_data.get("current_step","text")

    # Color
    if data.startswith("color_"):
        r,g,b = map(int,data.split("_")[1:])
        context.user_data["font_color"] = (r,g,b)
        context.user_data["current_step"]="animation"
        keyboard = [
            [InlineKeyboardButton("Fade In", callback_data="anim_fade_in"),
             InlineKeyboardButton("Scale", callback_data="anim_scale"),
             InlineKeyboardButton("Slide", callback_data="anim_slide")]
        ]
        await query.edit_message_text("🎬 Pilih animasi:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Animation
    if data.startswith("anim_") and current=="animation":
        anim = data.split("_")[1]
        context.user_data["animation_type"] = anim
        context.user_data["current_step"]="create"
        await query.edit_message_text("✅ Semua siap, tekan tombol untuk generate TGS",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Generate TGS", callback_data="create_tgs")]]))
        return

    # Create TGS
    if data=="create_tgs" and current=="create":
        text = context.user_data.get("emoji_text","")
        color = context.user_data.get("font_color",(0,0,0))
        anim = context.user_data.get("animation_type","fade_in")
        lottie_json = generate_lottie_shape(text,color,size=512,animation_type=anim)
        tgs_file = generate_tgs(lottie_json)
        await query.message.reply_sticker(sticker=InputFile(tgs_file, filename="emoji.tgs"))

# -------------------- MAIN --------------------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__=="__main__":
    main()
