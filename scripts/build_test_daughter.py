#!/usr/bin/env python3
"""Build a locked ("daughter") shared HTML from the current FlowNG.html, for testing.

The app normally makes these through Export Shareable HTML in a browser. This does the same
assembly without one, so a test can rebuild a daughter from the working tree in a second:
  - copies FlowNG.html and strips the @lite regions (what "Locked viewer" removes),
  - attaches the event bundle taken from an existing shared file (default: the repo example),
  - optionally lowers LOD_TARGET so the progressive-render path runs on a small file.

Usage:
  python3 scripts/build_test_daughter.py OUT.html
  python3 scripts/build_test_daughter.py OUT.html --lod 20000        # exercise the large-population path
  python3 scripts/build_test_daughter.py OUT.html --bundle other_shared.html
  python3 scripts/build_test_daughter.py OUT.html --unlocked         # keep loading/import/export code
"""
import argparse
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('out')
ap.add_argument('--bundle', default=str(root / 'samples' / 'CLL_Example_Small_FlowNG_shared.html'),
                help='shared HTML whose embedded events/template are reused')
ap.add_argument('--lod', type=int, help='override LOD_TARGET (default 100000)')
ap.add_argument('--unlocked', action='store_true', help='do not strip the loading/import/export code')
args = ap.parse_args()

src = (root / 'FlowNG.html').read_text(encoding='utf-8')
old = Path(args.bundle).read_text(encoding='utf-8')
m = re.search(r'<script id="flowng-bundle" type="application/json">(.*?)</script>', old, re.S)
if not m:
    raise SystemExit(f'no embedded bundle in {args.bundle}')
bundle = m.group(1)

if args.lod:
    assert 'const LOD_TARGET = 100_000;' in src
    src = src.replace('const LOD_TARGET = 100_000;', f'const LOD_TARGET = {args.lod};')

if args.unlocked:
    app = src
    bundle = bundle.replace('"sterile":true', '"sterile":false')
else:
    # Marker strings are split so this file never contains a literal marker.
    js = re.compile(r'/\*@li' + r'te:begin\*/[\s\S]*?/\*@li' + r'te:end\*/\n?')
    ht = re.compile(r'<!--@li' + r'te:begin-->[\s\S]*?<!--@li' + r'te:end-->\n?')
    app = ht.sub('', js.sub('', src))
    app = ''.join(app.split('<button class="primary" onclick="document.getElementById(\'file-input\').click()">Open FCS File</button>'))

tag = '<script id="flowng-bundle-loader"'
i = app.rindex(tag)
out = app[:i] + '<script id="flowng-bundle" type="application/json">' + bundle + '</script>\n' + app[i:]
Path(args.out).write_text(out, encoding='utf-8')
print(f'wrote {args.out} ({len(out) / 1048576:.1f} MB)')
