// Print the progress events each method emits (stage: count, first/last) and the calibration time.
import { readFileSync } from 'node:fs';
const [wasmPath, n = '20000', dataPath = 'bench/data/mm_mrd.f32'] = process.argv.slice(2);
const d = 20, N = +n;
const all = readFileSync(dataPath); const X = new Float32Array(all.buffer, all.byteOffset, N * d);
for (const m of [1, 2, 3, 4, 5, 6, 7, 10, 11]) {
  const ev = [];
  const t0 = performance.now();
  const { instance } = await WebAssembly.instantiate(readFileSync(wasmPath), { env: { mng_progress: (s, a, b) => ev.push([s, a, b, performance.now() - t0]) } });
  const e = instance.exports;
  const dp = e.mng_alloc(X.byteLength); new Float32Array(e.memory.buffer, dp, X.length).set(X);
  const ts = performance.now(); const rc = e.mng_run(m, dp, N, d, 0, 0, 42); const secs = (performance.now() - ts) / 1000;
  const by = {}; for (const [s, a, b, t] of ev) { (by[s] ??= { count: 0, first: t, last: t, total: b }); by[s].count++; by[s].last = t; }
  console.log(`m=${m} rc=${rc} ${secs.toFixed(1)}s events=${ev.length}`, Object.entries(by).map(([s, o]) => `stage${s}:${o.count}x total=${o.total} @${(o.first / 1000).toFixed(1)}-${(o.last / 1000).toFixed(1)}s`).join(' '));
  if (m === 11) { const t = performance.now(); e.mng_calibrate(); console.log('calibrate', ((performance.now() - t) / 1000).toFixed(3), 's'); }
}
