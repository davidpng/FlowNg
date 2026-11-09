#!/usr/bin/env python3
"""Run the browser tests of doc/TESTING.md (sections 3 to 13 and 15 to 18) in headless Chrome and print a pass/fail list.

  /usr/bin/python3 scripts/run_suite.py                 # everything (about 20 minutes)
  /usr/bin/python3 scripts/run_suite.py --only 4,5,17   # chosen sections
  /usr/bin/python3 scripts/run_suite.py --check         # also run scripts/test_check.py (online and offline) for section 17

The test pages are in scripts/suite/ (one per section, sharing lib.js); each follows its section of TESTING.md row by row and
reports rows with the row numbers used there. A scratch folder is built with FlowNG.html, the samples and fixtures, and shared files
"daughters" built from an export the section 8 page makes, so nothing in the repo changes. Needs Google Chrome or Chromium.
Section 2 (static checks) is separate: see TESTING.md, it needs only node and python.

Exit code 0 if every row passed and no console errors were reported.
"""
import argparse, http.server, json, shutil, subprocess, sys, tempfile, threading, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome_run import find_chrome, ROOT

# page name -> TESTING.md section it covers; order matters (section 8 makes the file the daughters are built from)
BEFORE_DAUGHTERS = [('3', '3'), ('4', '4 and 7.1'), ('5', '5 and 6'), ('7', '7 and 6 (leftovers)'), ('8', '8')]
AFTER_DAUGHTERS = [('9', '9'), ('9b', '9.10, 13.9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'),
                   ('15', '15'), ('15b', '15.9'), ('16', '16'), ('17', '17.17, 17.18'), ('17b', '17.19'), ('18', '18')]
SECTION_OF = {'3': '3', '4': '4', '5': '5', '7': '7', '8': '8', '9': '9', '9b': '9', '10': '10', '11': '11', '12': '12', '13': '13',
              '15': '15', '15b': '15', '16': '16', '17': '17', '17b': '17', '18': '18'}

ap = argparse.ArgumentParser()
ap.add_argument('--only', help='comma-separated TESTING.md section numbers, e.g. 4,5,17')
ap.add_argument('--check', action='store_true', help='also run scripts/test_check.py and its --offline run')
ap.add_argument('--timeout', type=int, default=420, help='seconds allowed per test page')
args = ap.parse_args()
want = set(args.only.split(',')) if args.only else None

work = Path(tempfile.mkdtemp(prefix='flowng-suite-'))
(work / 'samples').mkdir()
shutil.copy(ROOT / 'FlowNG.html', work)
for f in (ROOT / 'samples').iterdir():
    if f.suffix in ('.json', '.LMD'):
        shutil.copy(f, work / 'samples' / f.name)
        if f.suffix == '.LMD':
            shutil.copy(f, work / f.name)
for f in (ROOT / 'scripts' / 'suite').iterdir():
    shutil.copy(f, work / f.name)

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(work), **k)
    def do_POST(self):
        n = int(self.headers['Content-Length']); body = self.rfile.read(n)
        name = self.path.strip('/').split('/')[-1] or 'post'
        if name == 'progress':
            pass                                                  # live progress is not printed; the result file is what counts
        else:
            (work / name).write_bytes(body)
        self.send_response(200); self.end_headers()
    def log_message(self, *a): pass

srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
chrome = find_chrome()
total = {'rows': 0, 'fail': 0, 'errors': 0, 'pages': 0}

def run(page, label):
    res = work / f'result_s{page}'
    if res.exists(): res.unlink()
    prof = tempfile.mkdtemp(prefix='flowng-suite-chrome-')
    t0 = time.time()
    proc = subprocess.Popen([chrome, '--headless=new', f'--user-data-dir={prof}', '--no-first-run', '--disable-extensions',
                             '--allow-file-access-from-files', f'http://127.0.0.1:{port}/suite{page}.html'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while not res.exists() and time.time() - t0 < args.timeout:
        time.sleep(1)
    proc.terminate()
    try: proc.wait(10)
    except Exception: proc.kill()
    shutil.rmtree(prof, ignore_errors=True)
    total['pages'] += 1
    if not res.exists():
        print(f'[section {label}] TIMED OUT after {args.timeout} s'); total['fail'] += 1; return
    r = json.loads(res.read_text())
    fails = [x for x in r['rows'] if not x['pass']]
    total['rows'] += len(r['rows']); total['fail'] += len(fails); total['errors'] += len(r['errors'])
    print(f"[section {label}] {len(r['rows'])} rows, {len(fails)} failed, {len(r['errors'])} console errors ({time.time() - t0:.0f} s)")
    for x in fails:
        print(f"    FAIL {x['id']}: {x['name']}  {str(x['detail'])[:220]}")
    for e in r['errors'][:3]:
        print(f'    ERROR {e[:200]}')
    for n in r.get('notes', []):
        print(f'    note: {n}')

def selected(page):
    return want is None or SECTION_OF[page] in want or (page == '9b' and '13' in want)

def build_daughters():
    full = work / 's8_full.html'
    if not full.exists():
        print('  (no s8_full.html: run section 8 first to build the shared-file fixtures)'); return False
    b = ROOT / 'scripts' / 'build_test_daughter.py'
    for out, extra in (('daughter.html', []), ('daughter_lod.html', ['--lod', '20000']), ('daughter_unlocked.html', ['--unlocked'])):
        subprocess.run([sys.executable, str(b), str(work / out), '--bundle', str(full), *extra], check=True, stdout=subprocess.DEVNULL)
    d = (work / 'daughter.html').read_text(encoding='utf-8')
    app = (work / 'FlowNG.html').read_text(encoding='utf-8')
    inj = '<script>delete window.requestIdleCallback; delete window.cancelIdleCallback;</script>'
    for name, base, code in (('FlowNG_safari.html', app, inj), ('daughter_safari.html', d, inj),
                             ('daughter_nocs.html', d, '<script>delete window.CompressionStream; delete window.DecompressionStream;</script>')):
        i = base.index('<head>') + 6
        (work / name).write_text(base[:i] + code + base[i:], encoding='utf-8')
    return True

try:
    ran_8 = False
    for page, label in BEFORE_DAUGHTERS:
        if selected(page) or (page == '8' and want and want & {'9', '10', '12', '13'}):
            run(page, label)
            ran_8 = ran_8 or page == '8'
    need_daughters = any(selected(p) for p, _ in AFTER_DAUGHTERS if p in ('9', '9b', '10', '12', '13'))
    if need_daughters and not (work / 's8_full.html').exists():
        run('8', '8 (to build the shared-file fixtures)')
    if need_daughters:
        build_daughters()
    for page, label in AFTER_DAUGHTERS:
        if selected(page):
            run(page, label)
    if args.check:
        for extra in ([], ['--offline']):
            r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'test_check.py'), *extra], capture_output=True, text=True)
            last = [l for l in r.stdout.splitlines() if 'checks,' in l]
            print(f"[section 17 test_check.py {' '.join(extra) or '(online)'}] {last[-1] if last else r.stdout[-200:]}")
            if r.returncode: total['fail'] += 1
finally:
    srv.shutdown()
    shutil.rmtree(work, ignore_errors=True)

print(f"\n{total['pages']} test pages, {total['rows']} rows, {total['fail']} failed, {total['errors']} console errors")
sys.exit(1 if total['fail'] or total['errors'] else 0)
