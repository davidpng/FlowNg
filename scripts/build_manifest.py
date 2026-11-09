#!/usr/bin/env python3
"""Build check/manifest.json: the code hash of every released FlowNG version that can produce shared files.

For each commit that changed FlowNG.html and has the pristine-snapshot fix, hash the `full` variant (whole app) and the
`locked` variant (Locked viewer: loading/import/export code removed). The hash is made by check/index.html's own
FlowCheck code running in headless Chrome, so the manifest and the Check page agree by construction.

Each entry carries a data-rules level for the data-block check:
  strict    build is older than the HTML-escaping fix: names in the data block must not contain < > " '
  standard  build escapes names before putting them in HTML

Usage:  /usr/bin/python3 scripts/build_manifest.py [--rev HEAD] [--out check/manifest.json]
Run it on main at release time. Hand-edit "revoked" to withdraw a version: [{"hash": "...", "reason": "..."}].
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome_run import run_page, ROOT

ap = argparse.ArgumentParser()
ap.add_argument('--rev', default='HEAD')
ap.add_argument('--out', default=str(ROOT / 'check' / 'manifest.json'))
args = ap.parse_args()

def git(*a):
    return subprocess.run(['git', '-C', str(ROOT), *a], check=True, capture_output=True).stdout.decode('utf-8')

out = Path(args.out)
old = json.loads(out.read_text()) if out.exists() else {}
revoked = old.get('revoked', [])

jobdir = Path(tempfile.mkdtemp(prefix='flowng-manifest-'))
(jobdir / 'src').mkdir()
meta, jobs = [], []
for line in git('log', '--reverse', '--format=%H %ad %s', '--date=short', args.rev, '--', 'FlowNG.html').splitlines():
    sha, date, subject = line.split(' ', 2)
    try:
        src = git('show', f'{sha}:FlowNG.html')
    except subprocess.CalledProcessError:
        continue
    if 'flowng-bundle-loader' not in src or 'capturePristineSource' not in src:
        continue   # before the pristine-snapshot fix: shared files then carried live UI state (even the loaded file name) and cannot be reproduced
    rules = 'standard' if 'function _h(' in src else 'strict'
    (jobdir / 'src' / f'{len(meta)}.html').write_text(src, encoding='utf-8')
    for variant in ('full', 'locked'):
        jobs.append({'n': len(meta), 'variant': variant})
    meta.append({'seq': len(meta), 'commit': sha[:10], 'date': date, 'subject': subject[:90], 'dataRules': rules})
(jobdir / 'jobs.json').write_text(json.dumps(jobs))

res = run_page('build.html', jobdir)
if res.get('error'):
    raise SystemExit('browser job failed: ' + res['error'])
seen, entries = set(), []
for r in res['results']:
    assert not r['hasBundle'] and not r['problem'], r      # a source file has no data block
    key = (r['hash'], r['variant'])
    if key in seen: continue                                  # same code as an earlier commit
    seen.add(key)
    m = meta[r['n']]
    entries.append({'hash': r['hash'], 'variant': r['variant'], **m})
entries.sort(key=lambda e: (e['seq'], e['variant']))
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'format': 2, 'canon': 'check/index.html FlowCheck.canonHash', 'entries': entries, 'revoked': revoked}, indent=1) + '\n')
print(f'{len(entries)} entries ({sum(e["dataRules"] == "strict" for e in entries)} strict) -> {out}')
