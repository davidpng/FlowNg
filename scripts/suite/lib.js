// Shared helpers for the TESTING.md runs. Each suite page: <script src="lib.js"> then defines run(L).
window.sleep = ms => new Promise(r => setTimeout(r, ms));
const REPORT = { rows: [], errors: [], notes: [] };
window.R = (id, name, pass, detail) => { REPORT.rows.push({ id, name, pass: pass === true || pass === 'info' ? pass : !!pass, detail: detail === undefined ? '' : (typeof detail === 'string' ? detail : JSON.stringify(detail)) }); fetch('/progress', { method: 'POST', body: (pass ? 'ok ' : 'FAIL ') + id + ' ' + name }); };
window.N = t => REPORT.notes.push(t);
const FIX = ['00028336 001', '00028337 002', '00028338 003'].map(n => `TEST SAMPLE 26125127597b ${n}.LMD`);
window.newFrame = async (src, w = 1400, h = 900) => {
  document.querySelectorAll('iframe.app').forEach(f => f.remove());
  const f = document.createElement('iframe'); f.className = 'app'; f.style.cssText = `border:0;width:${w}px;height:${h}px`; f.src = src; document.body.appendChild(f);
  for (let i = 0; i < 400 && !(f.contentWindow && f.contentWindow.document && f.contentWindow.document.readyState === 'complete'); i++) await sleep(50);
  await sleep(1200);
  const win = f.contentWindow;
  win.addEventListener('error', e => REPORT.errors.push(String(e.message)));
  win.addEventListener('unhandledrejection', e => REPORT.errors.push('rejection: ' + String(e.reason)));
  const origErr = win.console.error; win.console.error = function (...a) { REPORT.errors.push('console.error: ' + a.map(String).join(' ').slice(0, 200)); return origErr.apply(this, a); };
  win.eval(`window.prompt=(m,d)=>d; window.confirm=()=>true; window.showSaveFilePicker=undefined; window.__clicks=[]; HTMLAnchorElement.prototype.click=function(){window.__clicks.push(this.download||this.href)};`);
  return { f, w: win, E: s => win.eval(s) };
};
window.loadFixtures = async (L, n = 3) => {
  for (const fn of FIX.slice(0, n)) {
    L.w.__b = await (await fetch('/' + encodeURIComponent(fn))).arrayBuffer();
    L.E(`loadFCS(__b, ${JSON.stringify(fn)})`); await sleep(5500);
  }
};
window.btmImport = async L => {
  const txt = await (await fetch('/samples/' + encodeURIComponent('BTM Triage Template v10_FlowNgtmplt.json'))).text();
  L.w.__tmpl = txt; L.E('importGates(__tmpl)'); await sleep(800);
  const rows = L.E(`[...document.querySelectorAll('#import-v3-modal tbody tr')].map(r=>r.innerText.replace(/\\s+/g,' ').trim().slice(-40))`);
  L.E('_doImportV3([0,1,2])'); await sleep(4500);
  return rows;
};
window.fresh = async (opts = {}) => {
  const L = await newFrame(opts.src || 'FlowNG.html');
  if (opts.fixtures) await loadFixtures(L, opts.fixtures === true ? 3 : opts.fixtures);
  if (opts.btm) { L.btmRows = await btmImport(L); }
  return L;
};
window.finish = async name => {
  REPORT.errors = REPORT.errors.filter((e, i, a) => a.indexOf(e) === i);
  await fetch('/result_' + name, { method: 'POST', body: JSON.stringify(REPORT) });
};
window.hist = L => L.E('_history.map(h=>h.what)');
window.toastText = L => L.w.document.getElementById('toast').textContent;
window.counts = (L, i = 0) => L.E(`fcsFiles[${i}].populations.filter(p=>p.gateInfo).length`);
