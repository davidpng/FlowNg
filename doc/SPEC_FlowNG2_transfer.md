# Spec for FlowNG2: 1D histogram, 1D range gate, axis range dialog, event colouring

This document describes four features built and tested in `FlowNG.html` so they can be rebuilt in FlowNG2. It states behaviour and the reasons for it. Names in `code font` refer to FlowNG so the reference implementation can be read; FlowNG2 need not use them. The automated checks are in `scripts/suite/suite19.html` (`doc/TESTING.md` section 19, 28 rows, run with `python3 scripts/run_suite.py --only 19`). Everything here passed those checks. Not tested: real (non-synthetic) mouse input, other browsers, expanded view beyond a manual look.

Terms. A **population** is All events or a gate. A **plot** shows one population (its *input population*) on an X and a Y axis. A population's **parent** is its parent in the gate tree (`parentId`); hierarchy is always decided by the tree, never by shared events. **Depth** is the number of parents between a population and the root (All events). **Colour precedence** is the user-ordered list of populations (`colorPrecedence`, index 0 is highest).

## 1. Event colouring (the inheritance rules)

This is the foundation for the histogram lines and the density plots, so it comes first.

### 1.1 Rules

For every event on a plot:

1. **Owner.** Among the gates (descendants of the plot's population, plus back-gated gates, see 1.3) that contain the event, the **farthest descendant** owns it: greatest depth wins; at equal depth the higher colour precedence wins. Ownership never depends on whether a gate has a colour. This lets back-gated children show.
2. **Own colour.** If the owner has a colour, the event takes it.
3. **Nearest coloured ancestor.** Otherwise the event takes the colour of the owner's nearest coloured ancestor. The walk stops at All events (All events has no colour).
4. **Highest-ranked coloured sibling.** Otherwise the event takes the colour of the owner's sibling (a population with the same parent) that has a colour and the highest colour precedence.
5. **Grey.** Otherwise the event is grey.

Events contained by no gate take the plot population's own colour by the same rules 2 to 5 (the population's own colour, nearest coloured ancestor, highest-ranked coloured sibling), else the neutral base grey.

A "No colour" gate is one with `noColor` set or no colour value; it is treated as having no colour of its own.

### 1.2 Why

An earlier version let any uncoloured gate deep in another branch paint grey over a coloured child, so events in K+ (a blue child of CD20+) showed grey. The two things that fix it are: rule 1 chooses the owner without regard to colour (deterministic, supports back-gating), and rules 3 and 4 give every uncoloured owner a meaningful colour instead of grey. The user's phrase for it was "absolute primogeniture": the highest-ranked, closest relation supplies the colour.

### 1.3 Which gates take part

FlowNG uses `getColorGates(popId)`: gates that are descendants by the tree, plus gates with overlapping events (back-gating) in the same file, plus boolean populations when the plot shows All events. The population itself is excluded from owners (it supplies the base colour) and ancestors of the plot population are excluded. At most 31 owner classes are used (the last 31 in paint order).

### 1.4 Reference implementation

`_siblingColor(g)`, `_primoColor(g)` (= nearest coloured ancestor, else sibling), `_withEffColor(g)` (copies the ancestor colour onto an uncoloured gate), `_ng2ClassItems(orderedGates, renderPop)` (owners in paint order with a resolved colour each; the last item containing an event owns it). The density plot paints with it; the "+" dot overlay and histogram lines use the same colour resolution.

### 1.5 Checks

19.23 to 19.26: sibling by precedence (and reordering precedence changes the result), ancestor beats sibling, nothing to inherit gives no colour, farthest descendant owns the event in its inherited colour and a deeper gate with nothing to inherit is still the owner (grey).

## 2. 1D histogram

### 2.1 Choosing it

The Y-axis dropdown lists **Count** and **Percent** as its first two entries, above the parameters. Choosing one turns the plot into a histogram of the **X parameter**. Choosing a parameter again turns it back into a 2D plot. The plot keeps its Y parameter while it is a histogram (the dropdown just shows Count or Percent), so going back restores it. With 2+ plots selected the change applies to all of them (the existing bulk-edit rule).

### 2.2 Drawing

- The axis stays linear: the Y scale button shows `LIN` and is disabled. Y range is 0 to 1.05 times the tallest line (nothing to configure).
- X axis, grid, ticks, scale (LIN/LOG/ASINH), zoom range and cofactor work exactly as on a 2D plot.
- One **line** is drawn for the plot's population (width 2) plus one per gate below it (width 1.5). Each line is a polyline through the bin centres. Lines are in each gate's resolved colour (section 1), the population's line in its base colour (neutral dark grey if none). The population's line is drawn first, so gate lines sit on top.
- **Which gates:** only true descendants of the plot's population by the gate tree (children, grandchildren, ...), and, on a plot of All events, boolean populations. Back-gated gates that merely overlap the population are **not** drawn. This differs from 2D, where back-gating is shown for colour. Reason: the user wanted the histogram to show the selected gate and its children only.
- Events outside the X axis range are not counted (they are off the plot).

### 2.3 Y values

- **Count**: events per bin.
- **Percent**: each line is 100 x (events in the bin) / (events in that line's own population). Every line therefore totals at most 100 (exactly 100 when all its events lie within the X range). This compares shapes of populations of different sizes. A different definition (share of the plot's population) was considered and not chosen.

### 2.4 Resolution slider

The existing bins slider (32 to 1024, step 32, default 256, saved with the plot) sets the **number of bins across the X range**. It already existed for 2D plots (bins per axis) and its range and behaviour are unchanged. The bin width is the displayed X range divided by the bin count, in display (scale-transformed) space.

### 2.5 What a histogram plot does not do

Polygon, Rect, Quadrant, Edit, Autocomp and Comp tools do nothing on a histogram (the click handlers return at once). Swap axes shows a message ("Switch the Y axis to a parameter to swap axes") and does nothing. The 1D range gate (section 3) is the gate type for histograms. Select and Delete modes work on range gates.

### 2.6 Saved state

`hist: 'count' | 'percent'` is saved in the template plot entry next to `bins` and restored; absent means 2D. A plot title/pair label reads "X histogram" for a histogram.

### 2.7 Checks

19.10 to 19.17 (Count and Percent listed first, linear and disabled scale button; one line per population and descendant in gate colours; count total equals events for a wholly-inside gate; bins 32/256/1024; percent totals 100; a gate histogram draws the gate and its true children but not an overlapping sibling; polygon does nothing; range tool works).

## 3. 1D range gate

### 3.1 What it is

A gate on one axis: **all events whose X value is between x1 and x2** (inclusive of the bounds, ties aside), regardless of Y. It works on 2D plots and on histograms, and works for any X scale because the comparison is monotonic.

Appearance: two vertical **bars** (solid, the gate's colour, 2 px, full plot height) at x1 and x2, and between them a **thicker translucent band** (the gate's colour at about 38% opacity, 22 px tall, centred on a chosen height). The **gate name** is drawn centred inside the band, clipped to it, dark text. The band's height is free: it can sit higher or lower to keep names from colliding. An uncoloured gate uses its inherited colour (section 1).

### 3.2 Creating it

A toolbar mode **1D range** (button label `D 1D range`, shortcut `D`; the toolbar, tooltip and help panel all list it). Press at one X, drag horizontally, release: x1 and x2 are the two X positions (ordered), and the band height is where the drag **started** vertically. A drag shorter than 3 px creates nothing. A live preview (amber bars and band) is drawn while dragging. On release the gate is made under the plot's population with the usual colour assignment and name prompt (default `Gate <id>`), as for other gates, one undo step ("Drew 1D range on X").

### 3.3 Editing it

In **Select** (and Edit) mode:

- Drag the **left or right bar** (hit zone 5 px either side of the bar, anywhere along its height): moves only that end. The ends may cross; they are re-ordered.
- Drag the **band** (inside the bars, within half the band height of its centre): moves both ends together and the band up or down. The shift is applied in display space, so on a log or arcsinh axis the raw width changes while the on-screen width stays the same.
- Hit order: bars across all range gates first, then bands (first gate in list order).
- Cursors: `ew-resize` over a bar, `move` over a band, `col-resize` in the 1D range mode.
- During a drag only the picture updates. On release the gate and its descendants are re-evaluated (in the worker) and the plots refresh. A click without movement cancels its undo step. Moving a parent keeps children inside it because children are re-evaluated from the parent.
- **Delete** mode: clicking a bar or band deletes the gate and its children (with the usual confirmation).
- Undo/redo restore x1, x2 and band height.

### 3.4 Where it shows

On every plot whose **input population is the gate's parent** and whose **X parameter equals the gate's X parameter**, whatever the Y axis (2D plot with any Y, or a histogram). The band height is a fraction of plot height, shared by all of those plots: moving it on one moves it on all. Range gates never show on a plot whose X is a different parameter, and are not drawn as polygons.

### 3.5 Data model

```
gateInfo: {
  xParam, yParam,            // yParam is only the Y of the plot it was drawn on
  xScale, yScale: 'lin',     // X scale as drawn; Y always 'lin'
  rawPts: 4-point rectangle  // (x1,-1e12) (x2,-1e12) (x2,1e12) (x1,1e12), raw units
  range: { x1, x2, yf }      // x1 <= x2 raw values; yf = band height, 0 bottom to 1 top
}
```

In FlowNG the rectangle exists so evaluation, worker messages, undo snapshots, templates and import/export work unchanged (quadrants use the same trick). FlowNG2 may instead evaluate `x1 <= x <= x2` directly and drop `rawPts`; it must keep `x1`, `x2` and `yf` in saved files. `range` is saved and loaded with the gate in templates, copied by copy/paste, and cloned by the undo snapshots. Swap-axes leaves range gates alone.

### 3.6 Checks

19.1 to 19.9 and 19.27: event count equals the independent count of events with X in the range (parent, child and overlapping sibling); stored shape; shown on a second 2D plot; hit zones; bar drag moves one end and re-evaluates; band drag moves both and raises the band; child stays inside a moved parent; undo; the tool creates a gate with its band at the drag height; works on a histogram and lands under the plotted population; template round trip.

## 4. Axis Range & Scaling dialog (right-click a plot)

### 4.1 Histogram plots

Only the X axis section is shown. In place of the Y section there is a one-line note: "Y: Count (linear, automatic range)" or "Y: Percent (...)". Apply and **Reset to Defaults** act on the X parameter only; a histogram's hidden Y parameter keeps whatever range it had (test 19.22). The Reset button's hover text says "this X axis" on a histogram and "both axes" on a 2D plot.

### 4.2 Actual min and max, and two fill buttons

Under each axis's Min and Max inputs:

- A text line: `Data: min <data minimum> · max <data maximum> · full scale <$PnR>`, from the file's column minimum and maximum and the parameter range keyword.
- **Set to data min/max** fills Min and Max with the data minimum and maximum (tightest fit).
- **Set to full scale** fills Min with 0 (1 on a log axis; the data minimum when that is below 0) and Max with the parameter's full scale (`$PnR`).

Both buttons only fill the boxes (marking them as modified); nothing changes until **Apply**. They also clear that axis's percentile override so the filled Min is used. The existing **Reset to Defaults** (whole dialog) and per-axis **Reset** (percentile only) remain.

### 4.3 Hover explanations

Every control has a hover tooltip saying what it does: both labels and inputs (Min, Max, ASINH cofactor, Min percentile), Calculate, per-axis Reset, Set to data min/max, Set to full scale, the data line, Apply, Reset to Defaults, Cancel. Test 19.19 fails if any button, input or label in the dialog has none.

### 4.4 Checks

19.18 to 19.22.

## 5. Build order for FlowNG2

1. Event colour resolution (section 1) with its pure-function tests; this has no UI.
2. Range gate data model, evaluation, template save/load, undo (3.5).
3. Range gate drawing, hit test, create and drag (3.1 to 3.4).
4. Histogram plot type (section 2), reusing 1 and 3.
5. Axis dialog changes (section 4).
6. The tests of `suite19.html`, adapted to FlowNG2's test harness. The test file uses synthetic mouse events on the plot canvas, independent counts computed from the raw data for gate membership, and fake populations to test colour rules without data.

## 6. Decisions worth keeping and open points

- Decided by the user: Count and Percent first in the Y list; lines coloured by gate; slider still sets the bin count; range gate is two bars plus a translucent band with the name inside; it must work on both 2D and 1D plots; histogram shows only children of the selected gate; the five colour rules in the order of section 1.1; the dialog shows actual min and max and has separate "data min/max" and "full scale" buttons plus the existing reset, all with hover text.
- My choices the user did not specify and may want to change: Percent is relative to each line's own population; the band is 22 px and 38% opaque; the shortcut is `D`; the "full scale" minimum rule; bar hit zone 5 px; the range gate shows on plots sharing the parent and X parameter (not other Y axes' parents).
- Known limit: Y zoom and polygon-type gate tools are ignored on histograms; the 1D range tool is the only gate tool there.
