# Testing FlowNG

A checklist for Claude (or a person) to follow after any change to `FlowNG.html`, the Kaluza converter, or the export code. It drives the real app in the browser pane, so it needs no test framework. Say "run TESTING.md" and work through the sections in order; sections 1-2 are always required, the rest depend on what changed (see the table).

The app keeps loaded files in a **Pool** and each loaded template in its own **workspace** (files, tabs, plots, undo, history). The globals `fcsFiles`, `plots`, `tabs`, `_undoStack`, `_history` always hold the *live* workspace, so older checks that read them still apply to whichever workspace is open.

| You changed... | Run sections |
|---|---|
| Anything | 1, 2, 3, 12 |
| Gating, tree, undo, plots | + 4, 5, 6, 10 |
| Templates, Kaluza converter | + 7, 13 |
| Workspaces, Pool, file loading, starter template | + 13 |
| Export, shared files, Save, History | + 8, 9, 11, 13 |
| Rendering, evaluation, loading | + 11 (performance) |

## 0. Rules and traps (learned the hard way)

- **Serve over HTTP.** `file://` blocks `fetch` and the browser pane refuses it. Use `python3 -m http.server PORT` from a scratch folder (section 1).
- **Keep each `javascript_exec` under about 40 seconds.** When the pane is hidden, timers are throttled and a long call times out. The script may still be running: check state before re-running, and split long flows into several calls.
- **Top-level `let`/`const` are not window properties.** In an iframe use `w.eval('fcsFiles.length')`, never `w.fcsFiles`. A poll on `w.fcsFiles` never resolves.
- **The pane allows a limited number of tabs.** Close old ones (`tabs_close`) before opening new ones; reuse one tab with `navigate`.
- **Stub dialogs and downloads before exercising export/save:** `window.showSaveFilePicker = undefined; HTMLAnchorElement.prototype.click = function(){}; window.prompt = (m, d) => d; window.confirm = () => true;` and capture the blob by wrapping `URL.createObjectURL`.
- **Workers cannot see main-script functions.** `evalGateW` and the parse worker have their own copies of helpers. `node --check` will not catch a helper used inside a worker; run a worker-evaluated gate (section 4) after touching shared math.
- **Never use real patient files.** The three `TEST SAMPLE *.LMD` files are the fixtures. A file name or header can hold a name, accession number or date: scan outputs (section 8).
- **Do not trust one signal.** A plot can have correct state and a stale picture; compare pixels (section 10).
- Timings below are from one Mac; use them as ratios. Re-baseline (section 11) when the hardware changes.

## 1. Setup

```bash
SP=<scratchpad dir>; mkdir -p $SP/t && cd /path/to/FlowNg
python3 scripts/build_test_daughter.py $SP/t/daughter.html                    # locked file
python3 scripts/build_test_daughter.py $SP/t/daughter_lod.html --lod 20000    # forces the large-population render path
python3 scripts/build_test_daughter.py $SP/t/daughter_unlocked.html --unlocked
cp FlowNG.html "TEST SAMPLE"*.LMD flowviz_B_cells.json $SP/t/ && mkdir -p $SP/t/samples && cp samples/*.json $SP/t/samples/
cd $SP/t && python3 -m http.server 8770 &
```

The app is `http://localhost:8770/FlowNG.html`. Expected: `curl -sI` returns 200. Rebuild the daughters whenever `FlowNG.html` changes (they embed a copy of it).

Load the three fixtures (used by most sections). Loaded files wait in the **Pool**; most sections then need a workspace, which comes from `openPoolInWorkspace()` (blank, one default plot per file) or from importing a template (section 7):

```js
const names = ['00028336 001', '00028337 002', '00028338 003'];
for (const n of names) {
  const fn = `TEST SAMPLE 26125127597b ${n}.LMD`;
  loadFCS(await (await fetch('/' + encodeURIComponent(fn))).arrayBuffer(), fn);
  await new Promise(r => setTimeout(r, 5500));
}
JSON.stringify({ events: fcsFiles.map(f => f.nEvents), tubes: fcsFiles.map(_fileTubeName) })
```
Replace `fcsFiles` with `poolFiles` in that line: the files are in the Pool, `fcsFiles.length` is 0 and there are no plots. Expected: events `[33635,37596,31015]`; tubes `LL panel B cell tube`, `LL panel T cell tube`, `LL panel myeloid tube`. The page shows the placeholder "3 files in the Pool, no workspace open".

## 2. Static checks (no browser)

```bash
python3 scripts/extract_js_for_graphify.py $SP/js && for f in $SP/js/*.js; do node --check "$f" && echo "ok $f"; done
```
Expected: `ok` for `flowng_main.js`, `compute_worker.js`, `parse_worker.js`.

Scope check: functions that exist only in the main script must not be called inside a worker.

```bash
python3 - <<'E'
import re
s = open('FlowNG.html').read()
main = re.search(r'<script>\n(.*?)</script>', s, re.S).group(1)
main_funcs = set(re.findall(r'^(?:async )?function (\w+)', main, re.M)) | set(re.findall(r'^const (\w+) = ', main, re.M))
for t in ('compute-worker-src', 'parse-worker-src'):
    w = re.search(r'<script id="%s" type="text/worker">\n(.*?)</script>' % t, s, re.S).group(1)
    own = set(re.findall(r'function (\w+)', w)) | set(re.findall(r'(?:const|let|var) (\w+)', w))
    bad = sorted(n for n in main_funcs - own if re.search(r'\b%s\(' % n, w))
    print(t, 'main-only helpers called in worker:', bad or 'none')
E
```
Expected: `none` for both. Any name listed is a bug unless the worker defines it.

Console check: after every section run `read_console_messages` with `onlyErrors: true`. Expected: none.

## 3. Load and basic rendering

After loading the fixtures (section 1) and `openPoolInWorkspace()`:

```js
JSON.stringify({ plots: plots.length, canvases: document.querySelectorAll('canvas[id^=canvas-]').length, tree: document.querySelectorAll('.pop-tree-node').length })
```
Expected: one default plot per file, canvases equal plots, the tree lists three file roots. Take a screenshot: a green workspace tab above the plot tabs, no Pool node (empty); the top bar has two groups of two rows: left Select, Polygon, Rect, Quadrant, Edit, Comp, Delete / Autocomp, Undo, Redo, History, + Add Plot; right Open FCS File, Export Template, Import Template, Export Shareable HTML / Settings (plus Save and Reset in shared files); at 1,400 px or wider the groups sit side by side (use `resize_window`, and reset it afterwards); plots are white with decade ticks; no console errors.

## 4. Gating

Helpers (paste once per page load):

```js
window.prompt = (m, d) => d; window.confirm = () => true;
const fire = (plot, type, rx, ry) => { const c = document.getElementById('canvas-' + plot.id), r = c.getBoundingClientRect(), tf = plot._tf;
  c.dispatchEvent(new MouseEvent(type, { bubbles: true, button: 0, clientX: r.left + tf.dataToCanvasX(rx) * r.width / c.width, clientY: r.top + tf.dataToCanvasY(ry) * r.height / c.height })); };
const gates = f => f.populations.filter(p => p.gateInfo);
```

Use the first tube after importing the BTM template (section 7) so there is a populated tree. Add a fresh plot to draw on: `const f = fcsFiles[0]; const ix = n => f.params.findIndex(p => p.name === n); addPlot(ix('Kappa FITC'), ix('Lambda PE'), f.fileId); const pl = plots[plots.length-1]; switchTab(pl.tabId); changePop(pl.id, f.populations.find(p => p.name === 'Viable').id);` and wait a second. Raw coordinates used below suit that plot (values up to about 1,000,000; clouds near 200-5000).

| # | Do | Expected |
|---|---|---|
| 4.1 | `setGlobalMode('gate')`; click four raw points around a cloud with `fire(pl,'click',x,y)`; click the first point again | A new gate appears in the tree, named by the stubbed prompt; its count is between 0 and the parent's; History has "Drew gate ..." |
| 4.2 | `setGlobalMode('rectgate')`; `fire(pl,'mousedown',x1,y1)`, `fire(pl,'mousemove',x2,y2)`, `fire(pl,'mouseup',x2,y2)` | A 4-point gate is created |
| 4.3 | `createQuadrant(pl, cx, cy)` then wait 2.5 s | Four gates Q1-Q4 whose counts **sum to the parent population's count** exactly |
| 4.4 | `setGlobalMode('pan')`; mousedown on a gate body, mousemove 40 px, mouseup | The gate moved; its count changed; History "Moved gate ..." |
| 4.5 | `setGlobalMode('edit')`; drag a vertex | History "Reshaped gate ..."; a click without movement adds **no** history entry |
| 4.6 | Drag the quadrant crosshair centre (`fire(p,'mousedown',cx,cy)` at the centre, `mousemove` elsewhere, `mouseup`) | All four counts change and still sum to the parent. **Use a plot with no other gates**: a polygon or rectangle drawn over the centre takes the click first |
| 4.7 | Delete a gate with `deleteGateFromTree(id, true)` | Gate and its children gone; plots whose population was deleted fall back to All Events (no blank plot) |
| 4.8 | `reparentGate(id, otherParentId)`; `reorderSibling(a, b, true)` | Tree order changes; colour precedence follows the tree (`fcsFile.colorPrecedence` is the reverse of tree order); a gate cannot be moved under its own descendant |
| 4.9 | `copyGate(id,false)`; `pasteGate(parentId)` | A "... copy" gate under the parent with the same shape; pasting into a file missing a channel is refused with a toast |
| 4.10 | `cycleDotBoost(id)` | Population drawn as exact dots; toggling again restores density |
| 4.11 | `undo()` after each of the above, then `redo()` | State returns and comes back; counts identical; undo/redo logged in History |
| 4.12 | Worker vs main-thread membership: `g.indices = new Int32Array(0); evalGateAsync(g); await 2.5 s` | Count equals the count before (worker result matches `evalGate`) |
| 4.13 | Re-parent siblings: `setGlobalMode('rectgate')`, draw a big rectangle then a smaller one inside it on the same plot (both children of All Events, sharing events); `reparentGate(g2, g1)` | `g2.parentId === g1`, toast "Moved ...". Regression: this used to be refused because the check used event overlap (`getDescendantGates`) instead of the `parentId` chain |
| 4.14 | Then `reparentGate(g1, g2)` | Refused with "Cannot reparent a gate onto one of its own descendants"; parents unchanged |
| 4.15 | Select a plot (add class `selected` to its `.plot-card`), then `setGlobalMode('gate')` | `getSelectedPlots().length === 0` and **every** plot's `.mode` is `'gate'` (drawing works on plots other than the one that was selected) |
| 4.16 | Tool shortcuts: dispatch `keydown` on `document` with `key` `s g r q e c a` | `globalMode` becomes `pan gate rectgate quad edit spill autocomp`; the matching `#gbtn-*` is `.active` |
| 4.17 | Same keys with `ctrlKey`, `metaKey`, `altKey` or `shiftKey: true`; with a `<input>` focused; with a `.modal-overlay` open; before any workspace is open (toolbar hidden) | `globalMode` does not change |
| 4.18 | `keydown` `Delete` and `Backspace` with no plot selected, then with one plot selected | No selection: `globalMode === 'delete'`. With a selection: that plot is removed and the mode is unchanged |
| 4.19 | Read the first eight `#global-toolbar .tool-btn` | Each label has its key in `<b>` (Select, Polygon, Rect, Quadrant, Edit, Comp, **Del**ete, Autocomp); tooltips end with "Shortcut: ..." |
| 4.20 | Rect orthogonality: draw a rectangle (`rectgate`), `setGlobalMode('edit')`, drag one corner (`fire` mousedown on the vertex, mousemove, mouseup) and read `gateInfo.rawPts`; repeat on another corner | Four points still form an axis-aligned rectangle (two distinct x values, two distinct y values, each side horizontal or vertical); the opposite corner has not moved. A hand-drawn polygon with slanted edges still moves one vertex independently |

Boolean gates (BTM has some): after import, their counts are non-zero and change when a referenced gate moves.

## 5. Compensation and cofactors

| # | Do | Expected |
|---|---|---|
| 5.1 | `const m = f.spillMatrix.map(r => [...r]); m[3][8] = 0.02; pushUndo('test'); recomputeCompensation(m, f.fileId); reevaluateAllGates(f)` | Compensated data changes; gate counts update; no error |
| 5.2 | `undo()` | Matrix and counts return to the originals |
| 5.3 | Autocomp on a flat population: add a CD5 PC5.5 vs CD20 PB plot of Lymphs, `setGlobalMode('autocomp')`, `fire` clicks at (3000,-300), (200000,-300), (200000,1500), (3000,1500), then the first point again | Toast "already flat"; no Undo entry and nothing added to History |
| 5.4 | Autocomp on a sloped region: points (-1000,-1000), (300000,-1000), (300000,100000), (-1000,100000) | Coefficient changes (measured 0 to about -0.051); toast and History show before and after; `undo()` restores 0 |
| 5.5 | Cofactor handle: `setGlobalMode('pan')`, select an asinh plot the way a user does (`card.querySelector('.plot-header').click()`; clicking the canvas does not select), then wait a moment, dispatch `mousedown` on `.cf-handle-x`, then `mousemove` and `mouseup` on `window` at a different x | The channel's cofactor changes (measured 300 to 5,508 when dragged to 75% of the axis), gates are re-evaluated, History "Set cofactor of ..."; `undo()` restores. A `keydown` Escape on `window` mid-drag restores the old value with no history entry |

## 6. Plots, tabs, tree

- Add a plot (`addPlot(i,j,fileId)`), change axes (`changeAxis`), change scale (`toggleAxisScale`), change bins (`changeBins(id,128)`): each redraws without error.
- Multi-select scale: with 2+ plots selected (add class `selected` to their `.plot-card`), `toggleAxisScale(id,'x')` gives the X axis of **every** selected plot the same new scale (`xLog`/`xAsinh` equal across them); with none selected it changes only that plot.
- `switchTab` through every tab: each shows its plots. `renameTab`, `removeTab` work and the tab strip shows "Name (count)".
- Delete plots: select two middle plots (add class `selected`), `keydown` `Delete`; History shows "Removed 2 plots", both cards gone. `undo()` restores both at their old positions (`plots` order and `.plot-card` DOM order match the original) and canvases draw; `redo()` removes them again; `Ctrl+Z` after a single-plot delete restores it.
- Tabs undo: `addTabUndoable()` twice, move plots 0 and 1 to tab 2 (`plots[i].tabId = id`), `renameTab(id)` (stub `prompt`), `removeTab(id)`. History shows "Added tab", "Renamed tab ... to ...", "Closed tab ... (its 2 plots moved to ...)". Four `undo()` calls step back through the close (tab returns at its position, the two plots return to it), the rename, and both adds; four `redo()` calls reapply them.
- Expand and collapse a plot (`togglePlotExpand`, `collapsePlot`).
- Axis Range dialog: `showAxisRangeModal(pl,100,100)` then `applyAxisRangeModal(pl.id)` and `resetAxisRangeModal(pl.id)`; no "Display Mode" block; History records both.
- Drag-reorder of plots and tree rows (dispatch `dragstart`/`dragover`/`drop` on `.plot-drag-handle` and `.pop-grip`) reorders them.

## 7. Templates and the Kaluza converter

1. **BTM import by tube name.** Load the fixtures into the Pool (do not open them), use a template whose file names do not match: `importGates(txt)` then read `#import-v3-modal tbody tr`. Expected: each row "by tube name" (or "by file name" for the repo sample), then `_doImportV3([0,1,2])`: a new workspace named after the template, Pool now empty, gate counts `[31,41,30]`, 255 plots, 15 tabs, no skipped gates. With an empty Pool `importGates(txt)` only toasts.
2. **Matcher unit checks** (no UI): build a template with `_buildTemplateV3('t')`, rename each `sourceFile`, then `_matchTemplateFiles(tfs, fcsFiles)` (the second argument is the candidate list; the default is the Pool) returns `tube name` for every file; remove `tube` and it returns `antibody panel`; a template using only channels shared by all tubes returns **no match** (never a guess).
3. **Unmatched sections** show "(skip this section)", not the first file.
4. **Version 2 and junk files are refused:** `importGates('{"version":2,"gates":[]}')` toast says version 2 is unsupported; `{"foo":1}` says "Not a FlowNG template".
5. **Round trip:** export a template (`_buildTemplateV3('rt')`), clear the gates, re-apply with `_applyTemplateV3(t, fcsFiles)`; gate counts and plot count equal the originals.
6. **Single-file template** (`flowviz_B_cells.json`): imports into one tube, 9 gates.
7. **Converter regression:** run `scripts/kaluza_to_flowng.py` on a template and diff against the committed sample (ignore `exported`); output must be identical unless the change was intended. Converted templates that use raw channel names (`FL1 INT`) match no file and say so.

## 8. Export Shareable HTML

```js
window.showSaveFilePicker = undefined; let cap = null; const oc = URL.createObjectURL; URL.createObjectURL = b => { cap = b; return oc(b); };
HTMLAnchorElement.prototype.click = function () {};
showShareDialog(); [...document.querySelectorAll('.share-fname')].forEach((e, i) => e.value = 'Tube ' + (i + 1));
document.getElementById('share-maxev').value = '20000';
await new Promise(r => setTimeout(r, 800)); _updateShareEstimate();
const est = _estimateShareBytes(); await doExportShareable(); window.__exp = cap;
JSON.stringify({ estMB: (est / 1048576).toFixed(2), actualMB: (cap.size / 1048576).toFixed(2) })
```

| # | Check | Expected |
|---|---|---|
| 8.1 | Estimate vs actual | Estimate within about 20% of actual and not more than 10% below it (measured: 2.15 MB estimated, 2.19 MB actual for 3 tubes at 20,000 events) |
| 8.2 | **PHI scan** of `await cap.text()` | Zero hits for: any original file name or its parts (`TEST SAMPLE`, `26125127597b`, the accession-like numbers), `$DATE`, `$BTIM`, `$ETIM`, `@SAMPLEID`, `@BARCODE`; titles and history use the renamed tubes |
| 8.3 | Title | `<title>Shared analysis — FlowNG</title>` (not a file name) |
| 8.4 | Locked content | Output has no `function loadFCS`, `parseLMD`, `showShareDialog`, `doExportTemplate`, `importGates`; no `@lite` markers; no open/import/export buttons |
| 8.5 | Events stored once | Bundle has `rawData` and `rawDataFmt:"i32cs"` and `data:null` for LMD tubes |
| 8.6 | Large file warning | With a file over 500,000 events the cap defaults to 500,000 |
| 8.7 | Size sanity | 3 tubes x 20,000 events is about 2 MB |
| 8.8 | Workspaces | Bundle has `format:2` and `workspaces`, one entry per open workspace, each with `fileIdx`, `template`, `history`; `files` holds every workspace file once; Pool files are not exported. Workspace names are never an original file name (the PHI scan in 8.2 covers them) |

For a real case file, never print contents: scan with a script that reports counts only.

## 9. Daughter (shared) files

Use `daughter.html` (locked) and `daughter_unlocked.html`.

| # | Do | Expected |
|---|---|---|
| 9.1 | Open `daughter.html`; poll `fcsFiles.length === 3 && plots.length > 100` | Ready in about 6 s for 3 x 100k events; gates `[31,41,30]`, 255 plots; Save and History buttons visible; **no** Open/Import/Export buttons; `typeof loadFCS === 'undefined'` |
| 9.2 | Make changes (quadrant, delete a gate, paste, change a coefficient) | Save button shows "Save changes •"; History lists each change with a time |
| 9.3 | `await saveDaughter()` (stubs from section 8) | Blob about the original size; button back to "Save"; toast names the file |
| 9.4 | Open the saved blob in an iframe; poll with `fr.contentWindow.eval(...)` | Changes present, coefficient preserved, History entries marked prior (`h.prior === true`), `_dirty === false` |
| 9.5 | `resetToAuthorGates()` in the saved copy | Deleted gate returns, author compensation returns, quadrant gone; `undo()` brings the working state back |
| 9.6 | Second save and reopen | Still opens; `_bundleObj.template` (the author's gates) is unchanged across generations |
| 9.7 | `showHistory()` | Modal lists entries newest first; Escape closes it |
| 9.8 | Locked guard | Dropping a file on the page does nothing; `importGates`/`loadFCS` are undefined |
| 9.9 | Unlocked daughter | Open/Import/Export present and working |
| 9.10 | Old files | `samples/CLL_Example_Small_FlowNG_shared.html` (built by older code, `format:1`) still opens as one workspace; it has no Save button (known). Saving a format 1 file (`build_test_daughter.py` uses it) writes `format:2` |
| 9.11 | Workspaces in a saved file | A two-workspace shared file reopens with both workspaces in the strip (`workspaces.length === 2`), the first active; a change made in the second one marks only that tab dirty (`•`), and `saveDaughter()` writes `format:2` with each workspace's own history; closing and Save buttons are hidden in the locked viewer |

## 10. Visual checks (screenshots)

Take a screenshot after loading `daughter_lod.html` (it exercises the progressive render path) and after the BTM import:

- **Stale-plot check (automatic):** after 12 s, hash each first-row canvas, force `p._lodLevel = 2; renderPlot(p)`, hash again. Expected: no differences. A difference means an old render painted over a new plot (the bug fixed in "stale first row").

```js
const hash = c => { const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let h = 0; for (let i = 0; i < d.length; i += 16) h = (h * 31 + d[i] + d[i + 1] * 3 + d[i + 2] * 7) | 0; return h; };
const first = plots.filter(p => p.tabId === activeTabId).slice(0, 6);
const settled = first.map(p => hash(document.getElementById('canvas-' + p.id)));
first.forEach(p => { p._lodLevel = 2; renderPlot(p); });
const fresh = first.map(p => hash(document.getElementById('canvas-' + p.id)));
JSON.stringify(first.filter((p, i) => settled[i] !== fresh[i]).map(p => p.id))   // expect []
```

- Linear axes show plain numbers, log and asinh show decade ticks with raised exponents; gate outlines and labels are visible; quadrant crosshair has four corner labels with percentages.
- Toolbar buttons are labelled, the active tool is highlighted, Undo/Redo grey out when empty.
- Tabs read "Name (n)  x" with a dashed "+ Tab"; tree rows show count, % of parent, `+`, `x`.
- Hover a toolbar button: a tooltip appears (a `title` exists on every visible control: query `button, select, input[type=range]` for an empty `title`).

## 11. Performance

Measure with `performance.now()` around synchronous calls (reliable even in a hidden pane) and by polling for async completion. Baselines from the reference Mac (3 tubes of about 33k events in the authoring app; 3 x 100k in the daughter). **Fail at more than 2x baseline, investigate at more than 1.5x.**

| Measure | Baseline |
|---|---|
| Load one LMD (parse + cofactors + first plot) | 100-150 ms |
| Import BTM template (106 gates, 255 plots), synchronous part | 970 ms |
| `renderAllPlots` active tab (12 plots, 33k events) | 30 ms (slowest plot 4 ms) |
| Switch through all 15 tabs | 520 ms |
| `evalGate` one gate, 33k events | 13 ms |
| `reevaluateAllGates` (31 gates, 33k) | 150 ms |
| `createQuadrant` / `undo` / `redo` call (33k) | 110 ms each |
| Recompensate after a coefficient change | 8 ms (+140 ms to re-gate) |
| Export Shareable HTML, 3 tubes | 160 ms, 3.4 MB |
| **Daughter, 3 x 100k events:** open to ready | 5.6 s (10 MB file) |
| `renderAllPlots` active tab (12 plots, 100k) | 670 ms (slowest 95 ms) |
| `evalGate` one gate, 100k | 150 ms |
| `reevaluateAllGates` (31 gates, 100k) | **2.1 s** |
| `createQuadrant` call (100k) | **1.3 s** |
| Save daughter (9.9 MB) | 335 ms |
| Reopen saved daughter | 5.4 s |

Known slow spots (not regressions, but the first things to improve): `reevaluateAllGates` and quadrant creation run on the main thread and freeze the page for seconds at 100k events; opening a 10 MB daughter takes several seconds because the bundle is decoded and every gate re-evaluated.

Scale test: build a bigger daughter by raising event caps in an export, or load a large FCS; check that the first plot appears within a few seconds and dragging a gate stays interactive (`evalGateLOD` x10 about 25 ms at 33k).

## 12. Browser compatibility checks

- **Safari-style load:** add `<script>delete window.requestIdleCallback; delete window.cancelIdleCallback;</script>` right after `<head>` in a copy of `FlowNG.html` and a daughter; load a file. Expected: loads and plots with no ReferenceError.
- `CompressionStream`/`DecompressionStream` are required for shared files (Safari 16.4+, Chrome, Edge, Firefox 113+); an older browser should fail with a visible message, not a blank page.
- Save As dialog (`showSaveFilePicker`) exists in Chrome/Edge only; elsewhere Save downloads. Test the download path by leaving the stub undefined.

## 13. Workspaces and the Pool

Start from a fresh page and load the fixtures (section 1); each check below uses `poolFiles`, `workspaces`, `getActiveWs()`.

| # | Do | Expected |
|---|---|---|
| 13.1 | Load 3 fixtures; read the sidebar | A **POOL (3)** node lists the files with tube names and tick boxes; no workspace; placeholder in the canvas; Import Template button visible, Add Plot / Export / Share hidden |
| 13.2 | Import the BTM template (7.1); then load the fixtures again and import it a second time | Two workspaces `BTM Triage Template v10` and `... (2)`; each has its own file ids (`[0,1,2]`, `[3,4,5]`), gate counts `[31,41,30]`, 255 plots, 255 `.plot-card` elements in the DOM while it is active; Pool is empty after each import |
| 13.3 | In workspace 2 delete a gate (`deleteGateFromTree(id, true)`), then `switchWorkspace` to 1 and back | Workspace 1 keeps `[31,41,30]` and its own undo depth (1); workspace 2 keeps `[2,41,30]` and undo depth 2; the strip shows `•` only on a dirty workspace; no console errors |
| 13.4 | `undo()` in each workspace | Only that workspace's change is undone; the other is untouched |
| 13.5 | Starter template: load the 3 fixtures, tick two and click Starter (or `generateStarterWorkspace()`) | One tab per tube named by tube, 4 plots per tube in order CD45 vs Time, FSC-H vs FSC-A, FSC-A vs SSC, CD45 vs SSC (Y vs X); no gates; the toast lists skipped plots when a channel is missing (check `fcsFiles[0].params` has `CD45` in the stain label) |
| 13.6 | `openPoolInWorkspace()` with one Pool file, and `addPoolFileToWorkspace(id)` with a workspace open | Blank workspace named by tube (never a file name) with one plot; the second moves the file into the live workspace with a default plot |
| 13.7 | `closeWorkspace(activeWsId)` twice | Files and plots of that workspace are gone, another workspace becomes live with its DOM rebuilt; closing the last one returns to the welcome drop zone with the sidebar hidden |
| 13.8 | `removeFile` on a Pool file | Leaves the Pool, its compute worker is terminated, workspaces untouched |
| 13.9 | Shared round trip (section 8 then 9.11) with two workspaces | Both restore with their plots and history |
| 13.10 | Locked viewer (`daughter.html`) | Workspace strip shows, but the close buttons and "+ Template" are hidden; `typeof openPoolInWorkspace === 'undefined'` |

## 14. Reporting

End every run with a short report:

1. A pass/fail table per section run (use the section numbers).
2. Console errors found (exact text) or "none".
3. Timings that exceeded 1.5x baseline.
4. What could **not** be tested: real mouse drags (synthetic events only), real Safari/Firefox, files over 500,000 events, the real Save As dialog.
5. Fixture state left behind: close extra tabs, stop the server (`pkill -f "http.server 8770"`), delete nothing in the repo.

When a test fails, fix the cause and rerun that section and section 2; do not weaken the check.
