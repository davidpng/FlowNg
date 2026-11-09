(async () => {
  const out = { results: [], error: null };
  const add = (name, pass, detail) => { out.results.push({ name, pass: !!pass, detail: detail || '' }); fetch('/progress', { method: 'POST', body: (pass ? 'ok ' : 'FAIL ') + name }); };
  const P = m => fetch('/progress', { method: 'POST', body: m });
  try {
    P('start');
    const f = document.getElementById('f');
    while (!(f.contentWindow && f.contentWindow.FlowCheck)) await new Promise(r => setTimeout(r, 50));   // load can fire before a listener is attached
    P('iframe loaded');
    const W = f.contentWindow, FC = W.FlowCheck;
    const manifest = await (await fetch('/check/manifest.json', { cache: 'no-store' })).json();
    const sample = await (await fetch('/samples/Complex_Analysis_FlowNg.html')).text();
    const appSrc = await (await fetch('/FlowNG.html')).text();
    P('sources loaded');
    const jobs = await (await fetch('/_job/jobs.json')).json();
    const extras = [];
    for (const x of jobs.extras) extras.push({ name: x.name, text: await (await fetch('/_job/extra/' + x.n + '.html')).text() });

    const status = async (name, text, wantOk, mustSay) => {
      const v = await FC.check(text, manifest);
      const good = (v.status === 'ok') === wantOk && (!mustSay || v.reasons.some(r => r.includes(mustSay)));
      add(name, good, v.status === 'ok' ? `ok ${v.variant} ${v.entry.commit} ${v.entry.dataRules}` : v.reasons.join(' | ').slice(0, 160));
      return v;
    };
    const BLK = /<script id="flowng-bundle" type="application\/json">([^<]*)<\/script>/;
    const blk = (t) => t.match(BLK)[0];
    const withBody = (t, body) => t.replace(BLK, () => '<script id="flowng-bundle" type="application/json">' + body.replace(/</g, '\\u003c') + '<\/script>');   // the app writes < as \u003c
    const minimal = (extra) => JSON.stringify(Object.assign({ format: 2, name: 'x', files: [{ filename: 'f', nEvents: 1, nPar: 1, params: [{ name: 'A' }] }] }, extra || {}));

    P('starting checks');
    // genuine
    await status('repo sample is a released build', sample, true);
    for (const e of extras) await status('extra: ' + e.name, e.text, true);

    // allowed edits
    await status('title changed', sample.replace(/<title>[\s\S]*?<\/title>/, '<title>Class 3</title>'), true);
    await status('data block replaced by a valid small one', withBody(sample, minimal()), true);
    await status('markup whitespace reflowed', sample.replace('><', '>\n<').replace('><', '>\n<'), true);

    // code attacks
    const attacks = [
      ['extra script tag', t => t.replace('</body>', '<script>fetch("//evil")<\/script></body>')],
      ['event-handler attribute on body', t => t.replace('<body', '<body onload="fetch(1)"')],
      ['image with onerror', t => t.replace('</body>', '<img src=x onerror=alert(1)></body>')],
      ['iframe', t => t.replace('</body>', '<iframe src="//evil"></iframe></body>')],
      ['external stylesheet', t => t.replace('</head>', '<link rel=stylesheet href=//evil/x.css></head>')],
      ['meta refresh', t => t.replace('</head>', '<meta http-equiv=refresh content="0;url=//evil"></head>')],
      ['one character of code changed', t => t.replace('function showToast', 'function showToasT')],
      ['code added inside the app script', t => t.replace('function showToast(', 'fetch("//evil");function showToast(')],
      ['style attribute on <html>', t => t.replace('<html', '<html style="x:y"')],
      ['comment added', t => t.replace('</body>', '<!--x--></body>')],
      ['svg with onload', t => t.replace('</body>', '<svg onload="fetch(1)"></svg></body>')],
      ['noscript wrapper', t => t.replace('</body>', '<noscript><img src=x onerror=alert(1)></noscript></body>')],
      ['template with script', t => t.replace('</body>', '<template><script>fetch(1)<\/script></template></body>')],
      ['base tag', t => t.replace('<head>', '<head><base href="//evil/">')],
      ['second look-alike data script (no type)', t => t.replace('</body>', '<script id="flowng-bundle">fetch(1)<\/script></body>')],
      ['two exact data blocks', t => t.replace(blk(t), blk(t) + blk(t))],
      ['data block moved elsewhere', t => t.replace(blk(t), '').replace('</body>', blk(t) + '</body>')],
      ['data block type changed to JavaScript', t => t.replace('id="flowng-bundle" type="application/json"', 'id="flowng-bundle" type="text/javascript"')],
      ['data block closed early, then a script', t => t.replace(blk(t), blk(t).slice(0, -9) + '<\/script><script>fetch(1)<\/script><script>')],
    ];
    for (const [n, fn] of attacks) await status('attack: ' + n, fn(sample), false);
    await status('plain app source (no data block)', appSrc, false, 'no data block');
    await status('not html', 'hello world', false);
    await status('empty file', '', false);

    // data-block checks
    const st = (name, body, want, say, base) => status(name, withBody(base || sample, body), want, say);
    await st('data: not JSON', 'not json', false, 'valid JSON');
    await st('data: wrong format number', minimal({ format: 9 }), false, 'format');
    await st('data: no files', JSON.stringify({ format: 2, files: [] }), false, 'no files');
    await st('data: size mismatch', JSON.stringify({ format: 2, files: [{ filename: 'f', nEvents: 1, nPar: 2, params: [{}] }] }), false, 'parameter list');
    await st('data: event data not plain encoded', minimal({ files: [{ filename: 'f', nEvents: 1, nPar: 1, params: [{}], rawData: 'AAAA"BBB' }] }), false, 'encoded');
    await st('data: array instead of object', '[1,2]', false, 'data object');
    // strict rules apply to old builds only
    const hostile = minimal({ files: [{ filename: 'a"><img src=x onerror=alert(1)>', nEvents: 1, nPar: 1, params: [{ name: 'P' }] }] });
    await st('strict build: hostile file name rejected', hostile, false, 'older FlowNG build');
    await st('strict build: hostile parameter name rejected', minimal({ files: [{ filename: 'f', nEvents: 1, nPar: 1, params: [{ name: "x'y" }] }] }), false, 'older FlowNG build');
    await st('strict build: ordinary names with spaces/dots pass', minimal({ files: [{ filename: 'Sample 1.fcs', nEvents: 1, nPar: 1, params: [{ name: 'FS INT LIN', longName: 'CD45 KrO' }] }] }), true);
    const cur = extras.find(e => /full/.test(e.name));
    if (cur) {
      await st('standard build: hostile names are escaped, so allowed', hostile, true, null, cur.text);
      await st('standard build: other data rules still apply', 'not json', false, 'valid JSON', cur.text);
    }
    // history strings with quotes are normal
    await st('strict build: quotes in history text are fine', minimal({ history: [{ t: 'x', what: 'Moved gate "Time"' }] }), true);

    // revocation
    const rm = JSON.parse(JSON.stringify(manifest));
    const e0 = (await FC.canonHash(sample)).hash;
    rm.revoked = [{ hash: e0, reason: 'Withdrawn for testing.' }];
    { const v = await FC.check(sample, rm); add('revoked build is refused with its reason', v.status === 'bad' && v.reasons[0] === 'Withdrawn for testing.'); }

    // update to the newest FlowNG
    const fullExtra = extras.find(e => /full/.test(e.name)), lockedExtra = extras.find(e => /locked/.test(e.name));
    for (const [label, text, variant] of [['strict sample', sample, 'full'], ['current full', fullExtra && fullExtra.text, 'full'], ['current locked', lockedExtra && lockedExtra.text, 'locked']]) {
      if (!text) continue;
      try {
        const v = await FC.check(text, manifest);
        const up = await FC.buildUpdate(v.body, variant, appSrc, manifest);
        const again = await FC.check(up.text, manifest);
        add('update: ' + label + ' -> newest, passes its own check, same data', again.status === 'ok' && again.body === v.body && again.variant === variant, `${again.entry && again.entry.commit} ${again.entry && again.entry.dataRules}`);
      } catch (e) { add('update: ' + label, false, e.message); }
    }
    try { await FC.buildUpdate(minimal(), 'full', appSrc.replace('function showToast', 'function showToasT'), manifest); add('update refuses an app source that is not the newest release', false); }
    catch (e) { add('update refuses an app source that is not the newest release', /newest listed release/.test(e.message)); }

    // page behaviour: really drop files on the page
    const dropFile = async (text, name) => {
      const dt = new W.DataTransfer(); dt.items.add(new W.File([text], name, { type: 'text/html' }));
      W.document.getElementById('drop').dispatchEvent(new W.DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true }));
      for (let i = 0; i < 100; i++) { await new Promise(r => setTimeout(r, 100)); const t = W.document.getElementById('result').innerText; if (t && !/Checking/.test(t)) return t; }
      return W.document.getElementById('result').innerText;
    };
    { const t = await dropFile(sample, 'good.html'); add('page: dropping a genuine file shows the green result', /Genuine FlowNG file/.test(t) && /Update to the newest/.test(t), t.slice(0, 80).replace(/\n/g, ' ')); }
    { const t = await dropFile(sample.replace('</body>', '<script>fetch(1)<\/script></body>'), 'bad.html'); add('page: dropping a tampered file shows the red result', /Do not open this file/.test(t) && !/Genuine/.test(t), t.slice(0, 80).replace(/\n/g, ' ')); }
    { const t = await dropFile('<html><body>hi</body></html>', 'plain.html'); add('page: dropping a plain web page shows red', /Do not open/.test(t)); }
    // the dropped file must never run anything or add elements to the page
    add('page: nothing from the dropped files ended up in the page', !W.document.querySelector('script[src]') && W.document.querySelectorAll('iframe,img,link[rel=stylesheet]').length === 0);
    // hostile file name is shown as text
    { const t = await dropFile(sample.replace('</body>', '<script>1<\/script></body>'), '"><img src=x onerror=window.__pwn=1>.html'); add('page: hostile file name is shown as text only', !W.__pwn && !W.document.querySelector('#result img'), ''); }
  } catch (e) { out.error = String(e) + (e.stack || ''); }
  await fetch('/result', { method: 'POST', body: JSON.stringify(out) });
})();
