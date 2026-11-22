"""Extract a benchmark matrix from an FCS file: fluorescence channels (not FSC/SSC/Time),
arcsinh(x/cofactor) as FlowNG displays them, a seeded random subset of events, row-major f32.

Usage: python3 fcs_to_f32.py <file.fcs> <out.f32> [max_events=2000000] [cofactor=300]
Writes <out.f32> and <out.f32>.json (channel names, n, d)."""
import json, sys
import numpy as np

src, out = sys.argv[1], sys.argv[2]
max_ev = int(sys.argv[3]) if len(sys.argv) > 3 else 2_000_000
cof = float(sys.argv[4]) if len(sys.argv) > 4 else 300.0

with open(src, 'rb') as f:
    head = f.read(58).decode('ascii')
    t0, t1, d0, d1 = (int(head[a:b]) for a, b in ((10, 18), (18, 26), (26, 34), (34, 42)))
    f.seek(t0)
    text = f.read(t1 - t0 + 1).decode('latin-1')
delim = text[0]
parts = text[1:].split(delim)
kw = {parts[i].upper(): parts[i + 1] for i in range(0, len(parts) - 1, 2)}
if d0 == 0:
    d0, d1 = int(kw['$BEGINDATA']), int(kw['$ENDDATA'])
npar, tot = int(kw['$PAR']), int(kw['$TOT'])
assert kw['$DATATYPE'] == 'F', kw['$DATATYPE']
endian = '<' if kw['$BYTEORD'].startswith('1,2') else '>'
names = [kw.get(f'$P{i}N', f'P{i}') for i in range(1, npar + 1)]
data = np.memmap(src, dtype=endian + 'f4', mode='r', offset=d0, shape=(tot, npar))
keep = [i for i, nm in enumerate(names) if not any(s in nm.upper() for s in ('FSC', 'SSC', 'TIME'))]
rng = np.random.default_rng(1234)
idx = np.sort(rng.choice(tot, size=min(max_ev, tot), replace=False))
X = np.arcsinh(np.asarray(data[idx][:, keep], dtype=np.float64) / cof).astype(np.float32)
rng.shuffle(X)  # benchmarks take the first n rows, so make every prefix a random sample
X.tofile(out)
json.dump({'source': src.split('/')[-1], 'n': len(X), 'd': len(keep), 'channels': [names[i] for i in keep],
           'cofactor': cof, 'total_events': tot}, open(out + '.json', 'w'), indent=1)
print(len(X), len(keep), [names[i] for i in keep])
