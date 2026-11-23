# ManifoldNG benchmark: event limits per method

ManifoldNG runs dimensionality reduction (UMAP, t-SNE, PaCMAP, PHATE, densMAP,
diffusion maps) and clustering (Phenograph, FlowSOM) inside FlowNG as one
single-threaded WebAssembly module. A wasm32 module can address at most 4 GB, and
FlowNG opened from `file://` cannot use threads (no cross-origin isolation), so
each method gets its own default event count, measured here rather than
guessed: the number of events it handles in 60 seconds (more on request, up to
what fits in memory).

## Setup

- Module: `manifoldng/` built with `cargo build --release --target wasm32-unknown-unknown`
  (Rust 1.90, no SIMD), the same bytes for every run.
- Runner: Node 24 (V8, the engine Chrome uses), one fresh process per point so
  WebAssembly linear memory starts empty; 4 runs at a time on a 14-core Apple M4
  Pro with 24 GB. Each run is single-threaded. Spot checks in headless Chrome are
  below.
- Data: 2,000,000 events drawn at random from
  a 10M-event multiple myeloma MRD FCS file (BD), its 20 fluorescence channels
  (no FSC, SSC or Time), arcsinh(x / 300) as FlowNG displays them. A run on n
  events takes the first n rows (a random sample).
- Default parameters: UMAP k 15, min_dist 0.1; t-SNE perplexity 30; PaCMAP
  n_near 10; PHATE k 5 and diffusion maps k 15, both with 2,000 landmarks;
  Phenograph k 30, Louvain, resolution 1; FlowSOM 10 x 10 grid, rlen 10,
  10 metaclusters.
- Ladder: 10k, 25k, 50k, 100k, 200k, 500k, 1M, 2M events, stopping a method
  after a run longer than 10 minutes or an error.
- "Peak memory" is the size of WebAssembly linear memory after the run. Linear
  memory never shrinks, so this is the high-water mark. It does not include
  FlowNG's own copy of the events in JavaScript.

Scripts: `manifoldng/bench/run_one.mjs` (one point), `ladder.mjs` (the ladder),
`fit.mjs` (fits and limits), `bench.html` + `chrome_bench.py` (Chrome check),
`fcs_to_f32.py` (data extraction). Raw results: `manifoldng/bench/results.jsonl`,
`results_d.jsonl`, `chrome.jsonl`; derived limits: `manifoldng/bench/limits.json`.

## Results (20 channels)

Time in seconds / peak memory in MB.

| Method | 10k | 25k | 50k | 100k | 200k | 500k | 1M | 2M |
|---|---|---|---|---|---|---|---|---|
| UMAP | 2.6 / 21 | 6.6 / 49 | 13.5 / 56 | 28 / 124 | 63 / 250 | 181 / 455 | 432 / 871 | 1062 / 1733 |
| densMAP | 3.0 / 21 | 7.6 / 49 | 15.8 / 56 | 34 / 124 | 80 / 250 | 212 / 455 | 551 / 871 | 1236 / 1733 |
| t-SNE (Barnes-Hut) | 16 / 40 | 47 / 96 | 100 / 188 | 221 / 377 | 502 / 754 | > 20 min | | |
| t-SNE (FFT) | 16 / 65 | 22 / 112 | 31 / 188 | 50 / 377 | 93 / 754 | 264 / 1893 | 627 / 3799 | |
| PaCMAP | 0.7 / 23 | 2.0 / 54 | 4.3 / 105 | 10 / 208 | 27 / 415 | 97 / 1034 | 288 / 2066 | out of memory |
| PHATE | 14 / 147 | 19 / 287 | 25 / 571 | 43 / 1139 | 79 / 2279 | out of memory | | |
| Diffusion maps | 5.0 / 145 | 9.6 / 279 | 18.5 / 557 | 37 / 1126 | 74 / 2253 | out of memory | | |
| Phenograph | 0.8 / 52 | 2.1 / 121 | 4.1 / 263 | 9.3 / 338 | 24 / 487 | 88 / 701 | 168 / 1444 | 301 / 2705 |
| FlowSOM | 0.4 / 2 | 0.9 / 4 | 1.8 / 6 | 3.6 / 10 | 7.2 / 19 | 18 / 44 | 36 / 86 | 73 / 170 |

**No method needs memory that grows with n².** Every method's memory grows
linearly with the event count. The slope sets the ceiling:

- **PHATE and diffusion maps** keep an events x 2,000-landmark matrix: about
  11 MB per 1,000 events, so they run out of the 4 GB address space between
  200k and 500k events (fit: about 300k).
- **t-SNE** keeps 3 x perplexity = 90 neighbours per event: about 3.8 MB per
  1,000 events, so about 920k events. Barnes-Hut is limited by time well before
  that.
- **PaCMAP**: about 2.1 MB per 1,000 events; about 1.6M events.
- **UMAP, densMAP, Phenograph**: about 0.85–1.3 MB per 1,000 events; the limit
  is time, not memory.
- **FlowSOM**: 0.08 MB per 1,000 events and linear time; it can take every
  event of a large file.

### Channels

At 50k synthetic events with 10, 20 and 40 channels, run time changes little:
time grows as channels^b with b between -0.1 and 0.16 for the embeddings, 0.27
for Phenograph and 1.0 for FlowSOM (the only method whose cost is mostly
distance computations in the input space). Memory changes by under 25%. The
limits below therefore depend on event count only; FlowNG's time prediction
applies the channel exponent.

| Method | b (channels) |
|---|---:|
| UMAP | 0.09 |
| densMAP | 0.09 |
| t-SNE BH | 0.05 |
| t-SNE FFT | -0.09 |
| PaCMAP | 0.16 |
| PHATE | 0.02 |
| Diffusion maps | 0.07 |
| Phenograph | 0.27 |
| FlowSOM | 0.99 |

## Default event counts (60 seconds) and the memory limit

Fits: time = a x n^b x (channels / 20)^beta (log-log least squares, points
from 25k up; beta from the channel test above); memory = c + m x n (least
squares).

**Rule: each method's default is the largest event count predicted to finish
in 60 seconds.** The user may ask for more: FlowNG then warns with the
predicted time and memory. The hard limit is memory only, the largest count
predicted to fit in 3.5 GB (the 4 GB wasm32 ceiling less headroom; column
"Memory limit" below, from the memory fit). At 60 s, time sets every
default; memory never does.

FlowNG rescales the 60 s to the user's computer. The first time the dialog
opens, the module runs a fixed workload (`mng_calibrate`: FlowSOM, 10x10
grid, 25 passes over 10,000 synthetic events with 20 channels; median of 3
after a warm-up). That took 0.183 s on the benchmark machine in Chrome 157.
Speed factor = measured time / 0.183 s. Predicted time = a x n^b x
(channels / 20)^beta x speed factor, so a computer twice as slow gets a default
about half as large (exactly 2^(-1/b)), and fewer channels give a larger default
where beta > 0.

| Method | Default on the benchmark machine (20 channels) | Predicted at default | Memory at default | Memory limit (hard) | Predicted time at the memory limit |
|---|---:|---:|---:|---:|---:|
| UMAP | 180,000 | 59 s | 185 MB | 4,000,000 | ~36 min |
| densMAP | 150,000 | 57 s | 160 MB | 4,000,000 | ~44 min |
| t-SNE (Barnes-Hut) | 31,000 | 59 s | 118 MB | 920,000 | ~47 min |
| t-SNE (FFT) | 98,000 | 60 s | 379 MB | 920,000 | ~8 min |
| PaCMAP | 340,000 | 59 s | 704 MB | 1,600,000 | ~8 min |
| PHATE | 140,000 | 57 s | 1,596 MB | 300,000 | ~1.6 min |
| Diffusion maps | 160,000 | 59 s | 1,800 MB | 310,000 | ~1.9 min |
| Phenograph | 440,000 | 60 s | 705 MB | 2,600,000 | ~8 min |
| FlowSOM | 1,600,000 | 58 s | 136 MB | 10,000,000 | ~6 min |

FlowNG's memory limit also counts the input matrix (events x channels x
4 bytes), so it is a little lower than this column with many channels.

The fitted constants are in `manifoldng/bench/limits.json` and copied into
`MNG_METHODS` in FlowNG.html; rerun `node fit.mjs` after a new benchmark and
update both.

### Progress

The status bar shows the running method, its stage, elapsed time and time
left, with Cancel. UMAP, densMAP, t-SNE, PaCMAP and PHATE report every
optimiser epoch from inside the module (a hook added to manifolds-rs's epoch
loops, see `manifoldng/vendor/PATCHES.md`); Phenograph reports its stages
and Louvain levels; FlowSOM reports SOM training steps. Before the first
epoch (neighbour search, graph, initialisation) the bar follows elapsed time
against the prediction, inside that stage's measured share of the run:

| Method | Share of run before the first epoch (20k events) |
|---|---:|
| UMAP | 10% |
| densMAP | 7% |
| t-SNE (Barnes-Hut / FFT) | 3% / 4% |
| PaCMAP | 40% |
| PHATE | 95% (landmark diffusion; the MDS loop is short) |
| Diffusion maps | 100% (no epoch loop: time-based only) |

## Chrome check

Each method at (or, for PHATE and diffusion maps, just under) its default, one run at a time, headless Chrome 157 (the
module runs in a Web Worker, as it will in FlowNG):

| Method | Events | Chrome time | Predicted | Ratio | Chrome peak MB | Predicted MB |
|---|---:|---:|---:|---:|---:|---:|
| UMAP | 180,000 | 50.4 s | 59.3 s | 0.85 | 236 | 185 |
| densMAP | 150,000 | 46.8 s | 57.1 s | 0.82 | 184 | 160 |
| t-SNE (Barnes-Hut) | 31,000 | 53.9 s | 58.8 s | 0.92 | 118 | 118 |
| t-SNE (FFT) | 98,000 | 45.6 s | 59.8 s | 0.76 | 370 | 379 |
| PaCMAP | 340,000 | 51.0 s | 59.5 s | 0.86 | 704 | 704 |
| PHATE | 130,000 | 49.5 s | 54.3 s | 0.91 | 1,481 | 1,483 |
| Diffusion maps | 130,000 | 44.4 s | 48.1 s | 0.92 | 1,457 | 1,465 |
| Phenograph | 440,000 | 41.6 s | 59.4 s | 0.70 | 685 | 705 |
| FlowSOM | 1,600,000 | 56.1 s | 57.8 s | 0.97 | 136 | 136 |

Chrome is 3–30% faster than the fit (the fit's runs shared the machine 4 at a
time), so the predictions are slightly pessimistic, which is the safe side.
Memory agrees within a few MB except UMAP/densMAP, where linear memory grows in
steps.

## Caveats

- Timings are from one machine (Apple M4 Pro) with 4 runs at a time; a slower
  laptop will be proportionally slower, which is why FlowNG shows the
  prediction and lets the user lower or raise the event count.
- The memory ceiling is the module's own 4 GB; the browser tab also holds
  FlowNG's events. A 2M-event, 20-channel file is 160 MB in FlowNG, so this is
  small next to the module.
- The synthetic data used for the channel test are easy (well-separated
  populations), so they say nothing about embedding quality, only cost.
