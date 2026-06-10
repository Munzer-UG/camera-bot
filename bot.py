import os
import speech_recognition as sr
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import logging

logging.basicConfig(level=logging.INFO)

# === إعداداتك ===
TOKEN = os.environ.get("TOKEN")
CHANNELS = ["@sodan249"]
SUPPORT_LINK = "https://t.me/U_MP_7"
ADMIN_ID = 8743242936

recognizer = sr.Recognizer()
BOT_PAUSED = False

LANGUAGES = {
    "ar": "🇸🇦 عربي",
    "en": "🇬🇧 English",
    "fr": "🇫🇷 Français",
    "es": "🇪🇸 Español",
}

LANGUAGE_CODES = {
    "ar": "ar",
    "en": "en",
    "fr": "fr",
    "es": "es",
}

async def is_subscribed(context, user_id):
    try:
        member = await context.bot.get_chat_member(CHANNELS[0], user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_subscribed(context, user_id) or user_id == ADMIN_ID:
        await welcome_message(update, context)
        return

    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة", url="https://t.me/sodan249")],
        [InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 **مرحبا!** اشترك أولاً ثم /start", reply_markup=reply_markup)

async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [[InlineKeyboardButton("🎙️ أرسل صوت الآن", callback_data="voice_mode")]]
    
    if user_id == ADMIN_ID:
        status = "⏸️ متوقف" if BOT_PAUSED else "▶️ شغال"
        keyboard.append([InlineKeyboardButton(f"{status}", callback_data="toggle_pause")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"✅ **البوت {'متوقف' if BOT_PAUSED else 'شغال'}**\n\n🎤 أرسل صوت → نص!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_PAUSED
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "toggle_pause" and user_id == ADMIN_ID:
        BOT_PAUSED = not BOT_PAUSED
        await welcome_message(update, context)
        return

    if data == "voice_mode":
        await query.edit_message_text("🎙️ **أرسل الرسالة الصوتية الآن...**")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_PAUSED
    user_id = update.effective_user.id

    if BOT_PAUSED and user_id != ADMIN_ID:
        await update.message.reply_text("⏸️ البوت متوقف.")
        return

    if not await is_subscribed(context, user_id) and user_id != ADMIN_ID:
        await start(update, context)
        return

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    msg = await update.message.reply_text("⏳ جاري تحويل الصوت...")

    try:
        file = await context.bot.get_file(voice.file_id)
        ogg_path = f"voice_{user_id}.ogg"
        await file.download_to_drive(ogg_path)

        with sr.AudioFile(ogg_path) as source:
            audio_data = recognizer.record(source)
            text = None
            
            # Try Arabic first
            try:
                text = recognizer.recognize_google(audio_data, language="ar-SA")
            except:
                try:
                    text = recognizer.recognize_google(audio_data, language="en-US")
                except:
                    pass

            if not text:
                await msg.edit_text("❌ ما قدرت أحول الصوت.\nجرب صوت أوضح.")
                return

            await msg.edit_text(f"**✅ النص:**\n\n{text}")

    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:100]}")
    finally:
        if os.path.exists(ogg_path):
            os.remove(ogg_path)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
