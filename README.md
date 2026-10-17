# FlowNG: Privacy-Focused Browser-Based Flow Cytometry Analysis

**FlowNG** is a lightweight, client-side flow cytometry analysis and visualization tool that runs entirely in your web browser. Upload your FCS files and start analyzing with interactive gating, spectral compensation, and automatic cofactor optimization—all without your data ever leaving your computer.

**[Try the live demo →](./FlowNG.html)** | [Privacy Policy](#privacy-and-data-security)

---

## Key Features

### 🎯 Interactive Gating
- **Polygon gating**: Click to draw custom polygonal gates with full hierarchy support
- **Rectangular gating**: Quick axis-aligned selections for rapid analysis
- **Gate editing & deletion**: Modify gates after creation without re-drawing
- **Hierarchical gate management**: Organize gates with parent-child relationships and precedence control
- **19-color palette**: Automatically color-coded populations for easy identification

### 📊 Visualization Modes
- **Heatmap rendering** (GPU-accelerated): Fast 2D density heatmaps with inferno colormap for large populations
- **Dot scatter plots**: Individual event rendering for smaller populations
- **Adaptive rendering**: Automatically switches modes based on population size for optimal performance
- **Grid overlay**: Reference grid on plots for precise axis reading
- **Multi-tab support**: Organize and compare multiple plots simultaneously

### ⚙️ Advanced Analysis Capabilities
- **Automatic arcsinh cofactor optimization**: Uses OTflow algorithm (Folcarelli et al., 2022) to automatically calculate optimal transformation cofactors for fluorescent parameters
- **Spectral compensation**: Apply compensation matrices from FCS `$SPILLOVER` keywords with interactive live adjustment
- **Multiple axis scales**: LOG, LINEAR, and ASINH transformations with per-plot or global configuration
- **Level-of-detail (LOD) rendering**: Subsampled preview rendering with automatic high-resolution upgrade during idle time for smooth interaction with large datasets

### 🔗 Shareable HTML
- **Export Shareable HTML** writes one self-contained HTML containing the event data (gzip), compensation, gates, plots and axis settings — not the original FCS/LMD file
- Recipients open it with your gating applied and can move, redraw and add gates; **Reset to author's gates** restores yours
- Options: cap events per file, anonymize file names, strip FCS header metadata (default; may contain patient IDs)

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
- **WebGL GPU acceleration**: Fast heatmap rendering even with 10M+ events
- **Web Workers**: Non-blocking FCS parsing and gate evaluation
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
1. Click the **Polygon Gate** tool (⬡) in the toolbar
2. Click points on the plot to outline your population
3. Right-click or double-click to close the gate
4. Your new population appears in the sidebar with event count

### 5. Explore & Analyze
- **Pan**: Use the **Pan** tool (✥) to navigate plots
- **View gates**: Expand the gating hierarchy in the left sidebar to see population counts
- **Adjust colors**: Click any gate in the precedence list to change draw order
- **Switch axes**: Right-click on any axis to select different parameters

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

### Toolbar Modes

| Mode | Icon | Function |
|------|------|----------|
| **Pan** | ✥ | Navigate and explore plots; scroll to zoom |
| **Polygon Gate** | ⬡ | Click to draw custom polygonal gates |
| **Rectangular Gate** | □ | Drag to create axis-aligned rectangular gates |
| **Edit** | ✎ | Click and drag gate vertices to modify shape |
| **Delete** | 🗑 | Click gates to delete them |
| **Spillover Adjust** | ⇔ | Interactive spectral compensation coefficient tuning |
| **Zoom** | ⛶ | Click and drag to zoom into regions |

**Keyboard Shortcuts** (visible in sidebar reference panel):
- `Z`: Zoom mode
- `P`: Pan mode  
- `G`: Polygon gate
- `R`: Rectangular gate
- `E`: Edit mode
- `D`: Delete mode
- `S`: Spillover adjustment
- `Esc`: Return to last mode
- `+` / `-`: Adjust density threshold

### Plot Configuration

**Axis Scaling Options**
1. Right-click any axis to open the scale menu
2. Select transformation type:
   - **LINEAR**: Standard arithmetic scale
   - **LOG**: Logarithmic scale (log₁₀)
   - **ASINH**: Inverse hyperbolic sine (arcsinh) for flow cytometry data

**Global Settings**
- Click the **Settings** (⚙) button to access:
  - **Density Threshold**: Adjust heatmap/dot rendering threshold
  - **Percentile Values**: Configure axis auto-ranging percentiles
  - Cofactor values for fluorescent parameters

**Per-Plot Configuration**
- Click **Axis Range** on any plot to:
  - Set manual axis ranges (min/max)
  - Adjust arcsinh cofactor for that plot
  - Apply settings to all plots or individual plots

### Gating Workflow

**Creating Gates**
1. Select a gating mode (Polygon or Rectangular)
2. On the target plot, click vertices (polygon) or drag a rectangle
3. Gates automatically evaluate on all populations in the gating hierarchy
4. Population counts update in real-time in the sidebar

**Gate Hierarchy**
- Child gates filter parent populations (standard flow cytometry logic)
- Reorder gates in the **Precedence List** sidebar to control draw order
- Color-coded display distinguishes populations visually

**Modifying Gates**
- **Edit Mode**: Click-and-drag vertices to reshape existing gates
- **Delete Mode**: Click a gate to remove it
- **Color Adjustment**: Click the gate in the Precedence List to move it forward/backward

**Population Analysis**
- Event counts displayed next to each population in the sidebar
- Percentages calculated relative to parent population
- Populations update dynamically as gates are added/modified

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
For multi-color experiments with compensation matrices:

1. FCS files with `$SPILLOVER` keywords load compensation automatically
2. Status bar indicates "Compensation Applied"
3. Use **Spillover Adjust** tool (⇔) to:
   - Fine-tune compensation coefficients interactively
   - Drag adjustment handles to modify spillover percentages
   - Live preview shows compensation effect immediately

**Manual compensation:**
- Drag compensation adjustment sliders in the toolbar
- Watch spillover correction update in real-time on the plot

#### Level-of-Detail (LOD) Rendering
For large datasets (>1M events):
- Initial subsampled render appears instantly
- Full-resolution render automatically upgrades when browser is idle
- Maintains smooth interaction during zoom/pan operations
- No user configuration needed—happens automatically

#### Background Rendering Queue
- Plots in non-active tabs are pre-rendered when browser is idle
- Clicking between tabs shows cached render immediately
- Automatic queue management based on browser activity

### Performance & Large Files

**Handling Large Datasets**
- **Level-of-detail rendering**: Subsampled preview with automatic high-resolution upgrade
- **GPU acceleration**: WebGL heatmap rendering handles 10M+ events
- **Web Worker processing**: Gate evaluation and parsing off main thread
- **Adaptive mode switching**: Automatically uses heatmap for large populations, dots for small

**Typical Performance**
- Files up to 10M events: Real-time interactive gating
- Files 10-100M events: LOD rendering with ~500ms full render
- Compensation adjustment: Interactive with live preview

---

## Technical Details

### Technology Stack
- **Pure JavaScript**: No external libraries or frameworks
- **HTML5 Canvas**: 2D plot rendering and dot scatter plots
- **WebGL**: GPU-accelerated density heatmaps
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
- **Inferno colormap**: Viridis/Inferno from Matplotlib color vision research

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
- WebGL support required for heatmap rendering (fallback to dots if unavailable)
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
- **Density threshold**: Lower the density threshold slider to show dots instead of heatmap
- **Axis scaling**: Verify axes are set appropriately for your data range
- **Missing parameters**: Check that selected parameters exist in the file

### Compensation Not Working
- **$SPILLOVER keyword**: Verify FCS file contains valid `$SPILLOVER` keyword
- **Parameter names**: Check that spillover matrix parameter names match FCS parameters
- **Manual application**: Use Spillover Adjust tool to manually correct if needed

### Slow Performance
- **Large files**: Use LOD rendering (enabled by default) to speed up interaction
- **Heatmap threshold**: Increase density threshold to reduce rendering load
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

**WebGL GPU acceleration** available on all modern browsers. If WebGL fails, dot scatter rendering is used automatically.

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
- Inferno colormap: Matplotlib Viridis team
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

**Q: What's the difference between heatmap and dot modes?**  
A: **Heatmaps** (GPU-rendered) are fast for large populations (>threshold events). **Dots** show individual events clearly for smaller populations (<threshold events). Switching is automatic based on population size.

**Q: How do I optimize axis transformation cofactors?**  
A: Right-click any plot axis, enable "Auto-optimize cofactors," and click Apply. FlowNG calculates optimal arcsinh cofactors using the OTflow algorithm.

**Q: Can I work with multiple files at once?**  
A: Yes. Load multiple FCS files—each opens in a separate tab at the top of the plot area.

---

## Changelog

### Version 1.0 (Current)
- Initial release with core gating and analysis features
- WebGL GPU-accelerated heatmap rendering
- Automatic cofactor optimization via OTflow algorithm
- Spectral compensation with interactive spillover adjustment
- Multi-tab support and background rendering queue
- Demo mode with sample PBMC data
- Support for FCS 2.0/3.0/3.1 and Beckman Coulter LMD files

---

**Happy analyzing! 🔬**

For the latest updates and to report issues, visit the [FlowNG GitHub repository](../../).
