#!/usr/bin/env python3
"""Tests for the code-hash manifest (phase 1 of the shared-file safety plan, see doc/SECURITY.md section 5).

  /usr/bin/python3 scripts/test_manifest.py [extra_shared_file.html ...]

Uses samples/Complex_Analysis_FlowNg.html (a real shared file) as the base for tamper tests. Extra files
given on the command line must also be listed in the manifest.
"""
import json, re, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / 'scripts'))
from flowng_canon import canon_hash, lite_strip, split_bundle

manifest = json.loads((root / 'check' / 'manifest.json').read_text())
by_hash = {}
for e in manifest['entries']:
    by_hash.setdefault(e['hash'], []).append(e)
fails = 0

def verdict(html):
    h, nb, problem = canon_hash(html)
    if problem: return 'REJECT: ' + problem
    if nb != 1: return 'REJECT: no data block'
    es = by_hash.get(h)
    return ('OK ' + es[0]['variant'] + ' ' + es[0]['commit'] + ' ' + es[0]['dataRules']) if es else 'REJECT: code not in manifest'

def expect(name, html, ok):
    global fails
    v = verdict(html)
    good = v.startswith('OK') == ok
    fails += not good
    print(f"{'PASS' if good else 'FAIL'}  {name:46s} {v}")

sample = (root / 'samples' / 'Complex_Analysis_FlowNg.html').read_text(encoding='utf-8')
expect('repo sample is a released build', sample, True)
for f in sys.argv[1:]:
    expect(f'extra: {Path(f).name}', Path(f).read_text(encoding='utf-8'), True)

# allowed changes: the data block and the title
expect('title changed', re.sub(r'<title>.*?</title>', '<title>Class 3</title>', sample, count=1, flags=re.S), True)
expect('data block replaced', re.sub(r'(<script id="flowng-bundle" type="application/json">)[^<]*(</script>)', r'\1{"a":1}\2', sample), True)
expect('markup whitespace reflowed', sample.replace('><', '>\n<', 5), True)

# attacks
expect('no data block (plain source)', (root / 'FlowNG.html').read_text(encoding='utf-8'), False)
expect('extra script tag', sample.replace('</body>', '<script>fetch("//evil")</script></body>'), False)
expect('event-handler attribute', sample.replace('<body', '<body onload="fetch(1)"', 1), False)
expect('image with onerror', sample.replace('</body>', '<img src=x onerror=alert(1)></body>'), False)
expect('iframe', sample.replace('</body>', '<iframe src="//evil"></iframe></body>'), False)
expect('external stylesheet', sample.replace('</head>', '<link rel=stylesheet href=//evil/x.css></head>'), False)
expect('meta refresh', sample.replace('</head>', '<meta http-equiv=refresh content="0;url=//evil"></head>'), False)
expect('one character of code changed', sample.replace('function showToast', 'function showToasT', 1), False)
expect('code added inside the app script', sample.replace('function showToast(', 'fetch("//evil");function showToast(', 1), False)
expect('style attribute on <html>', sample.replace('<html', '<html style="x:y"', 1), False)
expect('comment added', sample.replace('</body>', '<!--x--></body>'), False)
expect('second plain bundle-id script', sample.replace('</body>', '<script id="flowng-bundle">fetch(1)</script></body>'), False)
dup = re.search(r'<script id="flowng-bundle" type="application/json">[^<]*</script>', sample).group(0)
expect('two exact data blocks', sample.replace(dup, dup + dup, 1), False)
expect('data block moved elsewhere', sample.replace(dup, '', 1).replace('</body>', dup + '</body>'), False)
expect('data block type changed to JS', sample.replace('id="flowng-bundle" type="application/json"', 'id="flowng-bundle" type="text/javascript"', 1), False)
expect('data block closed early then script', sample.replace(dup, dup[:-9] + '</script><script>fetch(1)</script><script>', 1), False)
expect('lite-stripped source (no block)', lite_strip((root / 'FlowNG.html').read_text(encoding='utf-8')), False)

# manifest properties
ents = manifest['entries']
n_std = sum(e['dataRules'] == 'standard' for e in ents)
good = len(ents) > 20 and len({(e['hash'], e['variant']) for e in ents}) == len(ents) and n_std >= 2
fails += not good; print(f"{'PASS' if good else 'FAIL'}  manifest has {len(ents)} unique entries, {n_std} standard")
cur = subprocess.run(['git', '-C', str(root), 'log', '-1', '--format=%h'], capture_output=True).stdout.decode().strip()
print('HEAD', cur, '| failures:', fails)
sys.exit(1 if fails else 0)
