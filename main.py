import os
import json
import gzip
from io import BytesIO
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from fontTools.ttLib import TTFont

TOKEN = os.getenv("BOT_TOKEN")
FONT_DIR = "assets/fonts"

# -------------------- UTILITY --------------------
def glyph_to_lottie_path(font_path, char, size=512):
    """
    Ambil glyph outline dari font TTF, convert ke Lottie path
    """
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    if ord(char) not in cmap:
        char = '?'  # fallback
    glyph_name = cmap[ord(char)]
    glyph = font["glyf"][glyph_name]

    # Placeholder: rectangle path, harus diganti outline sebenarnya
    half = size/2
    path = {"i":[[0,0]]*4, "o":[[0,0]]*4, "v":[[-half,-half],[half,-half],[half,half],[-half,half]], "c":True}
    return path

def generate_lottie(text, font_file="Arial.ttf", font_color=(0,0,0), size=512, animation="fade_in"):
    r,g,b = [c/255 for c in font_color]
    layer_shapes = []
    for c in text:
        path = glyph_to_lottie_path(os.path.join(FONT_DIR,font_file), c, size=size)
        layer_shapes.append({"ty":"gr","it":[{"ty":"sh","ks":{"k":path}},{"ty":"fl","c":[r,g,b,1]}]})

    layer = {
        "ddd":0, "ind":1, "ty":4, "nm":text, "sr":1,
        "ks":{
            "o":{"a":1,"k":[{"t":0,"s":[0],"e":[100]},{"t":90}]} if animation=="fade_in" else 100,
            "p":{"a":0,"k":[size/2,size/2,0]},
            "s":{"a":1,"k":[{"t":0,"s":[0,0,100],"e":[100,100,100]},{"t":90}]} if animation=="scale" else [100,100,100],
            "r":{"a":0,"k":0}
        },
        "shapes": layer_shapes
    }

    lottie = {
        "v":"5.7.4","fr":30,"ip":0,"op":90,"w":size,"h":size,
        "nm":"emoji_animation","ddd":0,"assets":[],"layers":[layer]
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
    keyboard = [[InlineKeyboardButton("🖌️ Buat Emoji", callback_data="step_text")]]
    text = "✨ Welcome to Text Emoji Generator Bot ✨\nKlik tombol dibawah untuk mulai!"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ Kirim teks / emoji untuk dijadikan emoji.")
        return

    context.user_data["emoji_text"] = text
    context.user_data["current_step"] = "color"

    # preview awal
    color = context.user_data.get("font_color",(0,0,0))
    size = context.user_data.get("size",512)
    anim = context.user_data.get("animation_type","fade_in")
    font_file = context.user_data.get("font_file","Arial.ttf")
    lottie_json = generate_lottie(text, font_file=font_file, font_color=color, size=size, animation=anim)
    tgs_file = generate_tgs(lottie_json)
    await update.message.reply_sticker(sticker=InputFile(tgs_file, filename="emoji.tgs"))

    # step pilih warna
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

    if data=="step_text":
        context.user_data["current_step"]="text"
        await query.edit_message_text("📤 Silakan kirim teks / emoji untuk dijadikan emoji TGS:")
        return

    if data.startswith("color_") and current=="color":
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

    if data.startswith("anim_") and current=="animation":
        anim = data.split("_")[1]
        context.user_data["animation_type"] = anim
        context.user_data["current_step"]="preview"
        # preview final
        text = context.user_data.get("emoji_text","")
        color = context.user_data.get("font_color",(0,0,0))
        anim = context.user_data.get("animation_type","fade_in")
        size = context.user_data.get("size",512)
        font_file = context.user_data.get("font_file","Arial.ttf")
        lottie_json = generate_lottie(text, font_file=font_file, font_color=color, size=size, animation=anim)
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
