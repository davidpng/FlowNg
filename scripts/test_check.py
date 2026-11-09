#!/usr/bin/env python3
"""Tests for the Check page and the code-hash manifest (security phases 1 to 3, see doc/SECURITY.md section 5).

  /usr/bin/python3 scripts/test_check.py [--offline] [shared_file.html ...]

--offline builds the offline copy of the page (scripts/build_offline_check.py) and runs the same tests against it, plus a
check that it makes no network requests.

Runs check/index.html's own code in headless Chrome against samples/Complex_Analysis_FlowNg.html (a real shared
file), tamper variants of it, and any shared files given here (each must be a genuine build listed in the manifest;
name them *full* / *locked* so the update tests can use them). Needs Google Chrome or Chromium.
"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome_run import run_page

args = sys.argv[1:]
offline = '--offline' in args
args = [a for a in args if a != '--offline']
jobdir = Path(tempfile.mkdtemp(prefix='flowng-test-'))
(jobdir / 'extra').mkdir()
extras = []
for i, f in enumerate(args):
    (jobdir / 'extra' / f'{i}.html').write_bytes(Path(f).read_bytes())
    extras.append({'n': i, 'name': Path(f).name})
(jobdir / 'jobs.json').write_text(json.dumps({'extras': extras}))
page = 'test.html'
if offline:
    import subprocess
    subprocess.run([sys.executable, str(Path(__file__).resolve().parent / 'build_offline_check.py'), '--out', str(jobdir / 'offline.html')], check=True)
    page = 'test.html?check=/_job/offline.html'
res = run_page(page, jobdir)
if res.get('error'):
    print('BROWSER ERROR:', res['error']); sys.exit(2)
fails = 0
for r in res['results']:
    fails += not r['pass']
    print(('PASS  ' if r['pass'] else 'FAIL  ') + f"{r['name']:70s} {r['detail']}")
print(f"{len(res['results'])} checks, {fails} failed")
sys.exit(1 if fails else 0)
