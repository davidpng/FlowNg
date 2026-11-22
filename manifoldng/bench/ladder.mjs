// Scaling ladder: run each method at increasing N in a fresh process (so linear
// memory starts from zero) until it exceeds the time or memory budget.
// Appends one JSON line per run to results.jsonl; reruns skip finished points.
// Usage: node ladder.mjs <wasm> <methods comma list> [--data data/mm_mrd.f32 --d 20] [--jobs 4]
import { spawn } from 'node:child_process';
import { readFileSync, appendFileSync, existsSync } from 'node:fs';

const args = process.argv.slice(2);
const opt = (k, dflt) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : dflt; };
const wasm = args[0], methods = args[1].split(',').map(Number);
const data = opt('--data', null), d = +opt('--d', 20), jobs = +opt('--jobs', 4);
const ladder = (opt('--ns', '10000,25000,50000,100000,200000,500000,1000000,2000000')).split(',').map(Number);
const TIME_LIMIT = +opt('--max-secs', 600), MEM_LIMIT_MB = 3500, HARD_TIMEOUT_MS = (TIME_LIMIT * 2 + 60) * 1000;
const OUT = opt('--out', 'results.jsonl');
const tag = data ? data.split('/').pop() : 'synthetic';

const done = new Map();
if (existsSync(OUT)) for (const l of readFileSync(OUT, 'utf8').split('\n').filter(Boolean)) {
  const r = JSON.parse(l); done.set(`${r.dataset}|${r.method}|${r.n}|${r.d}`, r);
}

function runOne(method, n) {
  return new Promise(res => {
    const a = ['run_one.mjs', wasm, String(method), String(n), String(d), '42', ''];
    if (data) a.push('--data', data);
    const p = spawn('node', a, { stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '', err = '';
    p.stdout.on('data', b => out += b); p.stderr.on('data', b => err += b);
    const t = setTimeout(() => p.kill('SIGKILL'), HARD_TIMEOUT_MS);
    p.on('close', code => {
      clearTimeout(t);
      let r;
      try { r = JSON.parse(out.trim().split('\n').pop()); }
      catch { r = { method, n, d, error: code === null ? 'killed (hard timeout)' : (err.trim().split('\n').slice(-3).join(' | ') || `exit ${code}`) }; }
      r.dataset = tag; r.when = new Date().toISOString();
      appendFileSync(OUT, JSON.stringify(r) + '\n');
      res(r);
    });
  });
}

async function methodLadder(m) {
  for (const n of ladder) {
    const key = `${tag}|${m}|${n}|${d}`;
    let r = done.get(key) || await runOne(m, n);
    console.log(`m=${m} n=${n} d=${d} ${r.error ? 'ERROR ' + r.error : r.secs + 's ' + r.peakMB + 'MB'}`);
    if (r.error || r.secs > TIME_LIMIT || r.peakMB > MEM_LIMIT_MB) break;
  }
}

const queue = [...methods];
await Promise.all(Array.from({ length: Math.min(jobs, queue.length) }, async () => {
  while (queue.length) await methodLadder(queue.shift());
}));
console.log('ladder done');
