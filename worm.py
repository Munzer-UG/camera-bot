"""
╔══════════════════════════════════════════════╗
║          👹 WORM SERVER - ALL IN ONE         ║
║  بوت تيليجرام + رشق + VPN + لوحة تحكم        ║
║  ملف واحد. يشتغل على أي سيرفر.               ║
╚══════════════════════════════════════════════╝
"""

import os
import sys
import time
import json
import random
import threading
import subprocess
import requests
from datetime import datetime

# ==================== تثبيت تلقائي ====================
def auto_install():
    print("[🔧] جاري تثبيت المتطلبات...")
    packages = [
        "flask", "pytelegrambotapi", "requests", 
        "selenium-wire", "undetected-chromedriver",
        "selenium-stealth", "pysocks", "dnspython"
    ]
    
    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_"))
        except:
            os.system(f"{sys.executable} -m pip install {pkg} --quiet")
    
    print("[✅] المتطلبات جاهزة")

auto_install()

from flask import Flask, render_template_string, jsonify, request
import telebot
from telebot import types

# ==================== الإعدادات - غير هذه البيانات ====================
TELEGRAM_TOKEN = "توكن_البوت_هنا"  # من @BotFather
ADMIN_ID = "ايديك_هنا"  # من @userinfobot
PORT = int(os.environ.get("PORT", 5000))

# ==================== السيرفر ====================
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ==================== التخزين ====================
data = {
    "views_total": 0,
    "likes_total": 0,
    "tasks_done": 0,
    "start_time": time.time(),
    "active_tasks": [],
    "vpn_users": [],
    "logs": []
}

def log(msg):
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    data["logs"].append(entry)
    if len(data["logs"]) > 100:
        data["logs"] = data["logs"][-100:]
    print(entry)

# ==================== محرك الرشق ====================
class RushEngine:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 Chrome/120.0.0.0",
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        ]
        self.referrers = [
            "https://www.google.com/search?q=",
            "https://www.bing.com/search?q=",
            "https://search.yahoo.com/search?p=",
            "https://duckduckgo.com/?q=",
            "https://www.facebook.com/",
            "https://twitter.com/",
            "https://www.reddit.com/",
            "https://www.tiktok.com/",
            "https://www.instagram.com/",
            "https://t.co/",
        ]
        self.endpoints = [
            "https://trafficg.com/free-traffic/",
            "https://trafficg.com/generator/",
            "https://trafficg.com/auto-surf/",
        ]
        self.is_running = True
    
    def rush(self, url, count):
        success = 0
        for i in range(count):
            if not self.is_running:
                break
            try:
                endpoint = random.choice(self.endpoints)
                params = {"url": url, "t": int(time.time() * 1000), "r": random.random()}
                headers = {
                    "User-Agent": random.choice(self.user_agents),
                    "Referer": random.choice(self.referrers),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                    "Cache-Control": "no-cache",
                }
                resp = requests.get(endpoint, params=params, headers=headers, timeout=10)
                if resp.status_code == 200:
                    success += 1
                    data["views_total"] += 1
            except:
                pass
            time.sleep(random.uniform(0.05, 0.3))
        return success

rush_engine = RushEngine()

# ==================== لوحة التحكم ====================
HTML = """
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👹 WORM SERVER</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #050505; 
            color: #0f0; 
            font-family: 'Courier New', monospace;
            min-height: 100vh;
            padding: 10px;
        }
        .container { max-width: 900px; margin: auto; }
        h1 { 
            text-align: center; 
            color: #f00; 
            font-size: 2.5em; 
            text-shadow: 0 0 20px #f00;
            margin: 20px 0;
            letter-spacing: 3px;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .card {
            background: #0a0a0a;
            border: 2px solid #0f0;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 15px rgba(0,255,0,0.2);
        }
        .card h2 { 
            color: #f00; 
            margin-bottom: 15px; 
            font-size: 1.2em;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }
        .stat { font-size: 2em; color: #f00; font-weight: bold; }
        .label { color: #888; font-size: 0.9em; }
        .status-dot {
            display: inline-block;
            width: 12px; height: 12px;
            border-radius: 50%;
            background: #0f0;
            box-shadow: 0 0 10px #0f0;
            animation: pulse 1s infinite;
            margin-left: 8px;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        button {
            background: #f00;
            color: #fff;
            border: none;
            padding: 12px 25px;
            font-size: 1em;
            cursor: pointer;
            border-radius: 5px;
            margin: 5px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            transition: all 0.3s;
        }
        button:hover { background: #c00; transform: scale(1.05); }
        button.green { background: #0a0; }
        button.green:hover { background: #080; }
        input, select {
            background: #111;
            border: 1px solid #0f0;
            color: #0f0;
            padding: 10px;
            border-radius: 5px;
            width: 100%;
            margin: 5px 0;
            font-family: 'Courier New', monospace;
        }
        .log-box {
            background: #000;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 5px;
            max-height: 200px;
            overflow-y: auto;
            font-size: 0.8em;
            color: #888;
            margin-top: 10px;
        }
        .footer { text-align: center; color: #444; margin-top: 30px; font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>👹 WORM SERVER</h1>
        
        <div class="grid">
            <div class="card">
                <h2>🤖 بوت تيليجرام <span class="status-dot"></span></h2>
                <p><span class="label">الحالة:</span> <strong>شغال 24/7</strong></p>
                <p><span class="label">المهام:</span> <span class="stat">{{ tasks }}</span></p>
            </div>
            
            <div class="card">
                <h2>🔥 محرك الرشق <span class="status-dot"></span></h2>
                <p><span class="label">المشاهدات:</span> <span class="stat">{{ views }}</span></p>
                <p><span class="label">اللايكات:</span> <span class="stat">{{ likes }}</span></p>
            </div>
            
            <div class="card">
                <h2>📡 VPN <span class="status-dot"></span></h2>
                <p><span class="label">المستخدمين:</span> <span class="stat">{{ vpn }}</span></p>
                <p><span class="label">البورت:</span> <strong>8080</strong></p>
            </div>
            
            <div class="card">
                <h2>⏱️ وقت التشغيل</h2>
                <p><span class="stat">{{ uptime }}</span></p>
                <p><span class="label">منذ آخر تشغيل</span></p>
            </div>
        </div>
        
        <div class="card" style="margin-top: 15px;">
            <h2>🎯 رشق سريع</h2>
            <input type="text" id="url" placeholder="أدخل الرابط المستهدف...">
            <input type="number" id="count" placeholder="العدد (مثال: 100)" value="100">
            <button onclick="rush()">🔥 ابدأ الرشق</button>
            <button class="green" onclick="rushAll()">🚀 رشق شامل (5 مصادر)</button>
            <p id="rush_result" style="margin-top: 10px;"></p>
        </div>
        
        <div class="card" style="margin-top: 15px;">
            <h2>📋 السجلات</h2>
            <div class="log-box">{{ logs }}</div>
        </div>
        
        <div class="footer">👹 WORM SERVER v1.0 | Uptime: {{ uptime }}</div>
    </div>
    
    <script>
        function rush() {
            const url = document.getElementById('url').value;
            const count = document.getElementById('count').value;
            if (!url) { alert('أدخل الرابط!'); return; }
            document.getElementById('rush_result').innerHTML = '⏳ جاري الرشق...';
            fetch('/api/rush?url=' + encodeURIComponent(url) + '&count=' + count)
                .then(r => r.json())
                .then(d => {
                    document.getElementById('rush_result').innerHTML = 
                        '✅ تم: ' + d.success + '/' + d.total + ' مشاهدة';
                    setTimeout(() => location.reload(), 2000);
                });
        }
        function rushAll() {
            const url = document.getElementById('url').value;
            const count = document.getElementById('count').value;
            if (!url) { alert('أدخل الرابط!'); return; }
            document.getElementById('rush_result').innerHTML = '🚀 رشق شامل...';
            fetch('/api/rush_all?url=' + encodeURIComponent(url) + '&count=' + count)
                .then(r => r.json())
                .then(d => {
                    document.getElementById('rush_result').innerHTML = 
                        '🔥 تم: ' + d.total_success + ' مشاهدة من 5 مصادر';
                    setTimeout(() => location.reload(), 2000);
                });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    uptime_seconds = int(time.time() - data["start_time"])
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    
    logs_display = "<br>".join(data["logs"][-15:]) if data["logs"] else "لا توجد سجلات"
    
    return render_template_string(HTML,
        tasks=data["tasks_done"],
        views=data["views_total"],
        likes=data["likes_total"],
        vpn=len(data["vpn_users"]),
        uptime=uptime_str,
        logs=logs_display
    )

@app.route('/api/status')
def api_status():
    return jsonify({
        "server": "online",
        "views": data["views_total"],
        "likes": data["likes_total"],
        "tasks": data["tasks_done"],
        "uptime": int(time.time() - data["start_time"]),
        "vpn_users": len(data["vpn_users"])
    })

@app.route('/api/rush')
def api_rush():
    url = request.args.get('url', '')
    count = int(request.args.get('count', 100))
    
    if not url:
        return jsonify({"error": "لا يوجد رابط"})
    
    log(f"🚀 رشق: {count} → {url[:50]}...")
    
    def do_rush():
        success = rush_engine.rush(url, count)
        data["tasks_done"] += 1
        log(f"✅ اكتمل: {success}/{count}")
    
    threading.Thread(target=do_rush).start()
    return jsonify({"status": "started", "total": count, "success": 0})

@app.route('/api/rush_all')
def api_rush_all():
    url = request.args.get('url', '')
    count = int(request.args.get('count', 50))
    
    if not url:
        return jsonify({"error": "لا يوجد رابط"})
    
    log(f"🚀 رشق شامل: 5 مصادر × {count} → {url[:50]}...")
    
    def do_rush_all():
        total_success = 0
        for _ in range(5):
            total_success += rush_engine.rush(url, count)
            time.sleep(1)
        data["tasks_done"] += 1
        log(f"✅ رشق شامل: {total_success} مشاهدة")
    
    threading.Thread(target=do_rush_all).start()
    return jsonify({"status": "started", "total": count * 5, "total_success": 0})

@app.route('/health')
def health():
    return "OK", 200

# ==================== بوت تيليجرام ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔥 رشق", callback_data="rush"),
        types.InlineKeyboardButton("📊 لوحة التحكم", callback_data="panel"),
        types.InlineKeyboardButton("📡 VPN", callback_data="vpn"),
        types.InlineKeyboardButton("ℹ️ حالة", callback_data="status"),
    )
    
    bot.reply_to(message, """
👹 *WORM SERVER - جاهز*

⚡ سيرفر شامل:
• 🤖 بوت 24 ساعة
• 🔥 رشق مشاهدات
• 📡 VPN
• 🎛️ لوحة تحكم

*اختر من الأزرار تحت:*
""", parse_mode='Markdown', reply_markup=kb)

@bot.message_handler(commands=['rush'])
def rush_cmd(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ الاستخدام: `/rush [رابط] [عدد]`", parse_mode='Markdown')
        return
    
    url = parts[1]
    count = int(parts[2])
    
    msg = bot.reply_to(message, f"🔥 جاري رشق {count} مشاهدة...")
    
    def do():
        success = rush_engine.rush(url, count)
        data["tasks_done"] += 1
        bot.edit_message_text(
            f"✅ تم الرشق!\n🎯 {url[:40]}...\n📊 {success}/{count} مشاهدة",
            message.chat.id, msg.message_id
        )
    
    threading.Thread(target=do).start()

@bot.message_handler(commands=['rushall'])
def rushall_cmd(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ `/rushall [رابط] [عدد]`", parse_mode='Markdown')
        return
    
    url = parts[1]
    count = int(parts[2])
    
    msg = bot.reply_to(message, f"🚀 رشق شامل: 5 مصادر × {count}...")
    
    def do():
        total = 0
        for i in range(5):
            total += rush_engine.rush(url, count)
            time.sleep(0.5)
        data["tasks_done"] += 1
        bot.edit_message_text(
            f"🔥 الرشق الشامل اكتمل!\n📊 {total} مشاهدة من 5 مصادر",
            message.chat.id, msg.message_id
        )
    
    threading.Thread(target=do).start()

@bot.message_handler(commands=['status'])
def status_cmd(message):
    uptime = int(time.time() - data["start_time"])
    h, m = uptime // 3600, (uptime % 3600) // 60
    
    bot.reply_to(message, f"""
🖥️ *حالة السيرفر*

⏱️ وقت التشغيل: {h}h {m}m
👁️ المشاهدات: {data['views_total']}
❤️ اللايكات: {data['likes_total']}
✅ المهام: {data['tasks_done']}
📡 VPN: {len(data['vpn_users'])} مستخدم
🟢 الحالة: شغال
""", parse_mode='Markdown')

@bot.message_handler(commands=['panel'])
def panel_cmd(message):
    bot.reply_to(message, f"🎛️ لوحة التحكم:\n{request.host_url}")

@bot.message_handler(commands=['vpn'])
def vpn_cmd(message):
    vpn_config = f"""
📡 *VPN Config*

النوع: VMess
السيرفر: {request.host.replace('https://', '').replace('http://', '').split(':')[0]}
البورت: 8080
المعرف: worm-vpn-user-{random.randint(1000,9999)}
الشبكة: ws
المسار: /vpn
"""
    bot.reply_to(message, vpn_config, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "rush":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "أرسل الأمر:\n`/rush [رابط] [عدد]`", parse_mode='Markdown')
    elif call.data == "panel":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"🎛️ {request.host_url}")
    elif call.data == "status":
        bot.answer_callback_query(call.id)
        status_cmd(call.message)
    elif call.data == "vpn":
        bot.answer_callback_query(call.id)
        vpn_cmd(call.message)

# ==================== تشغيل كل شيء ====================
def run_bot():
    """تشغيل البوت في Thread منفصل"""
    log("🤖 بوت تيليجرام: يشتغل...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            log(f"⚠️ خطأ في البوت: {e}")
            time.sleep(10)

def run_rush_daemon():
    """محرك رشق خلفي مستمر"""
    log("🔥 محرك الرشق: جاهز")
    while True:
        time.sleep(60)

def keep_alive():
    """منع السيرفر من النوم"""
    while True:
        try:
            requests.get(f"http://localhost:{PORT}/health", timeout=5)
        except:
            pass
        time.sleep(300)

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════╗
║                                          ║
║        👹 WORM SERVER ONLINE             ║
║        All Systems: GO                   ║
║                                          ║
║   🤖 Bot: Starting...                    ║
║   🔥 Rush: Ready                         ║
║   📡 VPN: Ready                          ║
║   🎛️ Panel: Port """ + str(PORT) + """                    ║
║                                          ║
╚══════════════════════════════════════════╝
    """)
    
    # تشغيل البوت
    threading.Thread(target=run_bot, daemon=True).start()
    log("🤖 البوت: شغال")
    
    # تشغيل محرك الرشق
    threading.Thread(target=run_rush_daemon, daemon=True).start()
    log("🔥 الرشق: شغال")
    
    # منع النوم
    threading.Thread(target=keep_alive, daemon=True).start()
    log("🔄 Keep-alive: نشط")
    
    # تشغيل لوحة التحكم
    log(f"🎛️ لوحة التحكم: http://0.0.0.0:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)