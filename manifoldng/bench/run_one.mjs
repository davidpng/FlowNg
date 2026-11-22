// Run one ManifoldNG method on synthetic (or file) data in a fresh WASM instance
// and print one JSON line: time, peak linear memory, result sanity.
// Usage: node run_one.mjs <wasm> <method> <n> <d> [seed] [params,comma,separated] [--data file.f32]
import { readFileSync } from 'node:fs';

const [wasmPath, methodS, nS, dS, seedS = '42', paramsS = ''] = process.argv.slice(2);
const dataIdx = process.argv.indexOf('--data');
const method = +methodS, n = +nS, d = +dS, seed = +seedS;
const params = paramsS ? paramsS.split(',').map(Number) : [];

// mulberry32 + Box-Muller: deterministic synthetic flow-like data,
// 12 Gaussian populations of unequal size and spread.
function rng(s) { return () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function synth(n, d, seed) {
  const r = rng(seed), g = () => Math.sqrt(-2 * Math.log(r() + 1e-12)) * Math.cos(2 * Math.PI * r());
  const K = 12, centers = [], scales = [], w = [];
  for (let k = 0; k < K; k++) { centers.push(Array.from({ length: d }, () => r() * 4)); scales.push(0.1 + r() * 0.4); w.push(0.2 + r()); }
  const tot = w.reduce((a, b) => a + b), cum = []; w.reduce((a, b, i) => (cum[i] = (a + b) / tot, a + b), 0);
  const X = new Float32Array(n * d), lab = new Int32Array(n);
  for (let i = 0; i < n; i++) {
    const u = r(); let k = cum.findIndex(c => u <= c); if (k < 0) k = K - 1; lab[i] = k;
    for (let j = 0; j < d; j++) X[i * d + j] = centers[k][j] + scales[k] * g();
  }
  return { X, lab };
}

let X, lab = null;
if (dataIdx > 0) {
  const buf = readFileSync(process.argv[dataIdx + 1]);
  const all = new Float32Array(buf.buffer, buf.byteOffset, buf.byteLength / 4);
  const total = all.length / d; if (n > total) { console.log(JSON.stringify({ method, n, d, error: `file has only ${total} events` })); process.exit(0); }
  X = all.subarray(0, n * d);
} else ({ X, lab } = synth(n, d, 1234));

const { instance } = await WebAssembly.instantiate(readFileSync(wasmPath), { env: { mng_progress: () => {} } });
const e = instance.exports;
const mem0 = e.memory.buffer.byteLength;
const dp = e.mng_alloc(X.byteLength);
new Float32Array(e.memory.buffer, dp, X.length).set(X);
const pp = e.mng_alloc(Math.max(8, params.length * 8));
new Float64Array(e.memory.buffer, pp, params.length).set(params);
const t0 = performance.now();
const rc = e.mng_run(method, dp, n, d, pp, params.length, seed);
const secs = (performance.now() - t0) / 1000;
const out = { method, n, d, seed, params, secs: +secs.toFixed(3), peakMB: +(e.memory.buffer.byteLength / 2 ** 20).toFixed(1), inputMB: +(X.byteLength / 2 ** 20).toFixed(1), baseMB: +(mem0 / 2 ** 20).toFixed(1) };
if (rc !== 0) {
  out.error = new TextDecoder().decode(new Uint8Array(e.memory.buffer, e.mng_error_ptr(), e.mng_error_len()));
} else {
  const res = new Float32Array(e.memory.buffer, e.mng_result_ptr(), e.mng_result_len()).slice();
  out.resultLen = res.length;
  out.nonFinite = res.reduce((a, v) => a + (Number.isFinite(v) ? 0 : 1), 0);
  if (res.length === n) {
    const k = new Set(res); out.nClusters = [...k].filter(v => v >= 0).length; out.unassigned = res.filter(v => v < 0).length;
    if (lab) out.ari = +ari(lab, res).toFixed(4);
  } else {
    let mn = [Infinity, Infinity], mx = [-Infinity, -Infinity];
    for (let i = 0; i < n; i++) for (let j = 0; j < 2; j++) { const v = res[2 * i + j]; if (v < mn[j]) mn[j] = v; if (v > mx[j]) mx[j] = v; }
    out.range = [mn, mx].map(a => a.map(v => +v.toFixed(2)));
    if (lab) out.knnPurity = +knnPurity(res, lab, n).toFixed(4);
  }
}
console.log(JSON.stringify(out));

// Adjusted Rand index between true and found labels.
function ari(a, b) {
  const key = new Map(); const ca = new Map(), cb = new Map();
  for (let i = 0; i < a.length; i++) { const k = a[i] + ',' + b[i]; key.set(k, (key.get(k) || 0) + 1); ca.set(a[i], (ca.get(a[i]) || 0) + 1); cb.set(b[i], (cb.get(b[i]) || 0) + 1); }
  const c2 = x => x * (x - 1) / 2; let sij = 0, sa = 0, sb = 0;
  for (const v of key.values()) sij += c2(v); for (const v of ca.values()) sa += c2(v); for (const v of cb.values()) sb += c2(v);
  const exp = sa * sb / c2(a.length), mx = (sa + sb) / 2; return (sij - exp) / (mx - exp);
}
// Fraction of 10 nearest embedding neighbours (on a 2k sample, brute force) sharing the true label.
function knnPurity(Y, lab, n) {
  const m = Math.min(2000, n), step = n / m; let hit = 0, tot = 0;
  const S = Array.from({ length: m }, (_, i) => Math.floor(i * step));
  for (const i of S) {
    const ds = S.filter(j => j !== i).map(j => [(Y[2 * i] - Y[2 * j]) ** 2 + (Y[2 * i + 1] - Y[2 * j + 1]) ** 2, j]).sort((x, y) => x[0] - y[0]).slice(0, 10);
    for (const [, j] of ds) { tot++; if (lab[j] === lab[i]) hit++; }
  }
  return hit / tot;
}
