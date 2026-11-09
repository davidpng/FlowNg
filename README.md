# FlowNG: Privacy-Focused Browser-Based Flow Cytometry Analysis

**FlowNG** is a lightweight, client-side flow cytometry analysis and visualization tool that runs entirely in your web browser. Load your FCS or LMD files and start analyzing with interactive gating (polygon, rectangle and quadrant), spectral compensation, and automatic cofactor optimization. When you are done, export your analysis as one self-contained HTML file that a colleague can open, continue, save and pass on, all without your data ever leaving your computer.

**[Try the live demo →](https://davidpng.github.io/FlowNg/FlowNG.html)** | **[Open the example shared analysis →](https://davidpng.github.io/FlowNg/samples/Complex_Analysis_FlowNg.html)** | **[Check a shared file →](https://davidpng.github.io/FlowNg/check/)** | [Privacy Policy](#data-security--privacy)

The demo runs in your browser from GitHub Pages; the page is static and nothing you load is uploaded.

[![FlowNG walkthrough video on YouTube](https://img.youtube.com/vi/Xj0Y3ohmiGs/maxresdefault.jpg)](https://youtu.be/Xj0Y3ohmiGs)

**[Watch the walkthrough video on YouTube →](https://youtu.be/Xj0Y3ohmiGs)**: loading LMD files, importing a template, selecting plots, gating, cofactors, compensation and sharing, with the keys and mouse buttons shown on screen.

---

## Key Features

### 🎯 Interactive Gating
- **Polygon, rectangle and quadrant gates**: a quadrant is one draggable crosshair whose Q1–Q4 populations (clockwise from the upper right) always follow its centre and partition the parent exactly
- **Select, edit and delete**: drag a gate with Select, reshape it with Edit, remove it from the toolbar or the tree
- **Population tree**: counts and % of parent on every row, drag a row onto another to re-parent (any gate, including a sibling that shares events with it; only moving a gate under its own descendant is refused), drag its grip to reorder siblings (the gate lower in the tree wins shared cells; a child always beats its ancestors)
- **Right-click menu**: rename / colour, copy, cut, paste (into any loaded file, matched by parameter name) and delete
- **Undo / redo**: gates, colours, order, compensation and cofactors (Ctrl/Cmd+Z, Shift+Z)
- **Kelly 21-colour palette**, with a "No Color" option for gates that should not stand out

### 📊 Visualization
- **Blended density plots**: every plot is a binned density. Each bin takes the count-weighted colour of the populations that own its events and bleaches toward white as it gets denser, so back-gated populations show up in their own colours
- **"+" dot toggle**: draw any population additionally as exact events
- **Plot size slider** on the tab strip: one size for every plot on the active tab (280–800 px), saved with templates and shared files
- **Bins slider** per plot (32–1024 per axis; high values suit the expanded view)
- **Decade ticks**: log and arcsinh axes label each power of ten with a raised exponent (arcsinh also labels zero and the negative decades)
- **Axis cofactor handles**: select a plot, then drag the blue marker on an arcsinh axis to set that channel's cofactor live; gates are re-evaluated on release
- **Tabs**: named tabs with plot counts, right-click to rename, drag a plot onto a tab to move it

### ⚙️ Advanced Analysis Capabilities
- **Automatic arcsinh cofactor optimization**: Uses OTflow algorithm (Folcarelli et al., 2022) to automatically calculate optimal transformation cofactors for fluorescent parameters
- **Spectral compensation**: Apply compensation matrices from FCS `$SPILLOVER` keywords with interactive live adjustment
- **Multiple axis scales**: LOG, LINEAR, and ASINH transformations with per-plot or global configuration
- **Level-of-detail (LOD) rendering**: Subsampled preview rendering with automatic high-resolution upgrade during idle time for smooth interaction with large datasets

### 🔗 Shareable HTML
- **Export Shareable HTML** writes one self-contained HTML containing the event data (gzip), compensation, gates, plots and axis settings — not the original FCS/LMD file
- Recipients open it with your gating applied and can move, redraw and add gates; **Reset to author's gates** restores yours
- Events are stored once (the uncompensated values plus the spillover matrix; compensation is rebuilt on open), column by column in byte planes and gzipped, as text inside the HTML. A browser cannot embed raw binary in an HTML file, so base64 text is the compact single-file option. A 34k-event, 14-parameter LMD (3.0 MB) shares as about 1.3 MB
- **Saving a shared file and its History**: a shared file keeps working. Click **💾 Save** to write a new copy that contains your changes (gates, plots, axis settings, compensation) and the **🕘 History**, then pass that copy on; the next person opens it exactly where you left off. The original file is never altered, so keep it or download it again to start over, and **↺ Reset to author's gates** inside any copy goes back to the author's gates and compensation (undoable). In Chrome and Edge, Save opens a Save As dialog, so you can choose where the copy goes; elsewhere it downloads. The save button shows a dot while there are unsaved changes, and the browser warns before closing with unsaved changes
- **History**: every gating action is logged with its time and a plain description, for example `Drew gate "Blasts" on SS INT LOG vs CD45 KO (984 events)`, `Moved gate "Lymphs"`, `Adjusted spillover CD5 into CD20: 0.0000 to 0.0123`, `Set cofactor of CD19 ECD to 3085`, `Pasted gate "Viable" under "Singlets"`, plus undo, redo and reset. There are no user names or accounts, only what was done and when. The log keeps the latest 500 entries and travels inside saved files; an author's own history is included when exporting a shared file (file names in it are replaced with the tube names you chose)
- **Check before opening**: a shared file is a program, not a document. Drop it on the **[FlowNG Check page](https://davidpng.github.io/FlowNg/check/)** to confirm it contains only released FlowNG code and a data block (see [Checking a shared file](#checking-a-shared-file-before-opening-it))
- **Example**: [`samples/Complex_Analysis_FlowNg.html`](samples/Complex_Analysis_FlowNg.html) is a shared analysis with several tabs of gated plots. Download it and open it in a browser.
- **Privacy**: file names, dates and IDs often identify a patient. The export dialog asks you to rename the tubes, drops collection date/time and IDs from the FCS header, and writes only the pristine app, never the live page. Check the result before sharing
- Options: cap events per file (large files default to 500,000), rename the tubes / files (or use Sample 1, 2, …), strip FCS header metadata (default; removes sample IDs and collection dates and times), **Anonymise** (default on; leaves out the file's creation and export times and your History, so nothing in it says who made it or when; untick to keep your History for teaching), **Secure distribution channel** (see below), and **Locked viewer** (default on)
- **Locked viewer** removes the FCS/LMD parsers, demo data, template import/export and the share code from the file, hides the open/import/export buttons and stops dropped files. Recipients can still gate, compensate, undo and reset to your gates. The embedded events can still be read with View Source or developer tools, so it limits casual reuse rather than preventing extraction

### 📁 File Format Support
- **FCS 2.0, 3.0, 3.1** standard flow cytometry file format
- **Beckman Coulter LMD** files (embedded FCS 2.0 log-transformed + FCS 3.0 raw data)
- **Demo mode**: Included PBMC dataset with 9 FCS parameters for exploration without real data

### 🔒 Privacy-First Design
- **Client-side only**: All data processing occurs in your browser; data never transmitted to any server
- **No external dependencies**: Single-file application (about 350 KB) with zero external libraries
- **Works offline**: No internet connection required after initial page load
- **Transparent code**: GNU AGPLv3 licensed with full source visible in the HTML file

### 🚀 Performance & Technology
- **Web Workers**: Non-blocking FCS parsing and gate evaluation
- **Level-of-detail rendering**: large populations are drawn from a sample while you drag and refined when idle
- **Count-based density**: plots are a binned count, so drawing cost depends on events and the bins slider, not on any GPU
- **Cross-browser compatibility**: Works on Chrome, Firefox, Safari, Edge on Windows, macOS, and Linux

---

## Quick Start

### 1. Open the Application
Open the **[live demo](https://davidpng.github.io/FlowNg/FlowNG.html)**, or download **FlowNG.html** and open it in your web browser. No installation or server required.

```
Double-click FlowNG.html → opens in default browser
```

### 2. Load Sample Data (Optional)
Click the **Demo** button to load a sample PBMC dataset (9 parameters) for learning without your own files.

### 3. Upload Your FCS File
- Drag and drop an FCS file onto the gray upload area, or
- Click **Choose Files** and select your FCS file from disk

Supported formats: FCS 2.0, 3.0, 3.1, and Beckman Coulter LMD files

### 4. Create Your First Gate
1. Click **Polygon** in the toolbar
2. Click points on the plot to outline your population
3. Click the first point (or double-click) to close the gate
4. Name it; it appears in the population tree with its count and % of parent

### 5. Explore & Analyze
- **Select** moves a gate; **Edit** reshapes it; **Undo / Redo** reverse any change
- **Gating tree**: expand it in the left sidebar; right-click a row for rename / colour / copy / paste / delete
- **Switch axes**: use the dropdowns under and beside each plot; right-click the plot for axis range and cofactor
- **Share**: **Export Shareable HTML** produces one file with the data and your gates (see below)

---

## User Guide

### File Management

**Loading Files**
- FCS files can be loaded individually or in batches
- Drag-and-drop: Drop one or more FCS files on the upload area
- File browser: Click "Choose Files" for standard file selection
- Demo mode: Click "Demo" to load sample PBMC dataset (9 parameters)

**File Information**
- File size, parameter count, and event count displayed in the status bar
- View raw FCS metadata: Open the settings menu to browse keyword/value pairs
- Compensation status indicated in status bar

**Workspaces and the Pool**
- Opened files wait in the **Pool** (top of the sidebar). A **workspace** is one loaded template with its own files, tabs, plots, gates, undo history and change log; the workspace strip above the tabs switches between them. Gates and edits in one workspace never touch another
- **Import Template** matches the template to files in the Pool and moves the matched files into a new workspace. Import the same template again (with other files from the Pool) for a second case; each import is its own workspace. A file belongs to one workspace only
- Tick files in the Pool, then **Open** puts them in a blank workspace (one default plot per file), or **Starter** generates a starter template: one tab per tube with CD45 vs Time, FSC-H vs FSC-A, FSC-A vs SSC and CD45 vs SSC (Y vs X), no gates. A plot is skipped, and reported, when its channel is missing. Gate it, then **Export Template** to keep it
- Closing a workspace (✕) removes its files and gates. Rename one with a double-click
- **Export Shareable HTML** writes every workspace into the one file (the Pool is not included); a file made by an older version opens as a single workspace

**Export & Templates**
- Save gating hierarchies as reusable templates for batch processing
- Templates capture gate definitions, colors, and hierarchy for import into other files
- **Matching a template to your files**: on import, each template file is matched to a loaded file by (1) the same file name, then (2) the same **tube name** (the instrument's test name, such as "LL panel B cell tube"), then (3) the **antibody panel** (a loaded file that has every fluorescent channel the template's gates use, preferring the closest panel). So a later acquisition of the same tube lines up even though its file name is new. The import dialog shows how each match was made, lets you change any of them, and offers "skip this section"; a tie between equally good panels is left unmatched rather than guessed. Templates saved before tube and panel were recorded still match by panel, worked out from their gates.
- Only version 3 templates can be imported: this app's own exports and the Kaluza converter's output. An older version 2 template is refused with a message
- Shared HTML files keep the tube name (not the file name) in the header so matching still works on them

### Toolbar

The top bar has two groups, each in two rows, laid out like FlowNg2. They appear once a file is loaded.

- **Workspace strip** (above the plot tabs): one tab per workspace, plus **+ Template** to import one
- **Left group, row 1 (drawing tools):** Select, Polygon, Rect, Quadrant, Edit, Comp, Delete
- **Left group, row 2:** Autocomp, Undo, Redo, History, + Add Plot
- **Right group, row 1 (files and templates):** Open FCS File, Export Template, Import Template, Export Shareable HTML, SpikeNG
- **Right group, row 2:** Settings, Save and Reset to author's gates (the last two only in shared files)

| Tool | Function |
|------|----------|
| **Select** | Drag a gate to move it; with a plot selected (click its top bar or empty space on it), drag an arcsinh axis marker to set its cofactor |
| **Polygon** | Click to draw a polygon gate |
| **Rect** | Drag to draw a rectangular gate |
| **Quadrant** | Click to place a crosshair that creates Q1–Q4; drag the crosshair with Select or Edit |
| **Edit** | Drag gate vertices to reshape |
| **Comp** | Drag a plot's top or right edge to tune one spillover coefficient |
| **Delete** | Click a gate to remove it |
| **Autocomp** | Outline a population that should sit flat in the pair of axes; the spillover coefficient between them is fitted automatically |
| **Undo / Redo** | Step back / forward through gate, colour, order, compensation and cofactor changes |
| **History** | Every change with its time; shared files keep it when saved |

**Keyboard**: `Ctrl/Cmd+Z` undo, `Ctrl/Cmd+Shift+Z` or `Ctrl/Cmd+Y` redo, `Del` remove selected plot(s), `Esc` cancel a gate or deselect. **Tool shortcuts** (all on the left hand, plain letters; the key is bold and underlined on each button): `S` Select, `G` Polygon, `R` Rect, `Q` Quadrant, `E` Edit, `C` Comp, `A` Autocomp, and `Del` / `⌫` Delete mode when no plot is selected (with plots selected it removes them instead). Shortcuts are ignored while typing in a field, with `Ctrl`/`⌘`/`Alt`/`Shift` held, while a dialog is open, and before a workspace is open. Choosing a tool by button or key deselects all plots, so the tool applies to every plot.

**Hover for help.** The toolbar tools, header buttons, plot controls (population, axes, bins, grip, expand, swap), tabs, cofactor markers and tree controls (`+`, `×`, grip) all have tooltips: hold the pointer over one and it says what it does and what it needs (for example, Comp and Autocomp say that both axes must be in the spillover matrix).

### Quick Instructions (the lower-left panel)

The panel at the bottom of the left sidebar is a live cheat sheet that matches the controls below.

**Toolbar**

| Control | What it does |
|---|---|
| **Select** | Drag a gate to move it. With a plot selected (click its top bar or empty space on it), drag the blue marker on an arcsinh axis to change that channel's cofactor |
| **Polygon** | Click points around a population; click the first point (or double-click) to close the gate |
| **Rect** | Drag a rectangle |
| **Quadrant** | Click to place a crosshair (Q1–Q4, clockwise from upper right); drag it with Select or Edit |
| **Edit** | Drag gate corner points to reshape a gate |
| **Comp** | Drag a plot's top or right edge to tune one spillover coefficient |
| **Delete** | Click a gate to remove it |
| **Autocomp** | Outline a population that should sit flat; the spillover coefficient is fitted for you |
| **Undo / Redo** | `Ctrl/Cmd+Z`, `Ctrl/Cmd+Shift+Z` or `Ctrl/Cmd+Y` |

**Plots**

| Control | What it does |
|---|---|
| Click a plot's top bar (the row with the population menu and bins slider), or any empty space on the plot | Select (highlight) that plot; the cofactor markers need this. Empty space means blank canvas with Select, Edit or Delete (not while drawing or in Comp), the card margins, and the gaps beside the axis menus |
| Click empty canvas | Deselect all |
| `Shift`+click / `Ctrl`or`⌘`+click | Range-select / toggle plots; axis, population and bin changes then apply to every selected plot (including the LOG/LIN/ASINH scale: clicking the scale button on one selected plot gives that axis of every selected plot the same scale) |
| `Del` / `⌫` | Remove the selected plot(s) |
| `Esc` | Cancel a gate you are drawing, and deselect all |
| Drag ⠿ | Reorder plots, or drop one on a tab to move it there |
| Right-click the plot | Set axis min/max and the arcsinh cofactor numerically |
| Right-click the plot header | Switch the plot's source file (when several files are loaded) |
| Bins slider | Density bins per axis (32–1024) |

**Tabs**: right-click or double-click a tab to rename it, `✕` closes it, `+ Tab` adds one. The **Plot size** slider at the right end of the tab strip resizes every plot on that tab (each tab keeps its own size, saved with templates and shared files).

**Population tree**

| Control | What it does |
|---|---|
| `+` | Also draw this population as exact events (dots) |
| `×` | Delete the gate and its children (all of Q1–Q4 for a quadrant) |
| Right-click a row | Rename / colour, Copy, Cut, Paste, Delete |
| `Shift`+click a row | Rename / colour |
| Right-click a file row | Paste a copied gate at the top level of that file |
| Drag a row onto another | Re-parent the gate (onto the file row to un-parent) |
| Drag ⠿ above or below a sibling | Reorder; the gate lower in the tree wins shared cells |
| Click a gate's name | Jump to (or create) the plot where it was drawn |

### Compensation, Step by Step

Both tools need a file with a spillover matrix (an FCS `$SPILLOVER` keyword, or a Beckman Coulter LMD file) and a plot whose **two axes are both fluorescence channels in that matrix**. On any other pair the tooltip says so.

**Comp — adjust one coefficient by hand**
1. Choose **Comp** and make a plot with the two channels you want to compare (for example CD5 vs CD20).
2. Drag the plot's **top edge** left or right to change how much the Y channel spills into X, or its **right edge** up or down to change how much X spills into Y. A badge shows the coefficient.
3. The plot recompensates live. When you let go, every gate is re-evaluated, so counts and percentages in the tree update.
4. **Undo** reverses it.

**Autocomp — let FlowNG fit one coefficient**
1. Make a plot of the two channels with the spill problem; set the plot's population to the cells you trust (for example Lymphs).
2. Choose **Autocomp**.
3. Click points around a population that should sit flat in this pair, such as the negative or single-positive cloud that currently slopes. Click the first point (or double-click) to close the outline. It needs at least 100 events inside.
4. FlowNG takes the events in the outline, bins them by X into 20 equal-count bins, takes the median Y of each bin, and fits a weighted line through those medians. It adds that slope to the X→Y spillover coefficient and repeats up to three times (stopping when the slope falls under 0.0001). A toast reports the coefficient before and after; if the outlined population is already flat, nothing changes and nothing is added to the undo history.
5. All gates are re-evaluated. **Undo** restores the old matrix and counts, and you can run Autocomp again on another pair to fix it one pair at a time.

Autocomp fits one pair at a time from the population you outline; it is not the full AutoSpill algorithm that learns a whole matrix from single-stain controls. The outline is temporary and never becomes a gate.

### Changing a Cofactor by Dragging
1. **Select the plot** by clicking its **top bar** (the row with the population menu and the bins slider) or any empty space on it (blank canvas with Select active, the card margins). The plot gets a blue outline. Clicking on a gate or while drawing does not select it.
2. Make sure **Select** is the active tool. Each **ASINH** axis of the selected plot now shows a small blue marker (axes set to LIN or LOG have none).
3. Drag the marker along the axis: the position is geometric (1 to 100,000), the ticks and gate outlines follow live, and the zero point stays pinned at 20% of the axis.
4. On release every gate is re-evaluated and every plot of that channel adopts the new cofactor. `Esc` during the drag puts the old value back, and **Undo** reverses a committed change.

If the markers are missing, check that the plot is highlighted, that Select is active, and that the axis button reads ASINH. You can also right-click a plot and type a cofactor in the Axis Range dialog.

### Checking a shared file before opening it

A shared analysis is a single HTML file, which means it is also a program: anyone who changes it can make it do something else when you open it, and it will look the same. So check it first.

1. Open the **[FlowNG Check page](https://davidpng.github.io/FlowNg/check/)** (type or bookmark that address; do not follow a link in the email that sent you the file).
2. Drag the shared file onto the box, or click the box and choose it. The file is read on your computer and is not uploaded.
3. **Green, "Genuine FlowNG file"**: the program inside is an unmodified FlowNG release and the rest of the file is data only. The page also shows the analysis name, how many files and events it holds, which FlowNG build made it, and the file's SHA-256 (the sender can send you theirs separately to compare). Open the file as usual.
4. **Red, "Do not open this file"**: the page says why (the code is not any released FlowNG, the file has been changed, the data block is wrong, or it is not a shared FlowNG file at all). Ask the sender for a fresh copy from a source you trust.

- **Anyone can make a file that passes.** The check does not depend on who made the file, only on the file being built from a FlowNG release, so teachers, test providers and students can all share files and stay anonymous. A release is a pull request merged into the main branch.
- **Beta:** the list starts at 7 November 2026, and files from releases that had a known problem (names not escaped in the page) show red with an explanation. Open the analysis in the current FlowNG and share it again.
- **Update to the newest FlowNG** (green files only): puts the same analysis into the newest release and downloads it as a new file, after checking that the new file passes too. A locked viewer stays locked.
- **What green does not mean:** the analysis is correct, or that the file has no patient information (see the privacy notes under Shareable HTML). It also cannot protect you from a fake copy of the Check page, so use only the official address: `https://davidpng.github.io/FlowNg/check/`.
- **No network, no GitHub?** Opening a shared file never contacts anything; the Check page is an extra. If the Check page cannot be reached, use the **offline copy**: one HTML file with the list of releases and the newest FlowNG built in, which uses no network at all. Get it from the same trusted channel as the files (it is made with `scripts/build_offline_check.py` and handed out with each release; it shows how recent its list is, and a file from a newer release shows red until you get a newer copy).
- **Distributing files over a secure channel** (test providers, teachers): run `scripts/check_shared.py file1.html file2.html …` once before publishing. It uses the same check, prints PASS or FAIL for each file, and writes `SHA256SUMS` for the passing ones. Publish only those files, with `SHA256SUMS`, from a site you control. Recipients who get files from that site do not need to run the online check.
- **Sending files by email or chat** instead: tell recipients to check them at the official address. In **Export Shareable HTML**, leave **Secure distribution channel** unticked (default) and the file shows a small reminder to check it when opened, and the export dialog gives you a message to paste with the file's SHA-256. Tick the box when you publish the file yourself from a site you control: no reminder is shown.
- The list of releases is `check/manifest.json`. It is rebuilt for each merged pull request with `scripts/build_manifest.py` (releases are merge commits on main from 7 November 2026; branch commits are not releases), and a build with a problem can be withdrawn through its `revoked` list. How it works, what is not yet done (a stricter content policy in the app itself, an anonymise option and optional author signing in the share dialog) and how to scan a file yourself are in [`doc/SECURITY.md`](doc/SECURITY.md).

### Export to FCS and SpikeNG (full version only)

Right-click a population (or a file) and choose **Export events as FCS…** to save its events as a minimal FCS file with identifying metadata removed. **💉 SpikeNG** (toolbar) then merges two such files: the *schlemiel* (donor population) is spiked into the *schlimazel* (recipient). It checks the column labels match first, then either places the spike after the recipient with a time gap of 3% of the longer acquisition (educational), or interleaves it at random positions (proficiency testing). Enter the spike as a percentage of the recipient's events; an answer key of the spiked rows can be downloaded with the result. Exports keep the raw values and the spillover matrix, and SpikeNG merges raw values and applies the recipient's matrix to all events. Not available in locked shared files. See doc/SPEC.md section 14.

### Copying Gates
Right-click a gate row and choose **Copy** (or **Cut**), then right-click another row, in any loaded file, and choose **Paste**. The copy is a new independent gate under that row. It is matched to the target file by parameter name, so pasting into a file that lacks one of its channels is refused with a message. Quadrant gates cannot be copied.

### Plot Configuration

**Axis Scaling Options**
Click the **LIN / LOG / ASINH** button next to an axis's parameter drop-down to cycle its scale (each plot keeps its own scale, unless 2+ plots are selected, in which case they all take the same new scale on that axis):
   - **LINEAR**: Standard arithmetic scale
   - **LOG**: Logarithmic scale (log₁₀)
   - **ASINH**: Inverse hyperbolic sine (arcsinh) for flow cytometry data, with decade ticks including zero and the negative decades

**Global Settings**
- Click the **Settings** (⚙) button to access:
  - **Asinh cofactor**: one cofactor applied to every arcsinh axis (the per-channel optimum is the default; drag a marker to tune a single channel)
  - **Min Value Percentile**: set each fluorescent axis's lower limit from that percentile of its data

**Per-Plot Configuration**
- Right-click a plot to set manual axis ranges (min/max) and the arcsinh cofactor
- Or select the plot and drag the blue marker on an arcsinh axis; the zero point stays pinned at 20% of the axis while you drag, and `Esc` puts the old value back
- The cofactor is per file and channel, so every plot of that channel follows

### Gating Workflow

**Creating Gates**
1. Pick Polygon, Rect or Quadrant
2. On the target plot, click vertices, drag a rectangle, or click to place the crosshair
3. Gates evaluate against their parent population; counts and % of parent update in the tree

**Gate Hierarchy and Colour**
- Child gates filter their parent (standard flow cytometry logic); drag a tree row onto another to re-parent it, or onto "All Events" to un-parent it
- A plot shows its population plus every gate under it. Each density bin is coloured by the populations that own its events: the deepest gate owns a cell, and among siblings the one lower in the tree wins, so dragging a row's grip (⠿) above or below a sibling changes who wins a shared region
- Right-click a row to rename it, pick a colour or "No Color", copy / cut / paste a gate, or delete it. Paste always creates a new independent gate under the row you right-clicked, in any loaded file that has the same parameter names
- Click **+** on a row to also draw that population as exact events

**Population Analysis**
- Event count and % of parent next to each population

### Advanced Features

#### Automatic Cofactor Optimization
FlowNG uses the **OTflow algorithm** (Folcarelli et al., 2022) to automatically calculate optimal transformation cofactors for arcsinh scaling. The algorithm:
- Analyzes the distribution of fluorescent parameters using kernel density estimation (KDE)
- Evaluates normality using Jarque-Bera and Bartlett statistics
- Selects cofactors that minimize deviation from normality
- Automatically excludes scatter parameters (FSC, SSC) and time channels

**Where you see it:** the optimum is computed automatically when a file loads and is each channel's starting cofactor. You can change it three ways: drag the blue marker on an arcsinh axis (see *Changing a Cofactor by Dragging*), right-click a plot to type a cofactor in the Axis Range dialog, or set one cofactor for every arcsinh axis from **Settings**. Every change is undoable and recorded in History.

#### Spectral Compensation (Spillover Adjustment)
For multi-colour experiments with compensation matrices:

1. FCS files with `$SPILLOVER` keywords load compensation automatically
2. **Comp**: drag a plot's top or right edge to adjust one coefficient; the plot updates live and every gate is re-evaluated when you let go
3. **Autocomp**: outline a population that should sit flat in that pair of axes (at least 100 events). FlowNG fits the robust slope of Y on X inside the outline (equal-count bins, median Y per bin, weighted line) and adds it to the X→Y coefficient, repeating up to three times
4. Both are undoable

#### Level-of-Detail (LOD) Rendering
Populations above 100,000 events are drawn from a sample while you interact, then refined to every event when the browser is idle. This keeps gate dragging and axis-handle dragging responsive; it needs no configuration.

### Performance & Large Files

Measured on one Mac (three tubes of about 33,000 events in the full app; three tubes of 100,000 events in a shared file). Your numbers will differ; the ratios are what matter.

| Action | Time |
|---|---|
| Load one LMD (parse, cofactors, first plot) | 0.1-0.15 s |
| Import a 106-gate, 255-plot template | about 1 s |
| Redraw a tab of 12 plots (33k events) | 30 ms |
| Re-evaluate every gate after a compensation or cofactor change (31 gates, 33k / 100k events) | 0.15 s / 2.1 s |
| Open a 10 MB shared file (3 x 100k events) | about 5.6 s |
| Save it again | 0.3 s |

Gate re-evaluation and quadrant creation run on the page itself, so at 100,000 events or more they pause the page for a second or two; moving a gate uses a sampled version while you drag so it stays smooth. Lower a plot's bins slider to make drawing cheaper, and cap events per file when exporting a shared file to keep it small.

---

## Converting Kaluza Templates

`scripts/kaluza_to_flowng.py` converts a Kaluza `.composite` / `.protocol` file into a FlowNg template (`*_FlowNgtmplt.json`) you can load with **Import Template**. It uses only the Python standard library; run it with [uv](https://docs.astral.sh/uv/):

```bash
# See the tubes (Kaluza datasets) and plot sheets in the template
uv run scripts/kaluza_to_flowng.py "samples/BTM Triage Template v10.composite" --list

# Convert; pass the LMD files in Kaluza dataset order (B, T, myeloid for BTM)
uv run scripts/kaluza_to_flowng.py "samples/BTM Triage Template v10.composite" \
    --lmd "B.LMD" --lmd "T.LMD" --lmd "M.LMD" -o btm_FlowNgtmplt.json

# All options
uv run scripts/kaluza_to_flowng.py --help
```

Then open FlowNG.html, load the three LMD files, click **Import Template**, choose the JSON, and match each template entry to its tube.

`samples/` holds the example files: the BTM Triage Template v10 as a FlowNg template (`BTM Triage Template v10_FlowNgtmplt.json`), the three `TEST SAMPLE` LMD files it matches, and a shared analysis (`Complex_Analysis_FlowNg.html`).

What is converted: gate hierarchy (polygons, rectangles, quadrants, boolean OR/AND/NOT populations), gate colours (`#rrggbb`; gates without a colour become "no colour"), axis scales (logicle is approximated as asinh, cofactor 300) and axis ranges, and every plot sheet as a tab with its plots. Linked copy gates are merged into their originals.

Notes:
- **Tubes are positional.** Kaluza templates do not name their tubes; entry *i* of the output is Kaluza dataset *i*. Give `--lmd` (or `--tube-names "B tube,T tube,M tube"`) in that order, and match each entry to the right loaded tube in the import dialog.
- **Parameter names come from the LMD.** FlowNg names FL channels by their stain label (`$PnS`), which differs per tube, so pass `--lmd` for every tube; without it, FL parameters cannot be mapped and are skipped on import.
- Use `--sheets` / `--exclude-sheets` to choose which plot sheets become tabs.
- Not converted: report/stat sheets, compensation (FlowNg uses the LMD `$SPILLOVER`), hinged-quadrant tilt (centre point only).

## Technical Details

### Technology Stack
- **Pure JavaScript**: No external libraries or frameworks
- **HTML5 Canvas**: 2D plot rendering (binned, colour-blended density plus exact-event dots)
- **Web Workers**: Asynchronous FCS parsing and gate evaluation
- **Modern Browser APIs**: File API, Drag & Drop, requestIdleCallback

### Data Security & Privacy
✅ **All processing is client-side**: No data transmission to servers  
✅ **No analytics**: No tracking, cookies, or telemetry  
✅ **Offline operation**: Works without internet connection  
✅ **Source visible**: Full code transparency (view HTML source)  
✅ **Shared files can be checked**: the [Check page](https://davidpng.github.io/FlowNg/check/) confirms a shared file is released code plus data only (see above)  
✅ **Open source**: GNU AGPLv3 licensed

### FCS File Format Support
- **FCS 2.0**: Keyword/value pairs, list mode data, log-transformed values
- **FCS 3.0**: Full TEXT, ANALYSIS sections, compensated data keywords
- **FCS 3.1**: Enhanced metadata, additional keyword structures
- **Beckman Coulter LMD**: Proprietary format with embedded FCS data

### Supported Parameters
- **Scatter**: Forward Scatter (FSC), Side Scatter (SSC), Height/Area/Width/Time variants
- **Fluorescence**: Any parameter labeled as fluorescent (FL1-FL10, BV, PE, APC, etc.)
- **Special**: Time channels, compensation markers

### Algorithm References
- **OTflow cofactor optimization**: Folcarelli, M., et al. (2022). "Automatic compensation of spectral overlap in flow cytometry using machine learning." *Cytometry A*, 101(8), 701-713.
- **Kernel Density Estimation**: Scott, D. W. (2015). *Multivariate Density Estimation: Theory, Practice, and Visualization*.

---

## Use Cases & Applications

### Research & Education
- **Flow cytometry training**: Demo mode provides sample data for learning
- **Exploratory data analysis**: Quick visualization and gating of clinical/research samples
- **Parameter optimization**: Interactive axis scaling and cofactor adjustment

### Pre-Clinical Analysis
- **Population gating workflows**: Hierarchical gate definition and refinement
- **Multi-color compensation**: Spectral overlap correction with live adjustment
- **Batch processing**: Template-based gating applied across multiple files

### High-Dimensional Analysis
- **Parameter selection**: Explore and gate high-parameter FCS files (9+ parameters)
- **Population discovery**: Identify and characterize distinct cell populations
- **Quality control**: Assess compensation adequacy and population separation

### Comparative Studies
- **Multi-sample analysis**: Load several files at once; each appears as its own root in the population tree and plots can be switched between files
- **Consistent gating**: Export/import gate templates for standardized analysis
- **Population tracking**: Monitor population percentages across samples

---

## Known Limitations

### Not for Clinical Diagnostic Use
FlowNG is a research and educational tool **not intended for clinical diagnostic purposes**. While suitable for exploratory analysis and research workflows, it has not undergone validation for clinical use.

### Browser Requirements
- A current Chrome, Edge, Firefox or Safari. Everything except shared files works in any browser with ES2020 support.
- **Shared files** also need `CompressionStream` / `DecompressionStream`: Chrome and Edge 80+, Firefox 113+, Safari 16.4+. Older browsers cannot open them.
- **Save As dialog** (choosing where Save puts a copy) is Chrome and Edge only; other browsers download the file to the usual folder.
- 4GB+ RAM recommended for files >100M events

### Current Limitations
- No support for time-resolved kinetic data
- Limited to 2D plot visualization (3D visualization not supported)
- No built-in statistical testing (t-test, ANOVA, etc.)
- Export to FCS is one population at a time (no batch export)
- The Check page proves a shared file contains released FlowNG code; it does not prove that released code has no bugs, and it only protects people who use it
- Single-file application (all features in one HTML file)

### Unsupported File Formats
- FlowJo .wsp or .workspace files
- Cytobank or proprietary software formats
- Most vendor-specific analysis-ready data (ARD) formats

---

## Troubleshooting

### File Won't Load
- **Check file format**: Ensure file is valid FCS format (FCS 2.0/3.0/3.1)
- **File size**: Very large files (>1GB) may take several minutes to parse
- **Browser memory**: Close other applications if you have <4GB available RAM

### Plots Don't Display
- **Few events**: a small population shows as faint single bins; click **+** on its tree row to draw exact events
- **Axis scaling**: Verify axes are set appropriately for your data range
- **Missing parameters**: Check that selected parameters exist in the file

### Compensation Not Working
- **$SPILLOVER keyword**: Verify FCS file contains valid `$SPILLOVER` keyword
- **Parameter names**: Check that spillover matrix parameter names match FCS parameters
- **Manual correction**: use the Comp tool (or Autocomp) to correct it; both need two axes that are in the spillover matrix

### Slow Performance
- **Large files**: LOD rendering is on by default; moving a gate stays smooth, but re-evaluating many gates takes a second or two at 100,000 events or more
- **Bins**: lower a plot's bins slider to make density rendering cheaper
- **Browser memory**: Close other tabs and applications to free memory

---

## Browser Compatibility

| Browser | Status |
|---------|--------|
| Chrome, Edge (80+) | ✅ Tested, full support including the Save As dialog |
| Firefox (113+) | Expected to work; shared files need 113 or newer. Not tested by the author |
| Safari (16.4+) | ✅ Tested by the author on Safari 26.6.2: works fully, including shared files. Save downloads the file (no Save As dialog). Earlier versions are untested |

Plots render on a 2D canvas, so no GPU features are required.

---

## Development and Testing

FlowNG is one file, `FlowNG.html` (main script plus two worker scripts). To work on it, serve the folder (`python3 -m http.server`) and open it; no build step.

| File | Purpose |
|---|---|
| [`doc/SPEC.md`](doc/SPEC.md) | Interface and interaction decisions, and why each was made |
| [`doc/SECURITY.md`](doc/SECURITY.md) | Security risks of a single-file HTML app and how to scan a copy |
| [`doc/TESTING.md`](doc/TESTING.md) | A step-by-step test guide with expected results and performance baselines. Say "run doc/TESTING.md" to have Claude run it, or follow it by hand |
| `scripts/build_test_daughter.py` | Builds a locked shared file from the working tree for testing (`--lod N` forces the large-population path, `--unlocked` keeps import/export) |
| `scripts/extract_js_for_graphify.py` | Pulls the scripts out of the HTML so graphify (the `graphifyy` Python package) can build a real call graph; the result is in `graphify-out/` (`GRAPH_REPORT.md`, `graph.html`) |
| [`check/index.html`](check/index.html), `check/manifest.json`, `scripts/build_manifest.py`, `scripts/build_offline_check.py`, `scripts/check_shared.py`, `scripts/test_check.py` | **FlowNG Check**: a page where anyone drops a shared file to confirm it contains released FlowNG code and a data-only block (live at `https://davidpng.github.io/FlowNg/check/` once merged), the manifest of released code hashes (main releases only), an offline copy of the page, a publisher-side batch check, and the tests. Run the scripts with `/usr/bin/python3` on macOS. See `doc/SECURITY.md` section 5 |
| `scripts/kaluza_to_flowng.py` | Kaluza template converter (see above) |

Notes for contributors: code between `/*@lite:begin*/` and `/*@lite:end*/` (and `<!--@lite:...-->`) is removed from locked shared files, so anything a locked file needs (Save, History, rendering, gating) must stay outside those markers. Worker scripts cannot call main-script functions; a helper used in a worker needs its own copy.

---

## License & Attribution

**FlowNG** © 2026 David P. Ng, MD

Licensed under **GNU Affero General Public License v3.0** (GNU AGPLv3); the notice is at the top of `FlowNG.html`.

### Key Algorithms & References
- **OTflow optimization**: Folcarelli et al. (2022)
- **Kernel Density Estimation**: Scott (2015)
- **Flow Cytometry Standards**: International Society for Advancement of Cytometry (ISAC)

### Acknowledgments
- Flow cytometry parameter definitions: BD Biosciences, Beckman Coulter, Sony Biotechnology
- Gate colours: Kelly's 22 colours of maximum contrast
- FCS file format specification: ISAC

---

## Support & Contributing

### Reporting Issues
Found a bug or have a feature request? Please open an issue on GitHub with:
- Description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Browser version and OS

### Contributing Code
FlowNG is open source under AGPLv3. Code contributions are welcome:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/description`)
3. Commit changes with clear messages
4. Submit a pull request

### Contact
For questions or collaboration: [Create an issue on GitHub](../../issues)

---

## Frequently Asked Questions (FAQ)

**Q: Is my data secure?**  
A: Yes. All data processing happens in your browser. Your data never leaves your computer or connects to any server.

**Q: Can I use this for clinical diagnostics?**  
A: No. FlowNG is designed for research and educational use only. It is not validated or intended for clinical diagnostic purposes.

**Q: What's the maximum file size?**  
A: Theoretically limited by available browser memory (~2GB on most systems). Typical FCS files with 10-100M events work smoothly.

**Q: Can I export my gated populations?**  
A: You can export gate templates for reuse on other files. Direct export of gated populations as FCS files is not currently supported.

**Q: Does it work offline?**  
A: Yes. After the initial page load, FlowNG requires no internet connection.

**Q: How are populations coloured on a plot?**  
A: Every plot is a binned density. Each bin takes the colour of the populations that own its events (the deepest gate owns a cell; among siblings the one lower in the tree wins) and bleaches toward white as it gets denser. Click **+** on a tree row to also draw that population as exact events.

**Q: Can I send someone my analysis without the FCS file?**  
A: Yes. **Export Shareable HTML** writes one HTML with the event data, compensation, gates and plots. Tick "Locked viewer" to remove the loading, importing and exporting code from the file so recipients can only gate and view.

**Q: How do I change an axis's cofactor?**  
A: FlowNG computes a starting cofactor for every fluorescent channel when a file loads (the OTflow algorithm). To change one, select the plot and drag the blue marker on its arcsinh axis, or right-click the plot and type a value.

**Q: Can I load several templates at once?**  
A: Yes. Each imported template becomes a workspace with its own files, tabs and plots; switch with the workspace strip. Load all your files first (they wait in the Pool), then import the templates one by one.

**Q: Can I work with multiple files at once?**  
A: Yes. Load several files; each appears as its own root in the population tree, plots can be pointed at any loaded file (right-click a plot's header), and the tabs across the top are pages of plots, not files. Gates can be copied between files, and a template with several sections can be matched to several files at once.

---

## Changelog

### Latest
- **Workspaces**: several templates loaded at once, each with its own files, tabs, plots, undo and history; a Pool for unassigned files; a starter-template generator; shared files hold every workspace
- **Shared analyses**: Export Shareable HTML, a locked viewer option, Save and History inside shared files, privacy-aware export (renamed tubes, no dates or IDs), single-copy compressed event storage, and a size estimate
- **Gating**: quadrant gates, undo/redo, Autocomp, right-click menu with copy/cut/paste, sibling reorder that sets colour priority, axis cofactor handles, and a "+" dot toggle
- **Plots**: blended density plots coloured by population, decade ticks, bins slider, labeled toolbar and tooltips; the zoom tool was removed
- **Templates**: matching by file name, tube name or antibody panel; version 3 only (version 2 import removed); Kaluza converter
- **Fixes**: Safari load error (`requestIdleCallback`), stale first-row plots on load
- **Cleanup**: about 1,100 lines of old WebGL/heatmap code removed; `TESTING.md` added

### Version 1.0
- Initial release with core gating and analysis features
- Automatic cofactor optimization via OTflow algorithm
- Spectral compensation with interactive spillover adjustment
- Multi-tab support
- Demo mode with sample PBMC data
- Support for FCS 2.0/3.0/3.1 and Beckman Coulter LMD files

---

**Happy analyzing! 🔬**

For the latest updates and to report issues, visit the [FlowNG GitHub repository](../../).
