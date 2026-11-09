#!/usr/bin/env python3
"""Build the manifest of code hashes for every released FlowNG version that can produce shared files.

For each commit that changed FlowNG.html (and already has the shared-file loader), hash the canonical form of
  - the 'full' variant (shared with Locked viewer unticked: the whole app), and
  - the 'locked' variant (Locked viewer: loading/import/export code removed)
as scripts/flowng_canon.py defines them. A shared file is genuine FlowNG code if its canonical hash is listed.

Each entry also carries a data-rules level for the data block checker:
  strict    build is older than the HTML-escaping fix: names in the data block must not contain < > " ' &
  standard  build escapes names before putting them in HTML

Usage:  python3 scripts/build_manifest.py [--rev HEAD] [--out check/manifest.json]
The manifest is append-only: existing entries are kept; revoked hashes go in "revoked" (edit by hand).
"""
import argparse, json, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flowng_canon import canon_hash, lite_strip

root = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--rev', default='HEAD')
ap.add_argument('--out', default=str(root / 'check' / 'manifest.json'))
args = ap.parse_args()

def git(*a):
    return subprocess.run(['git', '-C', str(root), *a], check=True, capture_output=True).stdout.decode('utf-8')

out = Path(args.out)
old = json.loads(out.read_text()) if out.exists() else {'format': 1, 'entries': [], 'revoked': []}
have = {}   # rebuilt from history each time; older runs' rules may have changed

commits = git('log', '--reverse', '--format=%H %ad %s', '--date=short', args.rev, '--', 'FlowNG.html').splitlines()
for line in commits:
    sha, date, subject = line.split(' ', 2)
    try:
        src = git('show', f'{sha}:FlowNG.html')
    except subprocess.CalledProcessError:
        continue
    if 'flowng-bundle-loader' not in src or 'capturePristineSource' not in src:
        continue          # before the pristine-snapshot fix: shared files then carried live UI state (even the loaded file name) and cannot be reproduced
    rules = 'standard' if 'function _h(' in src else 'strict'
    for variant, text in (('full', src), ('locked', lite_strip(src))):
        h, nb, problem = canon_hash(text)
        assert nb == 0 and problem is None, (sha, variant, problem)
        if (h, variant) in have:
            continue
        have[(h, variant)] = {'hash': h, 'variant': variant, 'commit': sha[:10], 'date': date, 'subject': subject[:90], 'dataRules': rules}

entries = sorted(have.values(), key=lambda e: (e['date'], e['commit'], e['variant']))
manifest = {'format': 1, 'canon': 'scripts/flowng_canon.py', 'entries': entries, 'revoked': old.get('revoked', [])}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(manifest, indent=1) + '\n')
print(f'{len(entries)} entries ({sum(e["dataRules"] == "strict" for e in entries)} strict) -> {out}')
