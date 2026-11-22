"""Build the ManifoldNG WebAssembly module and embed it in FlowNG.html.

    /usr/bin/python3 scripts/build_manifoldng.py           # build, then write the module into FlowNG.html
    /usr/bin/python3 scripts/build_manifoldng.py --check   # build, then only confirm FlowNG.html holds exactly these bytes

The module is built from manifoldng/ with `cargo build --release --target wasm32-unknown-unknown --locked`.
Local paths are remapped (--remap-path-prefix) so the module never carries the builder's home folder or user
name, which makes the bytes the same on any machine with the same toolchain (manifoldng/rust-toolchain.toml).

FlowNG.html holds the module as gzip + base64 text in
    <script id="manifoldng-wasm" type="application/octet-stream" data-sha256="..." data-bytes="...">...</script>
where data-sha256 and data-bytes describe the uncompressed .wasm. The gzip stream is written with mtime 0, so the
embedded text is reproducible too. See doc/SECURITY.md ("ManifoldNG module").
"""
import base64, gzip, hashlib, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRATE = ROOT / 'manifoldng'
HTML = ROOT / 'FlowNG.html'
WASM = CRATE / 'target' / 'wasm32-unknown-unknown' / 'release' / 'manifoldng.wasm'
BLOCK_RE = re.compile(r'<script id="manifoldng-wasm" type="application/octet-stream"[^>]*>[^<]*</script>')


def build():
    cargo_home = Path(os.environ.get('CARGO_HOME', Path.home() / '.cargo')).resolve()
    rustup_home = Path(os.environ.get('RUSTUP_HOME', Path.home() / '.rustup')).resolve()
    flags = [
        '--cfg', 'getrandom_backend="custom"',          # same as manifoldng/.cargo/config.toml (RUSTFLAGS replaces it)
        f'--remap-path-prefix={cargo_home}=/cargo',
        f'--remap-path-prefix={rustup_home}=/rustup',
        f'--remap-path-prefix={ROOT}=/flowng',
    ]
    env = dict(os.environ, CARGO_ENCODED_RUSTFLAGS='\x1f'.join(flags))
    env.pop('RUSTFLAGS', None)
    subprocess.run(['cargo', 'build', '--release', '--target', 'wasm32-unknown-unknown', '--locked'],
                   cwd=CRATE, env=env, check=True)
    wasm = WASM.read_bytes()
    home = str(Path.home()).encode()
    if home in wasm or b'/Users/' in wasm or b'/home/' in wasm:
        sys.exit('The module still contains a local path; check the --remap-path-prefix flags.')
    return wasm


def block_for(wasm):
    sha = hashlib.sha256(wasm).hexdigest()
    b64 = base64.b64encode(gzip.compress(wasm, compresslevel=9, mtime=0)).decode('ascii')
    return (f'<script id="manifoldng-wasm" type="application/octet-stream" data-sha256="{sha}" '
            f'data-bytes="{len(wasm)}">{b64}</script>'), sha, b64


def main():
    check = '--check' in sys.argv[1:]
    wasm = build()
    block, sha, b64 = block_for(wasm)
    html = HTML.read_text(encoding='utf-8')
    found = BLOCK_RE.findall(html)
    if len(found) != 1:
        sys.exit(f'FlowNG.html must contain exactly one manifoldng-wasm block (found {len(found)}).')
    print(f'module: {len(wasm):,} bytes, sha256 {sha}; embedded text {len(b64):,} bytes')
    if check:
        if found[0] != block:
            m = re.search(r'data-sha256="([0-9a-f]*)"', found[0])
            sys.exit(f'MISMATCH: FlowNG.html holds {m.group(1) if m else "?"}, a fresh build gives {sha}')
        print('OK: FlowNG.html holds exactly this build')
        return
    if found[0] == block:
        print('FlowNG.html already holds this build; unchanged')
        return
    HTML.write_text(BLOCK_RE.sub(lambda _: block, html, count=1), encoding='utf-8')
    print('FlowNG.html updated')


if __name__ == '__main__':
    main()
