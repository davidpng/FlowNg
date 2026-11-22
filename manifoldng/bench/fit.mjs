// Fit time and memory against N for each method from results.jsonl and derive
// FlowNG's per-method event limits. Writes limits.json and prints a Markdown
// table for doc/MANIFOLDNG_BENCH.md.
//   time:   secs  = a * n^b            (least squares in log-log, points with n >= 25k)
//   memory: peakMB = c + m * n         (least squares, all points)
// cap = largest n with predicted secs <= 60 (on the reference machine) and
//       predicted peakMB <= 3500 (the 4 GB wasm32 ceiling, less headroom),
//       rounded down to 2 significant figures, never above 10,000,000.
// It is both the default and the maximum; FlowNG rescales the 60 s to the
// user's machine with mng_calibrate().
// pre = share of the run before the first optimiser epoch (from progress_check),
// used by FlowNG's status bar.
// beta = time exponent for channel count (results_d.jsonl, 10 vs 40 channels).
import { readFileSync, writeFileSync, existsSync } from 'node:fs';

const NAMES = { 1: 'umap', 2: 'tsne_bh', 3: 'tsne_fft', 4: 'pacmap', 5: 'phate', 6: 'densmap', 7: 'diffusion_maps', 10: 'phenograph', 11: 'flowsom' };
const file = process.argv[2] || 'results.jsonl', dataset = process.argv[3] || 'mm_mrd.f32';
const rows = readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse).filter(r => r.dataset === dataset && !r.error);
const round2 = x => { if (!(x > 0)) return 0; const p = 10 ** (Math.floor(Math.log10(x)) - 1); return Math.floor(x / p) * p; };
function lsq(xs, ys) {
  const n = xs.length, mx = xs.reduce((a, b) => a + b) / n, my = ys.reduce((a, b) => a + b) / n;
  let sxy = 0, sxx = 0; for (let i = 0; i < n; i++) { sxy += (xs[i] - mx) * (ys[i] - my); sxx += (xs[i] - mx) ** 2; }
  const slope = sxx ? sxy / sxx : 0; return [my - slope * mx, slope];
}
const drows = existsSync('results_d.jsonl') ? readFileSync('results_d.jsonl', 'utf8').split('\n').filter(Boolean).map(JSON.parse).filter(r => !r.error && r.n === 50000) : [];
// Share of run time before the first optimiser epoch (progress_check.mjs at 20k events, real data).
// Diffusion maps has no epoch loop (1 = time-based only); Phenograph/FlowSOM report their own stages.
const PRE = { 1: 0.10, 2: 0.03, 3: 0.04, 4: 0.40, 5: 0.95, 6: 0.07, 7: 1, 10: 0.6, 11: 0 };
const limits = {}, table = [];
for (const [id, name] of Object.entries(NAMES)) {
  const pts = rows.filter(r => r.method === +id).sort((a, b) => a.n - b.n);
  if (pts.length < 2) continue;
  const tp = pts.filter(r => r.n >= 25000).length >= 2 ? pts.filter(r => r.n >= 25000) : pts;
  const [la, b] = lsq(tp.map(r => Math.log(r.n)), tp.map(r => Math.log(r.secs)));
  const a = Math.exp(la);
  const [c, m] = lsq(pts.map(r => r.n), pts.map(r => r.peakMB));
  const nTime = (60 / a) ** (1 / b), nMem35 = (3500 - c) / m;
  const cap = Math.min(round2(Math.min(nTime, nMem35)), 1e7);
  const dp = drows.filter(r => r.method === +id), t10 = dp.find(r => r.d === 10), t40 = dp.find(r => r.d === 40);
  const beta = t10 && t40 ? Math.log(t40.secs / t10.secs) / Math.log(4) : 0;
  limits[name] = { method: +id, cap, limitedBy: nTime <= nMem35 ? 'time' : 'memory', pre: PRE[id],
    time: { a: +a.toPrecision(4), b: +b.toFixed(3), beta: +Math.max(0, beta).toFixed(2), refChannels: 20 },
    mem: { c: +c.toFixed(1), mPerK: +(m * 1000).toFixed(4) } };
  table.push({ name, cap, by: limits[name].limitedBy, b, beta, mPerK: m * 1000, secsAtCap: a * cap ** b, mbAtCap: c + m * cap, pts });
}
const cal = existsSync('calibrate.jsonl') ? readFileSync('calibrate.jsonl', 'utf8').split('\n').filter(Boolean).map(JSON.parse).pop() : null;
limits._reference = { machine: 'Apple M4 Pro, 24 GB', browser: 'Chrome 157', calibrateSecs: cal ? +cal.median.toFixed(4) : null, capSecs: 60, memCapMB: 3500 };
writeFileSync('limits.json', JSON.stringify(limits, null, 1) + '\n');
console.log('| Method | Cap (events) | Limited by | Predicted at cap | Time exponent (events) | Time exponent (channels) | MB per 1k events |');
console.log('|---|---:|---|---:|---:|---:|---:|');
for (const t of table) console.log(`| ${t.name} | ${t.cap.toLocaleString('en')} | ${t.by} | ${t.secsAtCap.toFixed(0)} s / ${Math.round(t.mbAtCap).toLocaleString('en')} MB | ${t.b.toFixed(2)} | ${Math.max(0, t.beta).toFixed(2)} | ${t.mPerK.toFixed(2)} |`);
