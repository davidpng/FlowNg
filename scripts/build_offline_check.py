#!/usr/bin/env python3
"""Build an offline copy of the Check page: check/index.html with check/manifest.json and the current FlowNG.html inside.

The offline copy needs no network (its Content Security Policy forbids it), so it works where GitHub is blocked.
Give it to people through a channel you trust, together with the shared files. It only knows the FlowNG releases that were
in the manifest when it was built (the page says so), so rebuild and redistribute it with each release.

  /usr/bin/python3 scripts/build_offline_check.py [--out FlowNG-Check-offline.html]
"""
import argparse, json, re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--out', default=str(root / 'FlowNG-Check-offline.html'))
args = ap.parse_args()

page = (root / 'check' / 'index.html').read_text(encoding='utf-8')
manifest = json.loads((root / 'check' / 'manifest.json').read_text(encoding='utf-8'))
app = (root / 'FlowNG.html').read_text(encoding='utf-8')

blob = json.dumps({'manifest': manifest, 'app': app}).replace('<', '\\u003c')      # no "<": cannot end the script early
tag = '<script id="flowcheck-embedded" type="application/json">' + blob + '</script>\n'
first = page.index('<script>')
out = page[:first] + tag + page[first:]
# no network at all
csp_old = "connect-src 'self';"
assert csp_old in out
out = out.replace(csp_old, "connect-src 'none';")
out = out.replace('<title>FlowNG Check</title>', '<title>FlowNG Check (offline copy)</title>')
Path(args.out).write_text(out, encoding='utf-8')
print(f'wrote {args.out} ({len(out) / 1024:.0f} KB), {len(manifest["entries"])} releases, manifest dated {manifest.get("generated")}')
