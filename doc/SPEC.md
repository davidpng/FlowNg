# FlowNG interface specification

This file records the interface and interaction decisions for `FlowNG.html`, and why each was made. It is the place to check before changing behaviour. `README.md` describes the features for users; `TESTING.md` says how to verify them. Where a rule has a check, its row number in `TESTING.md` is given.

## 1. Principles

1. **One mode, everywhere.** A tool choice applies to the whole workspace, not to whichever plot happens to be selected.
2. **Selection is for acting on plots, not for gating.** Selecting plots is needed for cofactor markers, bulk axis changes and removal. It must never silently restrict what the drawing tools can do.
3. **Predictable bulk edits.** When 2+ plots are selected, every per-plot display setting changes on all of them together.
4. **Tree structure decides hierarchy.** Whether one gate is "inside" another is decided by the population tree (`parentId`), never by which events the gates happen to share.
5. **Keyboard is a shortcut for the toolbar, never a different behaviour.** A key does exactly what clicking its button does.
6. **Discoverable.** Every shortcut is visible on its button, in its tooltip and in the help panel.
7. **Skip, don't fail.** Generated content (the starter template) leaves out what cannot be built and reports it, instead of stopping or guessing.

## 2. Toolbar and modes

The left toolbar group holds the modes: **Select, Polygon, Rect, Quadrant, Edit, Comp, Delete, Autocomp**, then Undo, Redo, History and Add Plot. The mode is global (`globalMode`); exactly one button is active.

**Narrow windows:** the two toolbar groups (tools on the left, files and settings on the right) always stay side by side. When there is not enough width each group wraps its own buttons onto extra lines, and the header grows taller (`--header-h` follows it), rather than the right group dropping underneath the left one.

### 2.1 Changing mode (`setGlobalMode`)

- Choosing a mode **deselects all selected plots** and applies the mode to **every plot** in the workspace.
- Reason: previously the mode went only to the selected plots, so with one plot selected the other plots kept their old mode and gates could not be drawn on them until the selection was cleared. Users expect a mode to be a property of the tool, not of a plot.
- Consequence: cofactor markers need a selected plot. Choose **Select** first, then click the plot (top bar or empty space). The help text and tooltips say this in that order.
- Check: `TESTING.md` 4.15.

### 2.2 Keyboard shortcuts

All tool keys are plain letters on the left hand, so one hand can stay on the mouse.

| Key | Mode | Mnemonic |
|---|---|---|
| `S` | Select | **S**elect |
| `G` | Polygon | poly**g**on (`P` was avoided, see below) |
| `R` | Rect | **R**ect |
| `Q` | Quadrant | **Q**uadrant |
| `E` | Edit | **E**dit |
| `C` | Comp | **C**omp |
| `A` | Autocomp | **A**utocomp |
| `Delete` / `Backspace` | Delete mode | the delete key |

Rules:

- **Delete key has two jobs, decided by selection.** With plots selected it removes them (the long-standing behaviour). With none selected it switches to Delete mode. Reason: users expect the delete key to mean delete, and a mode that also deletes plots under a selection would be a surprise.
- **Ignored when:** a modifier is held (`Ctrl`, `Cmd`, `Alt`, `Shift`); focus is in an input, select or textarea; a dialog (`.modal-overlay`, `#meta-modal`, `*-overlay`) is open; the toolbar is hidden (no workspace open); the key is auto-repeating. Reason: typing in dialogs and names must never change the tool, and `Ctrl/Cmd+Z`, `Ctrl/Cmd+Y` must keep working.
- **Letters only on the left hand.** `P` for Polygon would have been the obvious mnemonic but is on the right hand; `G` is on the left and was chosen. The Quadrant key `Q` and Select key `S` were chosen by the author, replacing an earlier proposal that used `W`/`D`/`F`.
- **Existing keys unchanged:** `Esc` cancels a gate being drawn and deselects all; `Ctrl/Cmd+Z` undo; `Ctrl/Cmd+Shift+Z` or `Ctrl/Cmd+Y` redo.
- Checks: `TESTING.md` 4.16 to 4.18.

### 2.3 Showing the shortcut

- Each button label has its key in **bold, underlined, white** (`.tool-btn b`): **S**elect, Poly**g**on, **R**ect, **Q**uadrant, **E**dit, **C**omp, **A**utocomp, **Del**ete. Where the key is not the first letter (Polygon) the bold letter sits mid-word.
- Each tooltip ends with "Shortcut: X."; Delete says "Del / Backspace with no plot selected."
- The Quick Instructions panel lists the keys under the `Esc` line.
- Check: `TESTING.md` 4.19.

## 3. Plot selection and multi-select

- A plot is selected by clicking its top bar (the row with the population menu and bins slider) **or any part of it that has no other job**:
  - blank canvas, when the tool is **Select, Edit or Delete** and the click is not on a gate or quadrant crosshair (those start a move, a reshape or a delete). Drawing tools (Polygon, Rect, Quadrant, Autocomp) and Comp use the canvas, so a click there never selects;
  - the card's margins and the empty gaps beside the axis menus (`xaxis-ctrl`, `yaxis-ctrl`) and the status strip.
  Controls (menus, buttons, slider, grip, expand, swap, cofactor markers) never select. Modifier clicks work the same everywhere: `Shift` range, `Ctrl`/`Cmd` toggle. Because selection no longer needs the top bar, a gate drag is the only canvas action that does not select.
- Clicking outside every plot deselects all; `Esc` also deselects.
- `Shift`+click range-selects; `Ctrl`/`Cmd`+click toggles.
- **With 2+ plots selected, these apply to all selected plots:** axis parameter, population, bins, and **scale (LOG / LIN / ASINH)**.
- **Scale rule (changed from "always per plot"):** clicking the scale button on one selected plot computes that plot's next scale in the cycle (LOG to LIN to ASINH to LOG) and gives the **same resulting scale** to that axis of every selected plot, so the plots end up matching even if they started different. Reason: users comparing several plots want them on one scale and had to click each button. Only the clicked axis (X or Y) changes.
- With one or no plot selected, the scale button changes only the clicked plot.
- Scale changes clear any in-progress gate points on the changed plots.
- Check: `TESTING.md` section 6, multi-select scale bullet.

## 4. Population tree

- Drag a row onto another to **re-parent**; drop on the file row ("All Events") to un-parent. Drag the grip to reorder siblings; the gate lower in the tree wins shared cells, and a child always beats its ancestors.
- **Re-parent validity (`reparentGate`):**
  - Refused if the target is the dragged gate or one of its true descendants, found by walking the target's `parentId` chain up to the root. Message: "Cannot reparent a gate onto one of its own descendants".
  - **Siblings are valid targets, even when their events overlap.** Gate B lying inside Gate A on a plot, both under All Events, can be moved under A. The earlier check used event overlap (`getDescendantGates`), which wrongly treated any gate sharing events as a descendant and blocked these moves.
  - Also refused: boolean populations (they stay top level), moves between files, and moving under a population that depends on the gate (`_upstreamIds`).
- `getDescendantGates` stays event-overlap based on purpose, for back-gating and re-evaluation after a move. It must not be used to answer "is this an ancestor/descendant?".
- Checks: `TESTING.md` 4.13, 4.14.

## 4a. Editing gate vertices (Edit mode)

- Dragging a vertex of a gate whose edges are **all horizontal or vertical** (a gate drawn with Rect, or any rectilinear polygon) keeps it rectilinear: each neighbour of the dragged corner keeps the edge it shared with it (a vertical edge keeps its x, a horizontal edge keeps its y). A rectangle therefore stays a rectangle and dragging a corner resizes it.
- Edges are judged horizontal or vertical on screen (within half a pixel), which is the same as in raw data because every axis scale is monotonic.
- A gate with any slanted edge (a hand-drawn polygon) is edited freely, one vertex at a time, as before. Moving a whole gate (Select, or dragging the body in Edit) is unchanged.
- Reason: dragging one corner of a rectangle used to skew it into a quadrilateral with slanted sides.
- Check: `TESTING.md` 4.20.

## 5. Starter template

Generated per tube from the Pool (**Starter**). One tab per tube, four plots, no gates. Plots are **Y vs X**:

| # | Y | X |
|---|---|---|
| 1 | CD45 | Time |
| 2 | FSC-H | FSC-A |
| 3 | FSC-A | SSC |
| 4 | CD45 | SSC |

- Layout decision: the author chose this arrangement (Time and SSC on X, CD45 and FSC-A on Y where used) over the earlier Time on Y / SSC on Y layout.
- **Channel matching is by role, by regex, on both name and long name**, so Beckman (`FS INT LOG`, `SS INT LOG`, marker in the stain label) and BD (`FSC-A`, `SSC-A`) files both work: FSC/FS with A, INT or AREA (area) and H, PEAK or HEIGHT (height); SSC/SS with A, INT or AREA; optional `LOG`/`LIN` suffix; `TIME`; `CD45` as a whole token.
- **A plot whose channel is missing is skipped.** The toast and console list each skipped plot and the missing channel. A tube with no usable plots gets no tab.
- Check: `TESTING.md` 13.5.

## 6. Feedback and messaging

- Refusals and results use a toast with a plain-language reason ("Cannot reparent ...", "Moved ..."). Silent failure is not acceptable for an action the user initiated.
- Every change that alters analysis state is undoable and logged in History (no user names).
- Status bar text under the plots states the current mode's gesture (for example "Click to add gate points").

## 7. Change log of decisions

| Change | Decision | Reason |
|---|---|---|
| Mode applies to all plots and clears selection | Adopted | Selected plot blocked drawing on other plots |
| Tool shortcuts `S G R Q E C A`, `Del` | Adopted, left hand, key shown on button | One-handed gating; discoverable |
| Delete key doubles as Delete mode only with no selection | Adopted | Keeps plot removal; matches expectation |
| Scale button affects all selected plots | Adopted (reversing "per plot") | Bulk comparison |
| Reparent check by tree, not event overlap | Adopted | Siblings sharing events were wrongly refused |
| Starter plot orientation | CD45 vs Time, FSC-H vs FSC-A, FSC-A vs SSC, CD45 vs SSC | Author's preferred layout |

## 8. Open points

- Shortcuts for Undo/Redo/History/Add Plot, and for toggling the scale, are not defined.

## 9. Anatomy of a plot: card, header, canvas

A plot is a **card** (`.plot-card`, `plot-card-<id>`, 352 px wide) with three parts. The parts have different jobs, and the split is deliberate: the canvas is for gating, the header is for managing the plot.

| Part | Contains | Click does |
|---|---|---|
| **Header** (`.plot-header`, the top bar) | Drag grip `⠿`, file colour dot (only with 2+ files), population menu, bins slider (32-1024) and value, event count | Selects the plot (see section 10) |
| **Canvas** (`<canvas id="canvas-<id>">`, 350 x 350) | The density plot, gates, quadrant crosshair, in-progress gate points | Acts according to the global mode (draw, move, edit, delete, ...) |
| **Overlay controls** (on the canvas wrap) | X axis menu and scale button (bottom), Y axis menu and scale button (left, rotated), `⇄` swap axes (bottom-left), `⤢` expand (corner) | Their own action; never selects the plot and never draws |

Definitions used throughout this spec:

- **Canvas** means only the drawing surface of one plot. It never means the whole work area. The work area that holds all cards is the **canvas area** (`#canvas-area`).
- A plot is selected from the header or from any empty part of the card (section 10); a click that draws, moves or edits a gate never changes the selection.
- **Right-click** targets differ by part: right-click the canvas opens Axis Range (min/max and the arcsinh cofactor, typed); right-click the header switches the plot's source file (only when 2+ files are loaded).
- A drag or click on a control inside the header (menu, slider, button, the grip) does not count as a selection click.

## 10. Selection model

- **Where:** click a plot's header. Not the canvas, not the overlay controls.
- **Single click** selects only that plot and deselects the rest. `Ctrl`/`Cmd`+click toggles one plot in or out. `Shift`+click selects the range between the last clicked plot and this one, in plot order.
- **Visual:** a selected card gets an accent border, a glow and a tinted header.
- **Deselect:** click empty canvas area, or press `Esc`. Choosing a tool also deselects (section 2.1).
- **What selection is for:** cofactor markers (drag the blue marker on an arcsinh axis), multi-plot axis/population/bin/scale changes, and removing plots with `Del`.
- **Focused file:** selecting a plot makes its file the focused file, which sets the draw/ownership order shown for that file.
- **Not for gating:** no drawing tool depends on a selection.
- **Removing plots (`Del`/`Backspace`) is undoable and logged.** One key press is one step: History shows "Removed plot X vs Y" (or "Removed N plots"), and Undo puts the same plots back at their old positions and tabs; Redo removes them again. Plots are not part of the gate snapshot, so ordinary Undo of a gate change never adds or removes plots; plot removal carries its own restore step (`plotOps` on the undo entry). Tab changes use the same mechanism (section 13).

## 11. Plot order, reordering and moving between tabs

- **Order** is the order of the `plots` list, which is also the order cards appear on screen. Range select uses this order.
- **Reorder:** drag a plot by its `⠿` grip (only the grip is draggable, so the density plot, sliders and menus never start a drag). Drop it on another card: the dragged plot takes that card's position and the others shift. The target card is highlighted while dragging, and the dragged card is dimmed.
- **Move to another tab:** drag the grip and drop on a tab button. The tab strip shows `Name (count)` and counts update.
- Reordering a plot changes layout only; it does not change gates and is not a history entry.
- The tree is separate: dragging tree rows or their grips changes gate hierarchy and sibling precedence (section 4), never plot order.

## 12. Expanding and swapping a plot

- **Expand** (`⤢`): shows one plot large in an overlay and hides the others; click the button again, or click outside the plot, to collapse. Only one plot is expanded at a time; expanding another collapses the first. Collapsing clears any zoom on that plot and redraws every plot at its normal size.
- **Swap axes** (`⇄`): exchanges X and Y parameters, their scales and any zoom. It acts on the clicked plot.
- Both are card-local buttons and neither selects the plot.

## 13. Tabs

- **Plot size per tab:** a **Plot size** slider at the right end of the tab strip sets the width and height of every plot on the active tab (280 to 800 px in steps of 10, default 350; the card is 2 px wider than the canvas). Dragging resizes the plots live. Each tab keeps its own size, the slider shows the active tab's, and a plot moved to another tab takes that tab's size. The expanded view is unaffected and returns to the tab's size when collapsed. New plots use the tab's size.
  - Reason: users wanted bigger (or more) plots per page without expanding each one; a tab is the natural unit because tabs group plots that are read together.
  - Saved in the template as `tabs: [{name, size}]` (only tabs not at the default), which also carries it into shared files and Save, since all of them are built from the template. Older templates have no `tabs` field and open at the default size. The minimum of 280 keeps the axis menus inside the plot.
  - It is a display setting like the bins slider: not an undo step and not in History. Pair large sizes with a higher bins value.

- A tab groups plots. The strip shows `Name (count)`; right-click or double-click renames; `✕` closes; `+ Tab` adds one.
- **Adding (`+ Tab`), renaming and closing a tab are undoable and logged** ("Added tab ...", "Renamed tab ... to ...", "Closed tab ... (its N plots moved to ...)"). Closing a tab never deletes plots: they move to the first remaining tab, and Undo reopens the tab at its old position and sends exactly those plots back; Redo repeats it. The last tab cannot be closed. Tabs made by the program (starter template, template import) are not individual undo steps.
- A workspace (one loaded template and its files) has its own tabs, plots, undo and history; the workspace strip sits above the tab strip.

## 14. FCS export and SpikeNG (full version only)

These tools write event data, so they exist only in the full app. They sit inside the `@lite` markers and are physically removed from locked shared files (see 8.4 in TESTING.md).

- **Export events as FCS:** right-click a population (or a file in the file list, for all events) and choose *Export events as FCS…*. It writes a minimal FCS 3.1 file: float32 list-mode data, parameter names (`$PnN`), labels (`$PnS`), ranges and `$TIMESTEP`. Everything else is dropped: patient and sample IDs, dates, instrument and cytometer settings, `$SPILLOVER`. The file is named after the population, never the source file, because source file names often hold patient identifiers.
  - **Compensation is not baked in.** When the file has a spillover matrix, the export writes the *uncompensated* values plus the file's current `$SPILLOVER` (including manual edits), so the file opens compensated exactly as in the app and SpikeNG can still reach the raw values. A file with no matrix exports its values as is. The matrix is instrument calibration, not an identifier.
  - Parameter names and labels are kept because SpikeNG needs them to match files.
- **SpikeNG** (toolbar button, always available): merges a donor file into a recipient file. The donor is the *schlemiel* (the population being spiked in, usually an exported population) and the recipient is the *schlimazel* (the sample receiving the spike). Both may be FCS or LMD.
  - **Column check first.** `$PnN` names must match (case and spacing ignored). If the same set is present in a different order the donor columns are reordered to match and the dialog says so. If `$PnS` labels are both given and differ, or any name is missing or duplicated, the merge is refused and the differences are listed.
  - **Spike amount** is a percentage of the *schlimazel* event count, with a linked box showing the equivalent number of events (editing either updates the other). The summary shows the result's total and the spike's share of it. If the schlemiel has fewer events than requested, all of them are used and a warning is shown. Events are never duplicated, since duplicates would be detectable.
  - Spike events are a random subset of the schlemiel chosen with a seed (same seed, same events), kept in their original order.
  - **Educational mode (time based):** the schlimazel events come first, then the spike events, with the Time channel of the spike shifted so there is a gap equal to 3% of the longer acquisition (the larger Time span of the two files). With no Time parameter the spike is simply appended and a warning is given.
  - **Proficiency mode (interleaved):** each spike event is inserted at a random position among the schlimazel events. A spike event takes the Time value of the schlimazel event just before it, so the Time channel stays continuous and gives nothing away.
  - Output `$PnR` is the larger of the two files' ranges. An optional **answer key** (CSV of 1-based output rows that are spiked) can be ticked in the dialog; it is off by default, and when ticked it downloads one second after the FCS file (a browser keeps only one of two simultaneous downloads, which is how the key once replaced the FCS file).
  - **Compensation:** files are merged in uncompensated (raw) space and the output carries the *schlimazel's* `$SPILLOVER`, so every event, spiked or not, is compensated by the same matrix when opened (as if the donor cells had been acquired on the recipient's run). The dialog states the case: same matrix; different matrices (the schlimazel's wins); only the schlimazel has one; neither has one; or only the schlemiel has one, in which case the result is uncompensated and the schlemiel's matrix is dropped (warned). Reason: merging a compensated donor into a raw recipient would put the spike in the wrong place on every fluorescence plot.

## 15. Provenance of this spec

Sections 1 to 8 record decisions made while changing the app. Sections 9 to 14 describe the current behaviour as implemented in `FlowNG.html` (rendering in `renderPlotCard`, selection in the header click handler, reordering in the grip and card drag handlers, `togglePlotExpand`, `renderTabStrip`) and in `README.md`. The author's earlier design discussions are not visible to this document's writer, so reasons are given only where the code or README states them; anything missing should be added when remembered.
