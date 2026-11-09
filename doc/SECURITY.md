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

## 5. Roadmap: making shared HTML files safe to open

**Trust model: know your sender.** FlowNG relies on people opening shared files only from senders and sites they know and trust, the same way they treat any HTML attachment. Nothing in FlowNG can make a file from an unknown sender safe. The checks below are an optional second layer for the cases where a known sender's account is hijacked or spoofed, or a file is altered on the way. They are deliberately not mandatory, and they are not to be grown further without a concrete threat. What matters most under this model:
1. **Protect the senders and the source.** Two-factor authentication (a hardware key if possible) on the GitHub account that owns the repository and Pages site, branch protection on `main`, and pull-request review. If the source is altered, every user is affected, and the Check page and its manifest too.
2. **Protect patient privacy.** The likeliest real harm is a trusted sender sharing identifiers by accident, not a forged file. Keep metadata stripping on, rename tubes, and review what is shared (phase 5 anonymise).
3. **Tell users the rule.** Open shared files only from people or sites you know; if in doubt, drop the file on the Check page first.

Phases 4 and 6 are **deferred** (not needed for this model); phase 5 is limited to the anonymise default.

Goal: students and proficiency-testing sites can open a single shared HTML file from many different authors without having to trust the author, and without per-author keys.

**Principle.** Every genuine shared file is released FlowNG code plus one data block. A central check can accept a file if (a) the code outside the data block is exactly a released build, and (b) the data block is only data. Authors can then stay anonymous. A file cannot vouch for itself (any check inside it can be edited out), so the check lives at a trusted address that the repo owner controls.

**Decisions made**
- Single-file sharing stays. Files come from teachers and proficiency sites; the central page and the sites' own publishing step are the channel.
- A release is a pull request merged into `main` (a merge commit on main's first-parent history). Commits on branches and direct commits to main are not releases. The manifest lists releases from 7 Nov 2026 on (the start of the beta policy).
- Beta: no backward compatibility. Releases before the HTML-escaping fix (`eb00718`) are withdrawn automatically (they show red with an explanation); files from before 7 Nov 2026 are not recognised.
- The online check must not be the only way to trust a file. Opening a shared file never contacts anything; the Check page is optional. Where GitHub or the network is blocked, or files arrive through a secure channel, use the offline copy of the Check page and the publisher-side check (below).
- Author attribution is optional and off by default; anonymity matters for proficiency testing.

**Phases**
1. **Normaliser and manifest.** A canonical form of a shared file (data block and title removed, HTML parsed to a stable token stream), hashed with SHA-256. A manifest lists the hash of every release (PR merged into `main`, from 7 Nov 2026) in each variant (full, locked). A revocation list is separate.
2. **Command-line checker** (`scripts/check_shared.py`) and tamper tests: injected script, event-handler attribute, extra tag, modified code, hostile data block, unknown version.
3. **Check page** (one HTML file, hosted from the repo's GitHub Pages): drop a file, get a large pass or fail, the reason, and an **Update this file** button that re-wraps the validated data in the current code. Fetches the manifest fresh each time.
4. **Content Security Policy and Trusted Types** in the app (new version, new manifest entry): no network access and no unsafe DOM sinks, so a passing file cannot send data out even if a parser bug is triggered.
5. **Share dialog:** a **Secure distribution channel** box (built): unticked, the file shows a dismissible reminder to check it on open and the export dialog gives a paste-in message with the Check page address and the file's SHA-256; ticked, there is no reminder and the dialog points the author to `scripts/check_shared.py`. The reminder is only a prompt: a tampered file would not show it. **Anonymise** is on by default: the file carries no creation or export time and none of the author's History, so nothing in it says who made it or when (a recipient's own Save adds its own save time and History). Still to build, if wanted: signing (no timestamps, History text, workspace names that could identify an author or site), ready-to-paste text with the Check page address, and optional signing (Ed25519; the file carries only the public key, a signature over the data block and an optional display name; the Check page shows it if present and never requires it).
6. **Protect the source of trust:** hardware-key two-factor, branch protection and `CODEOWNERS` for the manifest and Check page, signed tags, release attestations, and a revocation list for versions that cannot be made safe.

**Limits (tell users plainly)**
- The check protects people who use it or get files from the central place. A bad file sent with "skip the check" is still a risk.
- A lookalike Check page is possible, so state the one official address everywhere.
- The manifest is the crown jewel: if it is altered, bad code can be approved.
- Parser bugs in the data path remain possible; the CSP limits their effect.
- A "verified" badge inside a file proves nothing, because a tampered file would not show it.

**Tests required** (see `doc/TESTING.md`, section 17): tamper tests in the command-line checker and the Check page; hostile names in the data block; an older release's file passes or fails according to the manifest and revocation list; every feature still works under the CSP.

**Status:** phases 1 to 3 built (canonical form, manifest, data-block checks, Check page with Update); phases 4 to 6 not started. The Check page goes live at `https://davidpng.github.io/FlowNg/check/` once this branch is merged to `main` (GitHub Pages serves the repo root).

### What is built

- **`check/index.html`: the Check page.** Drop a shared file (or click to choose it). It reads the file in the browser, fetches `check/manifest.json` fresh, and shows a large green or red result with the reason, the file's SHA-256 (to compare with one sent separately) and, for green files, an **Update to the newest FlowNG** button. The page has its own Content Security Policy (`connect-src 'self'` only: it can read the manifest and `../FlowNG.html` and nothing else), shows file names as text only, and never inserts anything from the dropped file into the page.
- **The canonical form** (`FlowCheck.canonHash` in that page). The file is split at its data block (found only in its exact written form, once, directly before the loader script, body free of `<`), then the rest is parsed with the browser's own parser (`DOMParser`, an inert document). The walk records elements with sorted attributes, text (whitespace collapsed outside script/style), comments and doctype, script and style text exactly, and `<template>` contents. It ignores the `<title>` text and the run-time `--header-h` style on `<html>`. Parsing with the same engine a browser uses closes the parser-difference gap that an earlier Python version of this check had, so the Python canonicalizer was removed.
- **The manifest** (`scripts/build_manifest.py`, default `--rev main --since 2026-11-07`) walks the first-parent merge commits of `main` and, for each, hashes the `full` and `locked` variants by running the Check page's own code in headless Chrome (so the manifest and the page agree by construction). Identical code is listed once. Entries carry `seq` (release order) and the merge commit; `generated` records the build date. Releases from before the escaping fix are put in the `revoked` list automatically with a reason, and hand-written withdrawals in `revoked` are kept. Until this branch's PR is merged, `main` has no sound release, so the manifest in the PR is built on the branch with `--rev HEAD --tip`: `--tip` lists the branch's code as the release the PR will become (marked `pending`). The hash is of the code, so after the merge rebuilding on `main` gives the same hash as a real merge release; confirm that after each release.
- **Data-block checks** (`FlowCheck.validateBundle`): valid JSON object, known format, file list present and bounded, sizes consistent with the parameter list, event data only base64 characters. Names are ordinary data: current builds escape them before they reach the page.
- **Update** (`FlowCheck.buildUpdate`): takes the newest FlowNG (fetched from `../FlowNG.html` online, built in offline), requires it to be the newest `seq` in the manifest for the same variant, puts the validated data block into it (locked files stay locked), and runs the full check on the result. It only offers a file that passes its own check with identical data.
- **Offline copy** (`scripts/build_offline_check.py`): the same page with the manifest and the current `FlowNG.html` built in and `connect-src 'none'`. It works with no network and no GitHub, shows its manifest date, and is rebuilt and handed out with each release (a file from a newer release shows red in an older offline copy). It is not committed (`/FlowNG-Check-offline.html` is ignored).
- **Publisher check** (`scripts/check_shared.py`): checks files with the same code and writes `SHA256SUMS` for the ones that pass. A test provider or teacher who distributes over a secure channel checks files once when publishing, posts only passing files with `SHA256SUMS`, and recipients need no online check.
- **Tests:** `scripts/test_check.py` (section 17 of `doc/TESTING.md`), also against the offline copy (`--offline`).

### Findings from building it

- **A "skip anything that looks like a data block" rule was exploitable.** A second `<script id="flowng-bundle">` with no JSON type would run as JavaScript and still hash as clean. The rule is now an exact text match, once, in the right place; any look-alike stays in the code and changes the hash. Tests cover it.
- **Earlier builds are not supported.** Releases on `main` so far (PRs 25 and 26, 7 Nov 2026) do not escape names in the page, so they are withdrawn; files from before 7 Nov are not recognised. `samples/Complex_Analysis_FlowNg.html` was re-wrapped with the current build (same data) so the example passes.
- **Verified by generation.** Shared files made by the real app (current build, locked and full) and the repo's sample match their manifest entries.
- **Not yet done:** the CSP and Trusted Types in the app itself (phase 4), the anonymise and signing options in the share dialog (phase 5), and repository protection (phase 6). Until phase 4, a file that passes the check can still be made to misbehave by a bug in the app's own data handling; the check proves the code is released code, not that released code has no bugs.
