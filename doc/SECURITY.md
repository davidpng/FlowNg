# FlowNG security notes and scanning guide

FlowNG is one self-contained HTML file (`FlowNG.html`) that runs entirely in the browser. This document explains what can go wrong with a file like that and how to check a copy before using it, especially with patient data. It is a research tool, not validated for clinical use (see the README).

## 1. Security risks of a single-file HTML application

**The file is the program and the program is the file.** There is no installer, signature or update channel, so everything depends on whether the copy in front of you is the one the author published.

1. **Tampered copies.** Anyone can edit an HTML file and pass it on. A modified copy can send the events you load to a server (an image request, `fetch`, `WebSocket`, `sendBeacon`, a form post, a link that opens with data in the URL). To the user it looks identical. The browser asks for no permission because loading a file you opened yourself needs none.
2. **Shared analysis files are code plus data.** *Export Shareable HTML* makes a copy of the whole app with event data embedded. Opening one from an email or download runs whatever JavaScript is in it with the same access as any page you open. Treat a shared file from someone you do not trust like an unknown program, not like a document. The "Locked viewer" option removes loading and export features from the file, but that is a convenience for honest authors, not a defence against a hostile one.
3. **Hostile input files.** FCS and LMD files, JSON templates and shared-file bundles are parsed in the browser. Text from them (file names, parameter names and labels, population names, template fields) ends up in the page. If any of it is placed into the page as HTML without escaping, a crafted file can run script (cross-site scripting) inside the app and read everything loaded. Malformed files can also exhaust memory or hang the tab (denial of service). Neither normally gives access beyond the browser tab.
4. **No Content Security Policy.** The app does not currently set one, so nothing in the browser stops a modified or injected script from making network requests. A policy that forbids network access would turn most of the risks above into a blocked request (see 4.3).
5. **Patient data leaving by other routes.** Even a clean app can expose identifiers: FCS headers (`$DATE`, `$SRC`, `$FIL`, sample IDs), file names (often accession numbers), browser downloads and caches, screenshots, and shared files that include header metadata. *Export events as FCS* and *Export Shareable HTML* strip these by default; the file name you choose and the "include metadata" tick box are the author's responsibility.
6. **Browser environment.** Extensions can read pages you open, and a page opened from `file://` may be treated more loosely than one served over HTTPS. Use a clean profile or a browser with extensions off for sensitive data.
7. **Hosted copy.** If you use the GitHub Pages copy, you trust the hosting and the repository account (supply-chain risk of a changed commit). Pin to a tagged release and compare hashes (section 3) if that matters to you.

What the app does **not** do (checked in section 2): it has no external scripts, fonts, CDN libraries or analytics, and it does not use cookies, localStorage, sessionStorage or IndexedDB.

## 2. Known issues to check

- **Fixed:** menus and dialogs that put text from files into HTML (file, parameter, population, tab and template names, FCS keywords) now escape it with `_h()`. Before the fix, a file name or parameter name containing `"><img src=x onerror=...>` ran script when the plot, file menu, tab strip or other dialogs were drawn (13 executions in the test below); after it, 0 and the text shows as plain text. When adding a dialog, escape every value that came from a file or template with `_h()` or use `textContent`.
- No Content Security Policy (see 1.4).

## 3. How to scan

Run these from the repository root. A clean result from steps 1 to 3 supports, but does not prove, that a copy is safe.

### 3.1 Confirm the copy is the published one

```bash
# Hash of the file you will use
shasum -a 256 FlowNG.html

# Compare with the repository (no output = identical)
git fetch origin && git diff --stat origin/main -- FlowNG.html
# or against a released copy
curl -sL https://raw.githubusercontent.com/davidpng/FlowNg/main/FlowNG.html | shasum -a 256
```

For a shared file, the app part is the same code as `FlowNG.html` (minus the removed Locked-viewer sections) plus one `<script id="flowng-bundle" ...>` data block. Compare everything outside that block:

```bash
python3 scripts/build_test_daughter.py /tmp/expected.html          # what a locked build of the current app looks like
python3 - <<'PY'
import re,sys
def strip(p):
    s=open(p,encoding='utf-8').read()
    s=re.sub(r'<script id="flowng-bundle" type="application/json">.*?</script>\n?','',s,flags=re.S)
    return re.sub(r'<title>.*?</title>','',s,flags=re.S)
a,b=strip('/tmp/expected.html'),strip(sys.argv[1] if len(sys.argv)>1 else 'SHARED.html')
print('app code identical' if a==b else 'DIFFERENT: diff the two files')
PY
```

(Replace `SHARED.html` with the file to check. It will differ if it was built from a different app version; then diff against that version's tag.)

### 3.2 Static search for network and code-execution paths

Every hit must be understood. In the current app the only expected hits are the `fetch('data:...')` used to decompress shared files, the Blob-URL workers, and plain documentation links.

```bash
F=FlowNG.html     # or the shared file
# Anything that can talk to the network
grep -nE "fetch\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon|navigator\.(connection|serviceWorker)|importScripts|new Worker\(|RTCPeerConnection" "$F"
# External resources and links
grep -noE "(src|href|action|data|poster)=[\"']?https?://[^\"' >]+" "$F"
grep -noE "url\(https?://[^)]+\)|@import +[\"']?https?://|import\(['\"]https?://" "$F"
grep -nE "<form|<iframe|<object|<embed|<meta[^>]+refresh|<base " "$F"
# Dynamic code
grep -nE "\beval\(|new Function\(|document\.write|setTimeout\(['\"]|setInterval\(['\"]|javascript:" "$F"
# Persistent storage
grep -nE "localStorage|sessionStorage|indexedDB|document\.cookie|caches\.open" "$F"
# HTML injection sinks (review each: is text from a file escaped?)
grep -nE "innerHTML|outerHTML|insertAdjacentHTML" "$F"
```

For a shared file, also look at the embedded bundle for anything that is not event or gate data:

```bash
python3 - <<'PY'
import re,json
s=open('SHARED.html',encoding='utf-8').read()
m=re.search(r'<script id="flowng-bundle" type="application/json">(.*?)</script>',s,re.S)
b=json.loads(m.group(1))
print('keys:',list(b)); print('sterile:',b.get('sterile')); print('files:',[f.get('filename') for f in b['files']])
print('has <script in data:', '<script' in m.group(1).lower())
PY
```

### 3.3 Prove it makes no network requests

Static search can miss obfuscated code, so also watch the network while using the file. Either open DevTools, go to **Network**, tick **Preserve log**, then load a file, gate, export and save; the list should be empty apart from the page itself. Or block the network entirely and see that everything still works:

```bash
# Chrome with all DNS resolution disabled; the app must still load and work
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --user-data-dir=/tmp/flowng-scan --host-resolver-rules="MAP * ~NOTFOUND" \
  --disable-extensions "file://$PWD/FlowNG.html"
```

Any console error such as `ERR_NAME_NOT_RESOLVED` means something tried to reach a server.

### 3.4 Patient-identifier scan of anything you plan to share

For a shared HTML or an exported FCS, search for the strings that must not be there: original file names and parts of them, accession numbers, and header keywords.

```bash
OUT=SHARED.html          # or exported.fcs
grep -aoE "\\\$(DATE|BTIM|ETIM|SRC|FIL|OP|CYT|CYTSN|SMNO|EXP|INST|COM)\b|@SAMPLEID|@BARCODE" "$OUT" | sort | uniq -c
grep -a -c "the-original-filename-or-accession" "$OUT"      # repeat for each identifier
```

`doc/TESTING.md` section 8.2 lists the full PHI scan used for shared files, and 15.1 the check for exported FCS files. Rename tubes in the share dialog and leave the metadata box unticked.

### 3.5 Test hostile input

Make small files that try to break out and confirm nothing runs and nothing hangs:

- an FCS/LMD whose `$PnN`/`$PnS` names, or whose file name, contain `"><img src=x onerror=alert(1)>` (rename the file to carry the payload too);
- a template JSON with the same text in population, plot and tab names;
- an FCS whose `$TOT` or `$PAR` is far larger than the data, and a truncated file.

Open each in a throwaway browser profile. An alert box, a console error mentioning `onerror`, or a frozen tab is a failure to fix.

### 3.6 Optional tools

- **Content Security Policy.** Test a policy that blocks all network use. Add this as the first tag in `<head>` of a *copy* and check that every feature still works (workers are created from Blob URLs and the page has inline script and style, which is why those are allowed):

  ```html
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; script-src 'unsafe-inline' blob:; worker-src blob:; style-src 'unsafe-inline'; img-src data: blob:; connect-src data: blob:; base-uri 'none'; form-action 'none'">
  ```

  Then paste the policy into Google's CSP Evaluator for a review. This has not yet been tried against the full app, so expect to adjust it.
- **Linters.** Extract the script and run it through a security-aware linter, for example `eslint` with `eslint-plugin-security` and `eslint-plugin-no-unsanitized`, or `semgrep --config p/javascript`. `python3 scripts/extract_js_for_graphify.py` already pulls the JavaScript out of the HTML.
- **Python helpers.** `scripts/` has no third-party dependencies (`pyproject.toml` lists none), so there is nothing to audit there.

## 4. Safe use checklist

1. Get `FlowNG.html` from the repository or a tagged release and check its hash (3.1).
2. Open files from trusted sources only; open shared HTML files from others in a throwaway browser profile with no extensions.
3. For sensitive data, work offline (or with the network blocked, 3.3) and close the tab when done.
4. Rename tubes and leave "include metadata" off when sharing; run the identifier scan (3.4) on what you send.
5. Report problems at https://github.com/davidpng/FlowNg/issues, without attaching patient data.
