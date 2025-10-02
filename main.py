import os
import json
from io import BytesIO
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# -------------------- UTILITIES --------------------
def generate_json(text: str, font_color=(0,0,0), font_name="assets/fonts/NotoColorEmoji.ttf", size=512, animation_type="fade_in") -> BytesIO:
    # konversi warna 0-255 ke 0-1
    r,g,b = [c/255 for c in font_color]

    # keyframe opacity dan scale untuk animasi 3 detik
    if animation_type=="fade_in":
        o_anim = [{"t":0,"s":[0],"e":[100],"i":{"x":[0.667],"y":[1]},"o":{"x":[0.333],"y":[0]}},{"t":90}]
        s_anim = [{"t":0,"s":[100,100,100],"e":[100,100,100]}]  # tetap
    elif animation_type=="scale":
        o_anim = 100
        s_anim = [{"t":0,"s":[0,0,100],"e":[100,100,100],"i":{"x":[0.667]*3,"y":[1]*3},"o":{"x":[0.333]*3,"y":[0]*3}}, {"t":90}]
    elif animation_type=="slide":
        o_anim = 100
        s_anim = [{"t":0,"s":[100,100,100],"e":[100,100,100]}]
    else:
        o_anim = 100
        s_anim = [{"t":0,"s":[100,100,100],"e":[100,100,100]}]

    layer = {
        "ddd":0,
        "ind":1,
        "ty":5,  # text layer
        "nm":text,
        "sr":1,
        "ks":{
            "o":{"a":1,"k": o_anim},
            "p":{"a":0,"k":[size/2,size/2,0]},
            "s":{"a":1,"k": s_anim},
            "r":{"a":0,"k":0}
        },
        "t":{"d":{"k":[{"s":{"sz":[size,size],"ps":[0,0],"s":int(size*0.5),
                        "f":font_name,"t":text,"j":2,"tr":0,"lh":int(size*0.5),"fc":[r,g,b]},
                        "t":0}]}}
    }

    lottie = {
        "v":"5.7.4",
        "fr":30,
        "ip":0,
        "op":90,   # 3 detik
        "w":size,
        "h":size,
        "nm":"emoji_animation",
        "ddd":0,
        "assets":[],
        "layers":[layer]
    }

    out = BytesIO()
    out.write(json.dumps(lottie, indent=2).encode("utf-8"))
    out.seek(0)
    out.name = "emoji.json"
    return out

# -------------------- STEP FUNCTIONS --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖌️ Buat Emoji JSON", callback_data="step_text")],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="help")]
    ]
    await update.message.reply_text(
        "✨ *Animated Emoji JSON Wizard!* ✨\nBuat emoji step-by-step.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("current_step") != "text":
        await update.message.reply_text("❌ Tunggu, wizard masih berjalan.")
        return
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ Kirim teks/emoji!")
        return
    context.user_data["emoji_text"] = text
    context.user_data["current_step"] = "color"
    await send_color_step(update, context)

async def send_color_step(update, context):
    keyboard = [
        [InlineKeyboardButton("⬛ Hitam", callback_data="color_0_0_0"),
         InlineKeyboardButton("⬜ Putih", callback_data="color_255_255_255")],
        [InlineKeyboardButton("🔴 Merah", callback_data="color_255_0_0"),
         InlineKeyboardButton("🟢 Hijau", callback_data="color_0_255_0")],
        [InlineKeyboardButton("🔵 Biru", callback_data="color_0_0_255")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_text")]
    ]
    if isinstance(update, Update):
        await update.message.reply_text("🎨 Pilih warna teks:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.edit_message_text("🎨 Pilih warna teks:", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_font_step(query, context):
    font_files = os.listdir("assets/fonts")
    keyboard = []
    row = []
    for f in font_files:
        row.append(InlineKeyboardButton(f.replace(".ttf",""), callback_data=f"font_{f}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_color")])
    await query.edit_message_text("🖋️ Pilih font:", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_animation_step(query, context):
    keyboard = [
        [InlineKeyboardButton("Fade In", callback_data="anim_fade_in"),
         InlineKeyboardButton("Scale", callback_data="anim_scale"),
         InlineKeyboardButton("Slide", callback_data="anim_slide")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_size")]
    ]
    await query.edit_message_text("🎬 Pilih animasi:", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_create_step(query, context):
    keyboard = [[InlineKeyboardButton("✅ Buat JSON", callback_data="create_json")]]
    await query.edit_message_text("📌 Semua opsi siap! Tekan ✅ untuk generate JSON.", reply_markup=InlineKeyboardMarkup(keyboard))

# -------------------- CALLBACK HANDLER --------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    current = context.user_data.get("current_step","text")

    # Help
    if data=="help":
        await query.edit_message_text("ℹ️ Wizard buat animasi text emoji JSON.", reply_markup=None)
        return
    elif data=="step_text":
        context.user_data["current_step"]="text"
        await query.edit_message_text("📤 Kirim teks/emoji:")
        return

    # Color
    elif data.startswith("color_"):
        r,g,b = map(int,data.split("_")[1:])
        context.user_data["font_color"] = (r,g,b)
        context.user_data["current_step"]="font"
        await send_font_step(query, context)
        return
    elif data=="back_text":
        context.user_data["current_step"]="text"
        await query.edit_message_text("📤 Kirim teks/emoji:")
        return

    # Font
    elif data.startswith("font_") and current=="font":
        font_file = data.split("_",1)[1]
        context.user_data["font_name"] = f"assets/fonts/{font_file}"
        context.user_data["current_step"]="animation"
        await send_animation_step(query, context)
    elif data=="back_color" and current=="animation":
        context.user_data["current_step"]="color"
        await send_color_step(query, context)

    # Animation
    elif data.startswith("anim_") and current=="animation":
        anim_type = data.split("_")[1]
        context.user_data["animation_type"]=anim_type
        context.user_data["current_step"]="create"
        await send_create_step(query, context)
    elif data=="back_size" and current=="create":
        context.user_data["current_step"]="animation"
        await send_animation_step(query, context)

    # Create JSON
    elif data=="create_json" and current=="create":
        text = context.user_data.get("emoji_text","")
        font_color = context.user_data.get("font_color",(0,0,0))
        font_name = context.user_data.get("font_name","assets/fonts/NotoColorEmoji.ttf")
        size = 512
        anim_type = context.user_data.get("animation_type","fade_in")

        json_file = generate_json(text, font_color, font_name, size, anim_type)
        await query.message.reply_document(document=InputFile(json_file, filename="emoji.json"))

# -------------------- MAIN --------------------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__=="__main__":
    main()
