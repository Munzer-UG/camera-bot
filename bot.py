import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

# الحصول على التوكن من متغير البيئة
TOKEN = os.environ.get("TOKEN")

# إذا لم يكن هناك توكن، استخدم توكن افتراضي للاختبار
if not TOKEN:
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر البدء"""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🎙️ تحويل صوت", callback_data="info")],
        [InlineKeyboardButton("📞 تواصل معنا", url="https://t.me/U_MP_7")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 مرحبا {user.first_name}!\n\n"
        f"✨ أنا بوت تحويل الصوت إلى نص\n"
        f"🎤 أرسل لي رسالة صوتية وسأحولها إلى نص\n\n"
        f"📢 الميزات:\n"
        f"✅ تحويل صوت لنص\n"
        f"✅ دعم لغات متعددة\n"
        f"✅ سريع وموثوق",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر المساعدة"""
    help_text = (
        "🆘 **الأوامر المتاحة:**\n\n"
        "/start - ابدأ هنا\n"
        "/help - الأوامر المتاحة\n\n"
        "🎤 **طريقة الاستخدام:**\n"
        "1️⃣ أرسل رسالة صوتية\n"
        "2️⃣ سأحولها إلى نص\n"
        "3️⃣ استمتع بالنتيجة!\n\n"
        "📧 **هل عندك مشكلة؟**\n"
        "@U_MP_7"
    )
    await update.message.reply_text(help_text)

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل الصوتية"""
    if update.message.voice or update.message.audio:
        await update.message.reply_text(
            "✅ استقبلت الرسالة الصوتية\n\n"
            "📝 ملاحظة: هذه نسخة تجريبية\n"
            "🔧 التحديثات قريباً\n\n"
            "شكراً لاستخدامك البوت! 🙏"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    logging.error(f"Update {update} caused error {context.error}")

def main():
    """الدالة الرئيسية"""
    if not TOKEN:
        print("⚠️ تحذير: لم يتم تعيين TOKEN")
        print("البوت سيحاول الاتصال... إذا فشل، أضف TOKEN في Render")
        return
    
    # إنشء التطبيق
    app = Application.builder().token(TOKEN).build()
    
    # إضافة معالجات الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # معالج الرسائل الصوتية
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_message_handler))
    
    # معالج الأخطاء
    app.add_error_handler(error_handler)
    
    print("🚀 البوت يعمل الآن...")
    print("🎧 في انتظار الرسائل الصوتية...")
    
    # بدء البوت
    app.run_polling()

if __name__ == "__main__":
    main()
