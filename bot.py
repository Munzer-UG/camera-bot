import os
import speech_recognition as sr
from pydub import AudioSegment
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import logging
from googletrans import Translator

logging.basicConfig(level=logging.INFO)

# === إعدادات ===
TOKEN = "8455579008:AAFSURd26X8pl53AmO8ypH_8VKCmjX8u1A4"
CHANNELS = ["@sodan249", "https://t.me/+KyoM7mvMKAJiYjlk"]
SUPPORT_LINK = "https://t.me/U_MP_7"
ADMIN_ID = 8743242936

recognizer = sr.Recognizer()
translator = Translator()
BOT_PAUSED = False

LANGUAGES = {
    "ar": "🇸🇦 عربي", "en": "🇺🇸 English", "fr": "🇫🇷 Français",
    "es": "🇪🇸 Español", "ru": "🇷🇺 Русский", "de": "🇩🇪 German",
    "tr": "🇹🇷 Türkçe", "zh-cn": "🇨🇳 Chinese", "ja": "🇯🇵 Japanese"
}

async def is_subscribed(context, user_id):
    for ch in CHANNELS:
        try:
            if ch.startswith("https://t.me/+"):
                chat = await context.bot.get_chat(ch)
                member = await context.bot.get_chat_member(chat.id, user_id)
            else:
                member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ["member", "administrator", "creator"]:
                return True
        except:
            continue
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_subscribed(context, update.effective_user.id):
        await welcome_message(update, context)
    else:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة", url="https://t.me/sodan249")],
            [InlineKeyboardButton("👥 اشترك في المجموعة", url="https://t.me/+KyoM7mvMKAJiYjlk")],
            [InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_LINK)]
        ]
        await update.message.reply_text(
            "👋 **مرحبا بك في Voice Translate Pro**\n\n"
            "⚠️ يجب الاشتراك في القناة والمجموعة أولاً ثم اضغط /start",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎙️ ترجمة صوتية", callback_data="voice_mode")],
        [InlineKeyboardButton("🛠️ الدعم الفني", url=SUPPORT_LINK)]
    ]
    if update.effective_user.id == ADMIN_ID:
        status = "⏸️ متوقف" if BOT_PAUSED else "▶️ شغال"
        keyboard.insert(1, [InlineKeyboardButton(f"{status} - إيقاف/تشغيل", callback_data="toggle_pause")])
    
    await update.message.reply_text(
        "✅ **Voice Translate Pro شغال بقوة**\n\n"
        "🎙️ أرسل صوت أو فيديو أو نص واختر اللغة\n"
        "🌍 دعم أكثر من 100 لغة",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_PAUSED
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "toggle_pause" and user_id == ADMIN_ID:
        BOT_PAUSED = not BOT_PAUSED
        await welcome_message(update, context)
        return

    if data == "voice_mode":
        await query.edit_message_text("🎙️ أرسل الرسالة الصوتية الآن...")

    if data.startswith("translate_"):
        target = data.split("_")[1]
        text = context.user_data.get("last_text", "")
        if text:
            try:
                translated = translator.translate(text, dest=target).text
                await query.edit_message_text(f"**✅ الترجمة إلى {LANGUAGES.get(target)}:**\n\n{translated}")
            except:
                await query.edit_message_text("❌ خطأ في الترجمة")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_PAUSED
    user_id = update.effective_user.id

    if BOT_PAUSED and user_id != ADMIN_ID:
        await update.message.reply_text("⏸️ البوت متوقف من الإدارة.")
        return

    if not await is_subscribed(context, user_id):
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

        wav_path = f"voice_{user_id}.wav"
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")

        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = None
            for lang in ["ar-SA", "en-US", "fr-FR", "es-ES", "ru-RU"]:
                try:
                    text = recognizer.recognize_google(audio_data, language=lang)
                    if text and text.strip():
                        break
                except:
                    continue

            if not text:
                await msg.edit_text("❌ ما قدرت أحول الصوت.\nجرب صوت أوضح.")
                return

            context.user_data["last_text"] = text
            await msg.edit_text(f"**✅ النص الأصلي:**\n{text}\n\nاختر لغة الترجمة:")

            keyboard = [[InlineKeyboardButton(LANGUAGES[lang], callback_data=f"translate_{lang}") for lang in LANGUAGES]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("🔄 اختر اللغة:", reply_markup=reply_markup)

    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:200]}")
    finally:
        for f in [ogg_path, wav_path]:
            if os.path.exists(f):
                os.remove(f)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🚀 Voice Translate Pro شغال بقوة...")
    app.run_polling()

if __name__ == "__main__":
    main()