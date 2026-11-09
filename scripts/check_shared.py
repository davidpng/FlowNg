#!/usr/bin/env python3
"""Check shared FlowNG files before you distribute them, and write a SHA256SUMS list for them.

For test providers and teachers who publish files from a channel they control: run this once, publish only the files that
pass, and put SHA256SUMS next to them (recipients can compare it, and nobody has to run the online Check page).
Uses the same code as the Check page (check/index.html) in headless Chrome, against check/manifest.json.

  /usr/bin/python3 scripts/check_shared.py file1.html file2.html ... [--sums SHA256SUMS]

Exit code 0 if every file passes, 1 if any fails.
"""
import argparse, hashlib, json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chrome_run import run_page

ap = argparse.ArgumentParser()
ap.add_argument('files', nargs='+')
ap.add_argument('--sums', default='SHA256SUMS', help='where to write the SHA-256 list (only passing files are listed)')
args = ap.parse_args()

jobdir = Path(tempfile.mkdtemp(prefix='flowng-verify-'))
(jobdir / 'files').mkdir()
for i, f in enumerate(args.files):
    (jobdir / 'files' / str(i)).write_bytes(Path(f).read_bytes())
(jobdir / 'jobs.json').write_text(json.dumps([{'n': i} for i in range(len(args.files))]))
res = run_page('verify.html', jobdir)
if res.get('error'):
    print('BROWSER ERROR:', res['error']); sys.exit(2)

sums, bad = [], 0
for r in res['results']:
    path = Path(args.files[r['n']])
    if r['status'] == 'ok':
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sums.append(f'{digest}  {path.name}')
        i = r['info']
        print(f"PASS  {path.name}  ({r['build']}; {i['files']} file(s), {i['events']:,} events)")
    else:
        bad += 1
        print(f"FAIL  {path.name}  " + ' | '.join(r['reasons']))
if sums:
    Path(args.sums).write_text('\n'.join(sums) + '\n')
    print(f'wrote {args.sums} ({len(sums)} file(s))')
sys.exit(1 if bad else 0)
