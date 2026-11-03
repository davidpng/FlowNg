# Graph Report - .  (2026-11-03)

> Built from the code, not the HTML: `python3 scripts/extract_js_for_graphify.py <dir>` pulls the scripts out of `FlowNG.html` (`flowng_main.js`, `compute_worker.js`, `parse_worker.js`) so graphify parses real functions and calls. `source_file` names refer to those extracted files.

## Corpus Check
- Corpus is ~40,964 words - fits in a single context window. You may not need a graph.

## Summary
- 272 nodes · 893 edges · 16 communities
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Gate Editing and Actions
- Gate Evaluation and Density Plots
- Template Export and Session State
- Plot Controls and Axis Ticks
- Plot Creation and Template Import
- Kaluza Converter
- OTflow and Parse Worker
- Template Matching
- FCS Load Pipeline
- Shareable HTML Export
- File Metadata and Menus
- Shared File Save and Load
- Undo, Redo and History
- Density Colour Maths
- Compute Worker
- Plot Expand and Collapse

## God Nodes (most connected - your core abstractions)
1. `getFileById()` - 31 edges
2. `showToast()` - 30 edges
3. `renderPlot()` - 28 edges
4. `renderAllPlots()` - 27 edges
5. `renderPopList()` - 24 edges
6. `_applyTemplateV3()` - 24 edges
7. `pushUndo()` - 23 edges
8. `renderPlotCard()` - 22 edges
9. `getFileForPlot()` - 20 edges
10. `onCanvasMouseUp()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `renderPlot()` --indirect_call--> `_withEffColor()`  [INFERRED]
  flowng_main.js → flowng_main.js  _Bridges community 3 → community 2_
- `_restoreState()` --indirect_call--> `_clonePop()`  [INFERRED]
  flowng_main.js → flowng_main.js  _Bridges community 12 → community 4_
- `showPlotFileMenu()` --calls--> `getFileColor()`  [EXTRACTED]
  flowng_main.js → flowng_main.js  _Bridges community 3 → community 10_
- `addPlot()` --calls--> `getFileById()`  [EXTRACTED]
  flowng_main.js → flowng_main.js  _Bridges community 1 → community 4_
- `buildTreeNode()` --calls--> `getFileById()`  [EXTRACTED]
  flowng_main.js → flowng_main.js  _Bridges community 1 → community 0_

## Import Cycles
- None detected.

## Communities (16 total, 0 thin omitted)

### Community 0 - "Gate Editing and Actions"
Cohesion: 0.14
Nodes (41): autoCompensate(), beginCofactorDrag(), _boolLeaves(), buildTreeNode(), cancelUndo(), copyGate(), createQuadrant(), cycleDotBoost() (+33 more)

### Community 1 - "Gate Evaluation and Density Plots"
Cohesion: 0.10
Nodes (34): _boolMask(), buildLODSample(), buildSpatialIndex(), _bumpBoolDependents(), calculatePercentile(), copyMetadata(), defaultScale(), _doImportV3() (+26 more)

### Community 2 - "Template Export and Session State"
Cohesion: 0.07
Nodes (29): _asinhZeroFloor(), _authorSpill, _boolText(), colorPrecedence, doExportTemplate(), _drawTickLabel(), dropBox, _effColor() (+21 more)

### Community 3 - "Plot Controls and Axis Ticks"
Cohesion: 0.13
Nodes (30): _axisTicks(), _boolExprToNames(), buildAxisControls(), _buildTemplateV3(), canvasCoords(), _cfToFrac(), changeAxis(), changeBins() (+22 more)

### Community 4 - "Plot Creation and Template Import"
Cohesion: 0.19
Nodes (26): addFileToSession(), addPlot(), addTab(), applyAxisRangeModal(), applyGlobalAsinhCofactor(), applyGlobalMinPercentile(), applyGlobalSettings(), _applyTemplateV3() (+18 more)

### Community 5 - "Kaluza Converter"
Cohesion: 0.16
Nodes (18): argb_to_hex(), build_datasets(), collect_plots(), convert(), find_protocol(), Gate, infer_tube_labels(), legacy_to_raw() (+10 more)

### Community 6 - "OTflow and Parse Worker"
Cohesion: 0.20
Nodes (13): bartlett(), computeKDESetup(), findPeaks(), gaussianKDE(), jarqueBera(), makeLCG(), matInvert(), parseFCS() (+5 more)

### Community 7 - "Template Matching"
Cohesion: 0.29
Nodes (11): _filePanel(), _fileTubeName(), importGates(), _importGatesV3(), isFluorescentParameter(), _matchTemplateFiles(), _normTube(), _panelFit() (+3 more)

### Community 8 - "FCS Load Pipeline"
Cohesion: 0.35
Nodes (11): finalizeFCSLoad(), hideProgress(), isLMD(), loadFCS(), loadFCSFallback(), matInvert(), parseFCS(), parseLMD() (+3 more)

### Community 9 - "Shareable HTML Export"
Cohesion: 0.24
Nodes (10): capturePristineSource(), _docSource(), _docSourceLive(), doExportShareable(), _estimateShareBytes(), _gzipB64(), _measureShareRatios(), _packEvents() (+2 more)

### Community 10 - "File Metadata and Menus"
Cohesion: 0.25
Nodes (9): buildFileRootNode(), filterMeta(), renderMetaRows(), setActiveFile(), shortFilename(), showFileContextMenu(), showFilePicker(), showMetadata() (+1 more)

### Community 11 - "Shared File Save and Load"
Cohesion: 0.33
Nodes (6): _applySterileMode(), _gunzipB64(), loadBundleIfPresent(), saveDaughter(), _unpackEvents(), updateSaveButton()

### Community 12 - "Undo, Redo and History"
Cohesion: 0.47
Nodes (6): _clonePop(), logChange(), redo(), _snapshotState(), undo(), updateUndoButtons()

### Community 13 - "Density Colour Maths"
Cohesion: 0.33
Nodes (6): _ng2Anchor(), _ng2GrayAnchor(), _ng2Hsl(), _ng2Hue(), _ng2Rgb(), _ng2ToLin()

### Community 14 - "Compute Worker"
Cohesion: 0.70
Nodes (4): buildSpatialIndexW(), evalGateW(), spatialQueryW(), toDisplayW()

### Community 15 - "Plot Expand and Collapse"
Cohesion: 0.83
Nodes (4): collapseExistingExpanded(), collapsePlot(), expandPlot(), togglePlotExpand()

## Knowledge Gaps
- **17 isolated node(s):** `GATE_COLORS`, `FILE_DOT_COLORS`, `fcsFiles`, `plots`, `populations` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `getFileById()` connect `Gate Evaluation and Density Plots` to `Gate Editing and Actions`, `Template Export and Session State`, `Plot Controls and Axis Ticks`, `Plot Creation and Template Import`, `File Metadata and Menus`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `showToast()` connect `Plot Creation and Template Import` to `Gate Editing and Actions`, `Gate Evaluation and Density Plots`, `Template Export and Session State`, `Plot Controls and Axis Ticks`, `Template Matching`, `FCS Load Pipeline`, `Shareable HTML Export`, `Shared File Save and Load`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `renderPlot()` connect `Plot Controls and Axis Ticks` to `Gate Editing and Actions`, `Gate Evaluation and Density Plots`, `Template Export and Session State`, `Plot Creation and Template Import`, `Plot Expand and Collapse`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **What connects `GATE_COLORS`, `FILE_DOT_COLORS`, `fcsFiles` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Gate Editing and Actions` be split into smaller, more focused modules?**
  _Cohesion score 0.14268292682926828 - nodes in this community are weakly interconnected._
- **Should `Gate Evaluation and Density Plots` be split into smaller, more focused modules?**
  _Cohesion score 0.09982174688057041 - nodes in this community are weakly interconnected._
- **Should `Template Export and Session State` be split into smaller, more focused modules?**
  _Cohesion score 0.07056451612903226 - nodes in this community are weakly interconnected._