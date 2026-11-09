"""Run a page in headless Chrome against a local server and collect what it POSTs to /result.

The repo root is served at /, a temporary job folder at /_job/, and the helper pages in scripts/chrome/ at /_tool/.
Used by build_manifest.py and test_check.py so that the Check page's own code (FlowCheck, using the browser's
HTML parser) is the only implementation of the canonical form.
"""
import http.server, json, os, shutil, subprocess, tempfile, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME_CANDIDATES = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
]

def find_chrome():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c): return c
    raise SystemExit('Chrome not found; install Google Chrome or Chromium')

def run_page(page, jobdir, timeout=600):
    """page: path under /_tool/ (e.g. 'build.html'). Returns the JSON the page posts to /result."""
    jobdir = Path(jobdir)
    box = {}
    class H(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            p = path.split('?', 1)[0]
            if p.startswith('/_job/'): return str(jobdir / p[len('/_job/'):])
            if p.startswith('/_tool/'): return str(ROOT / 'scripts' / 'chrome' / p[len('/_tool/'):])
            return str(ROOT / p.lstrip('/'))
        def do_POST(self):
            n = int(self.headers['Content-Length']); body = self.rfile.read(n)
            if self.path.startswith('/progress'):
                print('  ..', body.decode('utf-8', 'replace'), flush=True)       # live progress from the page
            else:
                box['data'] = body
            self.send_response(200); self.end_headers()
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    prof = tempfile.mkdtemp(prefix='flowng-chrome-')
    proc = subprocess.Popen([find_chrome(), '--headless=new', f'--user-data-dir={prof}', '--no-first-run',
                             '--disable-extensions', f'http://127.0.0.1:{port}/_tool/{page}'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        t0 = time.time()
        while 'data' not in box and time.time() - t0 < timeout: time.sleep(0.3)
        if 'data' not in box: raise SystemExit('timed out waiting for the browser page')
        return json.loads(box['data'])
    finally:
        proc.terminate()
        try: proc.wait(10)
        except Exception: proc.kill()
        srv.shutdown(); shutil.rmtree(prof, ignore_errors=True)
