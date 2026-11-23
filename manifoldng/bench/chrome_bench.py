"""Confirm node timings in headless Chrome: run bench.html for each (method, n) given.

Usage: /usr/bin/python3 chrome_bench.py 1:100000 3:50000 ... [--d 20] [--out chrome.jsonl]
Each point loads a fresh page (fresh WASM memory). Serves this folder over HTTP with Range support."""
import http.server, json, os, re, shutil, subprocess, sys, tempfile, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'scripts'))
from chrome_run import find_chrome  # noqa: E402

args = sys.argv[1:]
d = int(args[args.index('--d') + 1]) if '--d' in args else 20
out = args[args.index('--out') + 1] if '--out' in args else 'chrome.jsonl'
points = [a for a in args if re.fullmatch(r'\d+:\d+', a)] + (['0:0'] if '--calibrate' in args else [])
box = {}

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(HERE), **k)
    def send_head(self):
        rng = self.headers.get('Range')
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path): return super().send_head()
        a, b = (int(x) for x in re.match(r'bytes=(\d+)-(\d+)', rng).groups())
        size = os.path.getsize(path); b = min(b, size - 1)
        f = open(path, 'rb'); f.seek(a)
        self.send_response(206)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Range', f'bytes {a}-{b}/{size}')
        self.send_header('Content-Length', str(b - a + 1)); self.end_headers()
        self.wfile.write(f.read(b - a + 1)); f.close(); return None
    def do_POST(self):
        box['data'] = self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(200); self.end_headers()
    def log_message(self, *a): pass

srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
for pt in points:
    m, n = pt.split(':')
    box.clear()
    prof = tempfile.mkdtemp(prefix='mng-chrome-')
    url = f'http://127.0.0.1:{port}/bench.html?method={m}&n={n}&d={d}&wasm=data/bench.wasm&data=data/mm_mrd.f32' + ('&calibrate=1' if m == '0' else '')
    proc = subprocess.Popen([find_chrome(), '--headless=new', f'--user-data-dir={prof}', '--no-first-run',
                             '--disable-extensions', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while 'data' not in box and time.time() - t0 < 1800: time.sleep(0.5)
    proc.terminate(); proc.wait(10); shutil.rmtree(prof, ignore_errors=True)
    r = json.loads(box['data']) if 'data' in box else {'method': int(m), 'n': int(n), 'd': d, 'error': 'timeout'}
    r['dataset'] = 'mm_mrd.f32'
    with open(HERE / out, 'a') as f: f.write(json.dumps(r) + '\n')
    print(r, flush=True)
srv.shutdown()
