#!/usr/bin/env python3
"""Tests for the Check page and the code-hash manifest (security phases 1 to 3, see doc/SECURITY.md section 5).

  /usr/bin/python3 scripts/test_check.py [shared_file.html ...]

Runs check/index.html's own code in headless Chrome against samples/Complex_Analysis_FlowNg.html (a real shared
file), tamper variants of it, and any shared files given here (each must be a genuine build listed in the manifest;
name them *full* / *locked* so the update tests can use them). Needs Google Chrome or Chromium.
"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome_run import run_page

jobdir = Path(tempfile.mkdtemp(prefix='flowng-test-'))
(jobdir / 'extra').mkdir()
extras = []
for i, f in enumerate(sys.argv[1:]):
    (jobdir / 'extra' / f'{i}.html').write_bytes(Path(f).read_bytes())
    extras.append({'n': i, 'name': Path(f).name})
(jobdir / 'jobs.json').write_text(json.dumps({'extras': extras}))
res = run_page('test.html', jobdir)
if res.get('error'):
    print('BROWSER ERROR:', res['error']); sys.exit(2)
fails = 0
for r in res['results']:
    fails += not r['pass']
    print(('PASS  ' if r['pass'] else 'FAIL  ') + f"{r['name']:70s} {r['detail']}")
print(f"{len(res['results'])} checks, {fails} failed")
sys.exit(1 if fails else 0)
