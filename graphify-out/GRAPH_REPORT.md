# Graph Report - .  (2026-08-01)

## Corpus Check
- Corpus is ~39,273 words - fits in a single context window. You may not need a graph.

## Summary
- 86 nodes · 58 edges · 37 communities (8 shown, 29 thin omitted)
- Extraction: 76% EXTRACTED · 21% INFERRED · 3% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.81)
- Token cost: 0 input · 87,352 output

## Community Hubs (Navigation)
- Gate Evaluation & Spatial Indexing
- OTflow Statistical Engine
- FCS Load & Worker Pipeline
- File Parsing & Compensation
- WebGL Rendering
- Adaptive LOD Rendering
- Background Render Queue
- Gate Hierarchy Management
- Display-Space Hit Testing
- Add File To Session
- Add Plot
- Axis Range Modal
- Global Asinh Cofactor
- Global Settings
- Export Template
- Import V3
- Full-Res Dot Rendering
- Export Gates
- Worker-Side KDE
- Demo Data Generation
- Spillover Indices
- Spillover Zone
- Import Gates
- Import Gates V2
- Import Gates V3
- Load Demo
- Canvas Click Handler
- Canvas Mouse Down
- Canvas Mouse Move
- Canvas Mouse Up
- Populations View Rebuild
- Remove File
- Gate Precedence List
- Worker Data Dispatch
- Show Axis Range Modal
- Global Settings Dialog
- ISAC Reference

## God Nodes (most connected - your core abstractions)
1. `evalGate` - 6 edges
2. `runOTflow` - 6 edges
3. `startOTflowPool` - 5 edges
4. `initComputeWorkerForFile` - 4 edges
5. `renderPlot` - 4 edges
6. `drawDotsWebGL` - 4 edges
7. `OTflow automatic cofactor optimization` - 4 edges
8. `parseFCS` - 3 edges
9. `evalGateAsync` - 3 edges
10. `gaussianKDE` - 3 edges

## Surprising Connections (you probably didn't know these)
- `Not intended for clinical diagnostic use` --conceptually_related_to--> `OTflow automatic cofactor optimization`  [AMBIGUOUS]
  README.md → FlowNG.html
- `Client-side-only, no-server privacy architecture` --conceptually_related_to--> `Per-file compute worker (gate eval off main thread)`  [INFERRED]
  README.md → FlowNG.html
- `Single-file application with zero external libraries` --conceptually_related_to--> `Shared parse-worker-src reused for FCS parsing and OTflow pool`  [INFERRED]
  README.md → FlowNG.html
- `FCS 2.0/3.0/3.1 file format` --references--> `parseFCS`  [EXTRACTED]
  README.md → FlowNG.html
- `Beckman Coulter LMD file format` --references--> `parseLMD`  [EXTRACTED]
  README.md → FlowNG.html

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **OTflow parallel worker pool cofactor optimization pipeline** — flowng_loadfcs, flowng_startotflowpool, flowng_runotflow, flowng_computekdesetup, flowng_gaussiankde, flowng_jarquebera, flowng_bartlett, flowng_finalizefcsload [EXTRACTED 0.90]
- **GPU heatmap rendering pipeline (WebGL)** — flowng_renderplot, flowng_getglrenderer, flowng_createglrenderer, flowng_buildheatmaptexture, flowng_gethmapgl, flowng_drawheatmapgl, flowng_drawdotswebgl [EXTRACTED 0.90]
- **Gate creation and evaluation flow (main thread + worker)** — flowng_finalizegate, flowng_evalgateasync, flowng_evalgate, flowng_evalgatelod, flowng_evalgatew, flowng_initcomputeworkerforfile, flowng_buildspatialindex [EXTRACTED 0.90]

## Communities (37 total, 29 thin omitted)

### Community 0 - "Gate Evaluation & Spatial Indexing"
Cohesion: 0.17
Nodes (13): buildSpatialIndex, buildSpatialIndexW, Per-file compute worker (gate eval off main thread), evalGate, evalGateAsync, evalGateLOD, evalGateW (worker-side gate eval), finalizeGate (+5 more)

### Community 1 - "OTflow Statistical Engine"
Cohesion: 0.22
Nodes (10): bartlett, computeKDESetup, gaussianKDE, jarqueBera, OTflow automatic cofactor optimization, runOTflow, runOTflowParallel, Scott, D. W. (2015), Multivariate Density Estimation (+2 more)

### Community 2 - "FCS Load & Worker Pipeline"
Cohesion: 0.33
Nodes (7): finalizeFCSLoad, LMD files bypass OTflow, use fixed cofactor 300, loadFCS, loadFCSFallback, Shared parse-worker-src reused for FCS parsing and OTflow pool, startOTflowPool, Single-file application with zero external libraries

### Community 3 - "File Parsing & Compensation"
Cohesion: 0.29
Nodes (7): matInvert, parseFCS, parseLMD, recomputeCompensation, Spectral compensation via $SPILLOVER matrix inversion, Beckman Coulter LMD file format, FCS 2.0/3.0/3.1 file format

### Community 4 - "WebGL Rendering"
Cohesion: 0.33
Nodes (6): createGLRenderer, drawDotsWebGL, drawHeatmapGL, getGLRenderer, getHmapGL, Inferno/Viridis colormap (Matplotlib)

### Community 5 - "Adaptive LOD Rendering"
Cohesion: 0.50
Nodes (5): Adaptive heatmap-vs-dot rendering based on population size, buildHeatmapTexture, buildLODSample, Level-of-detail (LOD) rendering with idle-time upgrade, renderPlot

### Community 6 - "Background Render Queue"
Cohesion: 0.50
Nodes (4): Background rendering queue for off-tab plots, queueBgRenderPlot, _runBgRenderChunk, scheduleBgRender

### Community 7 - "Gate Hierarchy Management"
Cohesion: 0.67
Nodes (4): deleteGateAndDescendants, Hierarchical gate parent-child population model, getDescendantGates, reparentGate

## Ambiguous Edges - Review These
- `pointInPolygonDisp` → `Ray-cast gate test done in display space, not raw space`  [AMBIGUOUS]
  FlowNG.html · relation: rationale_for
- `OTflow automatic cofactor optimization` → `Not intended for clinical diagnostic use`  [AMBIGUOUS]
  README.md · relation: conceptually_related_to

## Knowledge Gaps
- **50 isolated node(s):** `loadFCSFallback`, `sendDataToComputeWorkerForFile`, `evalGateLOD`, `finalizeGate`, `runOTflowParallel` (+45 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `pointInPolygonDisp` and `Ray-cast gate test done in display space, not raw space`?**
  _Edge tagged AMBIGUOUS (relation: rationale_for) - confidence is low._
- **What is the exact relationship between `OTflow automatic cofactor optimization` and `Not intended for clinical diagnostic use`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `evalGate` connect `Gate Evaluation & Spatial Indexing` to `Gate Hierarchy Management`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `OTflow automatic cofactor optimization` connect `OTflow Statistical Engine` to `FCS Load & Worker Pipeline`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `evalGate` (e.g. with `evalGateLOD` and `evalGateW (worker-side gate eval)`) actually correct?**
  _`evalGate` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `loadFCSFallback`, `sendDataToComputeWorkerForFile`, `evalGateLOD` to the rest of the system?**
  _50 weakly-connected nodes found - possible documentation gaps or missing edges._