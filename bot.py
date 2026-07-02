#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MUNZER SERVER BOT - Render 24/7
# المطور: The Architect

import os
import sys
import time
import threading
from datetime import datetime
from flask import Flask, jsonify
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== سيرفر Flask (عشان Render ما يوقفش) ==========
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>MUNZER Server</title>
    <style>body{background:#000;color:#f00;text-align:center;padding-top:100px;font-family:Arial;}
    h1{font-size:50px;}</style></head>
    <body><h1>MUNZER SERVER</h1><p>Online 24/7</p></body></html>
    """

@app.route('/health')
def health():
    return jsonify({'status': 'online', 'time': datetime.now().isoformat()})

@app.route('/ping')
def ping():
    return 'pong'

# ========== بوت تيليجرام ==========
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set!")

bot = TeleBot(TOKEN)
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

start_time = time.time()

# ========== أوامر البوت ==========
def escape_markdown(text):
    """يشيل/يهرب الرموز اللي ممكن تكسر تنسيق Markdown في تيليجرام"""
    if not text:
        return ""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#',
                      '+', '-', '=', '|', '{', '}', '.', '!']
    for ch in special_chars:
        text = text.replace(ch, '')
    return text

@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    safe_name = escape_markdown(user.first_name)

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 الحالة", callback_data="status"),
        InlineKeyboardButton("ℹ️ معلومات", callback_data="info"),
    )

    bot.send_message(message.chat.id, f"""
⚡ *MUNZER SERVER BOT*

مرحباً {safe_name}
السيرفر شغال 24 ساعة على Render

*الأوامر:*
/start - القائمة الرئيسية
/status - حالة السيرفر
/info - معلومات
/ping - فحص الاتصال
/time - الوقت الحالي
""", parse_mode='Markdown', reply_markup=kb)

@bot.message_handler(commands=['status'])
def status_command(message):
    uptime = time.time() - start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)

    bot.send_message(message.chat.id, f"""
📊 *حالة السيرفر*

✅ *Online*
⏱ *Uptime:* {hours}h {minutes}m
🕐 *الوقت:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 *المنصة:* Render
""", parse_mode='Markdown')

@bot.message_handler(commands=['info'])
def info_command(message):
    bot.send_message(message.chat.id, f"""
ℹ️ *معلومات السيرفر*

🏷 *الاسم:* MUNZER SERVER
👤 *المطور:* The Architect
🐍 *Python:* {sys.version.split()[0]}
🌐 *Flask:* شغال
🤖 *البوت:* شغال
📡 *Render:* 24/7
""", parse_mode='Markdown')

@bot.message_handler(commands=['ping'])
def ping_command(message):
    start = time.time()
    msg = bot.send_message(message.chat.id, "🏓 Pinging...")
    end = time.time()
    ping_time = round((end - start) * 1000, 2)

    bot.edit_message_text(f"🏓 *Pong!*\n⚡ `{ping_time}ms`",
                          message.chat.id, msg.message_id, parse_mode='Markdown')

@bot.message_handler(commands=['time'])
def time_command(message):
    now = datetime.now()
    bot.send_message(message.chat.id, f"""
🕐 *الوقت الحالي*

📅 *التاريخ:* {now.strftime('%Y-%m-%d')}
⏰ *الوقت:* {now.strftime('%H:%M:%S')}
🌍 *UTC:* {datetime.utcnow().strftime('%H:%M:%S')}
""", parse_mode='Markdown')

# ========== أزرار ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'status':
        status_command(call.message)
    elif call.data == 'info':
        info_command(call.message)

    bot.answer_callback_query(call.id)

# ========== تشغيل البوت في خلفية (Thread منفصل) ==========
def run_bot_polling():
    print("[✓] Telegram Bot Started")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"[!] Error: {e}")
            time.sleep(10)

# هذا الجزء بيشتغل سواء عبر "python bot.py" مباشرة أو عبر Gunicorn،
# لأن Gunicorn بيستورد الملف بس ما بيشغّل __main__.
bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
bot_thread.start()

# ========== تشغيل مباشر (للتجربة المحلية فقط) ==========
if __name__ == '__main__':
    print("""
╔══════════════════════════════════╗
║   MUNZER SERVER BOT             ║
║   Running on Render 24/7        ║
║   المطور: The Architect          ║
╚══════════════════════════════════╝
    """)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
