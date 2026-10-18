# FlowNG: Privacy-Focused Browser-Based Flow Cytometry Analysis

**FlowNG** is a lightweight, client-side flow cytometry analysis and visualization tool that runs entirely in your web browser. Upload your FCS files and start analyzing with interactive gating, spectral compensation, and automatic cofactor optimization—all without your data ever leaving your computer.

**[Try the live demo →](./FlowNG.html)** | [Privacy Policy](#privacy-and-data-security)

---

## Key Features

### 🎯 Interactive Gating
- **Polygon, rectangle and quadrant gates**: a quadrant is one draggable crosshair whose Q1–Q4 populations (clockwise from the upper right) always follow its centre and partition the parent exactly
- **Select, edit and delete**: drag a gate with Select, reshape it with Edit, remove it from the toolbar or the tree
- **Population tree**: counts and % of parent on every row, drag a row onto another to re-parent, drag its grip to reorder siblings (the gate lower in the tree wins shared cells; a child always beats its ancestors)
- **Right-click menu**: rename / colour, copy, cut, paste (into any loaded file, matched by parameter name) and delete
- **Undo / redo**: gates, colours, order, compensation and cofactors (Ctrl/Cmd+Z, Shift+Z)
- **Kelly 21-colour palette**, with a "No Color" option for gates that should not stand out

### 📊 Visualization
- **Blended density plots**: every plot is a binned density. Each bin takes the count-weighted colour of the populations that own its events and bleaches toward white as it gets denser, so back-gated populations show up in their own colours
- **"+" dot toggle**: draw any population additionally as exact events
- **Bins slider** per plot (32–512 per axis)
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
- Options: cap events per file (large files default to 500,000), rename the tubes / files (or use Sample 1, 2, …), strip FCS header metadata (default; may contain patient IDs), and **Locked viewer** (default on)
- **Locked viewer** removes the FCS/LMD parsers, demo data, template import/export and the share code from the file, hides the open/import/export buttons and stops dropped files. Recipients can still gate, compensate, undo and reset to your gates. The embedded events can still be read with View Source or developer tools, so it limits casual reuse rather than preventing extraction

### 📁 File Format Support
- **FCS 2.0, 3.0, 3.1** standard flow cytometry file format
- **Beckman Coulter LMD** files (embedded FCS 2.0 log-transformed + FCS 3.0 raw data)
- **Demo mode**: Included PBMC dataset with 9 FCS parameters for exploration without real data

### 🔒 Privacy-First Design
- **Client-side only**: All data processing occurs in your browser; data never transmitted to any server
- **No external dependencies**: Single-file application (~260KB) with zero external libraries
- **Works offline**: No internet connection required after initial page load
- **Transparent code**: GNU AGPLv3 licensed with full source visible in the HTML file

### 🚀 Performance & Technology
- **Web Workers**: Non-blocking FCS parsing and gate evaluation
- **Level-of-detail rendering**: subsampled while you drag, refined when idle
- **Background rendering queue**: Pre-renders off-tab plots when idle for instant tab switching
- **Cross-browser compatibility**: Works on Chrome, Firefox, Safari, Edge on Windows, macOS, and Linux

---

## Quick Start

### 1. Open the Application
Simply open **FlowNG.html** in your web browser. No installation or server required.

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

**Export & Templates**
- Save gating hierarchies as reusable templates for batch processing
- Templates capture gate definitions, colors, and hierarchy for import into other files

### Toolbar

| Tool | Function |
|------|----------|
| **Select** | Drag a gate to move it; with a plot selected, drag an arcsinh axis marker to set its cofactor |
| **Polygon** | Click to draw a polygon gate |
| **Rect** | Drag to draw a rectangular gate |
| **Quadrant** | Click to place a crosshair that creates Q1–Q4; drag the crosshair with Select or Edit |
| **Edit** | Drag gate vertices to reshape |
| **Comp** | Drag a plot's top or right edge to tune one spillover coefficient |
| **Delete** | Click a gate to remove it |
| **Autocomp** | Outline a population that should sit flat in the pair of axes; the spillover coefficient between them is fitted automatically |
| **Undo / Redo** | Step back / forward through gate, colour, order, compensation and cofactor changes |

**Keyboard**: `Ctrl/Cmd+Z` undo, `Ctrl/Cmd+Shift+Z` or `Ctrl/Cmd+Y` redo, `Del` remove selected plot(s), `Esc` cancel a gate or deselect.

**Hover for help.** The toolbar tools, header buttons, plot controls (population, axes, bins, grip, expand, swap), tabs, cofactor markers and tree controls (`+`, `×`, grip) all have tooltips: hold the pointer over one and it says what it does and what it needs (for example, Comp and Autocomp say that both axes must be in the spillover matrix).

### Quick Instructions (the lower-left panel)

The panel at the bottom of the left sidebar is a live cheat sheet that matches the controls below.

**Toolbar**

| Control | What it does |
|---|---|
| **Select** | Drag a gate to move it. With a plot selected, drag the blue marker on an arcsinh axis to change that channel's cofactor |
| **Polygon** | Click points around a population; click the first point (or double-click) to close the gate |
| **Rect** | Drag a rectangle |
| **Quadrant** | Click to place a crosshair (Q1–Q4, clockwise from upper right); drag it with Select or Edit |
| **Edit** | Drag gate corner points to reshape a gate |
| **Comp** | Drag a plot's top or right edge to tune one spillover coefficient |
| **Autocomp** | Outline a population that should sit flat; the spillover coefficient is fitted for you |
| **Delete** | Click a gate to remove it |
| **Undo / Redo** | `Ctrl/Cmd+Z`, `Ctrl/Cmd+Shift+Z` or `Ctrl/Cmd+Y` |

**Plots**

| Control | What it does |
|---|---|
| Click a plot's header | Select that plot |
| Click empty canvas | Deselect all |
| `Shift`+click / `Ctrl`or`⌘`+click | Range-select / toggle plots; axis, population and bin changes then apply to every selected plot (the LOG/LIN/ASINH scale stays per plot) |
| `Del` / `⌫` | Remove the selected plot(s) |
| `Esc` | Cancel a gate you are drawing, and deselect all |
| Drag ⠿ | Reorder plots, or drop one on a tab to move it there |
| Right-click the plot | Set axis min/max and the arcsinh cofactor numerically |
| Right-click the plot header | Switch the plot's source file (when several files are loaded) |
| Bins slider | Density bins per axis (32–512) |

**Tabs**: right-click or double-click a tab to rename it, `✕` closes it, `+ Tab` adds one.

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
Select a plot in **Select** mode. Each arcsinh axis shows a small blue marker. Drag it along the axis: the position is geometric (1 to 100,000), the ticks and gate outlines follow live, and the zero point stays pinned at 20% of the axis. On release every gate is re-evaluated and every plot of that channel adopts the new cofactor. `Esc` during the drag puts the old value back, and **Undo** reverses a committed change.

### Copying Gates
Right-click a gate row and choose **Copy** (or **Cut**), then right-click another row, in any loaded file, and choose **Paste**. The copy is a new independent gate under that row. It is matched to the target file by parameter name, so pasting into a file that lacks one of its channels is refused with a message. Quadrant gates cannot be copied.

### Plot Configuration

**Axis Scaling Options**
1. Right-click any axis to open the scale menu
2. Select transformation type:
   - **LINEAR**: Standard arithmetic scale
   - **LOG**: Logarithmic scale (log₁₀)
   - **ASINH**: Inverse hyperbolic sine (arcsinh) for flow cytometry data

**Global Settings**
- Click the **Settings** (⚙) button to access:
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

**Enable automatic optimization:**
1. Open **Axis Range** modal (right-click plot axis or use toolbar)
2. Check "Auto-optimize cofactors"
3. Click "Apply" to calculate and apply optimal values
4. Optimization applies to all plots if selected

#### Spectral Compensation (Spillover Adjustment)
For multi-colour experiments with compensation matrices:

1. FCS files with `$SPILLOVER` keywords load compensation automatically
2. **Comp**: drag a plot's top or right edge to adjust one coefficient; the plot updates live and every gate is re-evaluated when you let go
3. **Autocomp**: outline a population that should sit flat in that pair of axes (at least 100 events). FlowNG fits the robust slope of Y on X inside the outline (equal-count bins, median Y per bin, weighted line) and adds it to the X→Y coefficient, repeating up to three times
4. Both are undoable

#### Level-of-Detail (LOD) Rendering
For large datasets (>1M events):
- Initial subsampled render appears instantly
- Full-resolution render automatically upgrades when browser is idle
- Maintains smooth interaction while dragging gates and axis handles
- No user configuration needed—happens automatically

#### Background Rendering Queue
- Plots in non-active tabs are pre-rendered when browser is idle
- Clicking between tabs shows cached render immediately
- Automatic queue management based on browser activity

### Performance & Large Files

**Handling Large Datasets**
- **Level-of-detail rendering**: Subsampled preview with automatic high-resolution upgrade
- **Web Worker processing**: Gate evaluation and parsing off main thread

**Typical Performance**
- Files up to 10M events: Real-time interactive gating
- Files 10-100M events: LOD rendering with ~500ms full render
- Compensation adjustment: Interactive with live preview

---

## Converting Kaluza Templates

`scripts/kaluza_to_flowng.py` converts a Kaluza `.composite` / `.protocol` file into a FlowNg template (`*_FlowNgtmplt.json`) you can load with **Import Template**. It uses only the Python standard library; run it with [uv](https://docs.astral.sh/uv/):

```bash
# See the tubes (Kaluza datasets) and plot sheets in the template
uv run scripts/kaluza_to_flowng.py "BTM Triage Template v10.composite" --list

# Convert; pass the LMD files in Kaluza dataset order (B, T, myeloid for BTM)
uv run scripts/kaluza_to_flowng.py "BTM Triage Template v10.composite" \
    --lmd "B.LMD" --lmd "T.LMD" --lmd "M.LMD" -o btm_FlowNgtmplt.json
```

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
- **Multi-sample analysis**: Load multiple FCS files in separate tabs
- **Consistent gating**: Export/import gate templates for standardized analysis
- **Population tracking**: Monitor population percentages across samples

---

## Known Limitations

### Not for Clinical Diagnostic Use
FlowNG is a research and educational tool **not intended for clinical diagnostic purposes**. While suitable for exploratory analysis and research workflows, it has not undergone validation for clinical use.

### Browser Requirements
- Modern browser with ES6 support: Chrome/Edge 60+, Firefox 55+, Safari 12+
- 4GB+ RAM recommended for files >100M events

### Current Limitations
- No support for time-resolved kinetic data
- Limited to 2D plot visualization (3D visualization not supported)
- No built-in statistical testing (t-test, ANOVA, etc.)
- No batch export of populations as FCS files
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
- **Manual application**: Use Spillover Adjust tool to manually correct if needed

### Slow Performance
- **Large files**: Use LOD rendering (enabled by default) to speed up interaction
- **Bins**: lower a plot's bins slider to make density rendering cheaper
- **Browser memory**: Close other tabs and applications to free memory

---

## Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 60+ | ✅ Full support |
| Firefox | 55+ | ✅ Full support |
| Safari | 12+ | ✅ Full support |
| Edge | 79+ | ✅ Full support |
| Opera | 47+ | ✅ Full support |

Plots render on a 2D canvas, so no GPU features are required.

---

## License & Attribution

**FlowNG** © 2026 David P. Ng, MD

Licensed under **GNU Affero General Public License v3.0** (GNU AGPLv3). See LICENSE file for details.

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

**Q: How do I optimize axis transformation cofactors?**  
A: Right-click any plot axis, enable "Auto-optimize cofactors," and click Apply. FlowNG calculates optimal arcsinh cofactors using the OTflow algorithm.

**Q: Can I work with multiple files at once?**  
A: Yes. Load multiple FCS files—each opens in a separate tab at the top of the plot area.

---

## Changelog

### Version 1.0 (Current)
- Initial release with core gating and analysis features
- Blended density rendering
- Automatic cofactor optimization via OTflow algorithm
- Spectral compensation with interactive spillover adjustment
- Multi-tab support and background rendering queue
- Demo mode with sample PBMC data
- Support for FCS 2.0/3.0/3.1 and Beckman Coulter LMD files

---

**Happy analyzing! 🔬**

For the latest updates and to report issues, visit the [FlowNG GitHub repository](../../).
