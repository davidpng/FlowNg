#!/usr/bin/env python3
"""Extract FlowNG.html's three <script> blocks to .js files so graphify can parse them as code.

graphify treats .html as a document (LLM summary), not code. Extracting the scripts gives it a real
call graph. Usage:
  python3 scripts/extract_js_for_graphify.py OUT_DIR      # then: cd OUT_DIR && graphify .
Writes flowng_main.js, compute_worker.js, parse_worker.js and copies kaluza_to_flowng.py.
"""
import re, shutil, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1] if len(sys.argv) > 1 else 'graphify-corpus')
out.mkdir(parents=True, exist_ok=True)
html = (root / 'FlowNG.html').read_text(encoding='utf-8')
written = set()
for m in re.finditer(r'<script([^>]*)>\n(.*?)</script>', html, re.S):
    attrs, body = m.groups()
    name = ('compute_worker.js' if 'compute-worker-src' in attrs else
            'parse_worker.js' if 'parse-worker-src' in attrs else
            'flowng_main.js' if not attrs.strip() else None)
    if name and name not in written:
        (out / name).write_text(body, encoding='utf-8'); written.add(name)
shutil.copy(root / 'scripts' / 'kaluza_to_flowng.py', out / 'kaluza_to_flowng.py')
print('wrote', sorted(written), 'to', out)
