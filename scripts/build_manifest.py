#!/usr/bin/env python3
"""Build check/manifest.json: the code hash of every FlowNG release, meaning each pull request merged into main.

A release is a merge commit on main's first-parent history (what "Merge pull request" creates) dated on or after
--since (default 2026-11-07, the start of the beta policy). Commits made on branches, and direct commits to main, are not
releases. For each release the `full` variant (whole app) and the `locked` variant (Locked viewer: loading/import/export
code removed) are hashed by check/index.html's own FlowCheck code in headless Chrome, so the manifest and the Check page
agree by construction. Releases whose code has the same hash as an earlier one are listed once.

A release made before the pristine-snapshot and HTML-escaping fixes is withdrawn automatically: its hashes go in "revoked"
with a reason, so its files show red with an explanation instead of "unknown code".

Usage:  /usr/bin/python3 scripts/build_manifest.py [--rev main] [--since 2026-11-07] [--tip] [--out check/manifest.json]
  --tip  also lists the current branch tip as the release this pull request will become (marked "pending"). Use it on the
         PR branch so the manifest in the PR already contains the code that will be merged. After the merge, rebuilding on
         main gives the same hash (check this), now as a real merge release.
Hand-edit "revoked" to withdraw a version by hand: [{"hash": "...", "reason": "..."}]; entries marked "auto" are rebuilt.
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome_run import run_page, ROOT

ap = argparse.ArgumentParser()
ap.add_argument('--rev', default='main', help='history to list (default: main)')
ap.add_argument('--tip', action='store_true', help='also list the current branch tip as the pending release of this PR')
ap.add_argument('--since', default='2026-11-07', help='first release date to list')
ap.add_argument('--out', default=str(ROOT / 'check' / 'manifest.json'))
args = ap.parse_args()

def git(*a):
    return subprocess.run(['git', '-C', str(ROOT), *a], check=True, capture_output=True).stdout.decode('utf-8')

out = Path(args.out)
old = json.loads(out.read_text()) if out.exists() else {}
revoked = [r for r in old.get('revoked', []) if not r.get('auto')]      # keep hand-written withdrawals
WITHDRAWN = ('This FlowNG version has a known problem (it does not escape names, so a crafted file could run code). '
             'Ask the sender to re-export the analysis with the current FlowNG.')

jobdir = Path(tempfile.mkdtemp(prefix='flowng-manifest-'))
(jobdir / 'src').mkdir()
meta, jobs = [], []
for line in git('log', '--first-parent', '--merges', '--reverse', f'--since={args.since}', '--format=%H %ad %s', '--date=short', args.rev).splitlines():
    sha, date, subject = line.split(' ', 2)
    try:
        src = git('show', f'{sha}:FlowNG.html')
    except subprocess.CalledProcessError:
        continue
    if 'flowng-bundle-loader' not in src:
        continue   # no shared-file feature
    sound = 'capturePristineSource' in src and 'function _h(' in src
    (jobdir / 'src' / f'{len(meta)}.html').write_text(src, encoding='utf-8')
    for variant in ('full', 'locked'):
        jobs.append({'n': len(meta), 'variant': variant})
    meta.append({'seq': len(meta), 'commit': sha[:10], 'date': date, 'subject': subject[:90], 'sound': sound})
if args.tip:
    src = (ROOT / 'FlowNG.html').read_text(encoding='utf-8')       # the working tree: the code this PR will release
    sound = 'capturePristineSource' in src and 'function _h(' in src
    (jobdir / 'src' / f'{len(meta)}.html').write_text(src, encoding='utf-8')
    for variant in ('full', 'locked'):
        jobs.append({'n': len(meta), 'variant': variant})
    meta.append({'seq': len(meta), 'commit': git('rev-parse', '--short=10', 'HEAD').strip(), 'date': __import__('datetime').date.today().isoformat(),
                 'subject': 'pending release: the tip of this pull request', 'pending': True, 'sound': sound})
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
    m = dict(meta[r['n']]); sound = m.pop('sound')
    if sound:
        entries.append({'hash': r['hash'], 'variant': r['variant'], **m})
    else:
        revoked.append({'hash': r['hash'], 'variant': r['variant'], 'commit': m['commit'], 'date': m['date'], 'reason': WITHDRAWN, 'auto': True})
entries.sort(key=lambda e: (e['seq'], e['variant']))
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'format': 3, 'generated': __import__('datetime').date.today().isoformat(), 'rev': args.rev, 'canon': 'check/index.html FlowCheck.canonHash', 'entries': entries, 'since': args.since, 'revoked': revoked}, indent=1) + '\n')
print(f'{len(entries)} releases listed, {sum(bool(r.get("auto")) for r in revoked)} withdrawn automatically ({args.rev} since {args.since}) -> {out}')
