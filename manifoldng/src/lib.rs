//! ManifoldNG: dimensionality reduction and clustering for FlowNG.
//!
//! The crate compiles to `wasm32-unknown-unknown` and is embedded in FlowNG.html.
//! It exposes a small C ABI instead of wasm-bindgen so the JS glue in FlowNG stays
//! a few hand-written lines that anyone can audit:
//!
//! 1. `mng_alloc(bytes)` returns a pointer; JS copies the row-major `n x d` f32
//!    event matrix and the f64 parameter vector into linear memory.
//! 2. `mng_run(method, data, n, d, params, n_params, seed)` returns 0 on success.
//! 3. `mng_result_ptr()` / `mng_result_len()` describe the f32 result
//!    (`n x 2` row-major coordinates, or `n` cluster labels).
//!    On failure `mng_error_ptr()` / `mng_error_len()` hold a UTF-8 message.
//! 4. `mng_free(ptr, bytes)` releases what `mng_alloc` gave.
//!
//! The same functions are callable natively (see `src/bin/mng_bench.rs`).

pub mod embed;
pub mod flowsom;
pub mod phenograph;
pub mod progress;

use std::cell::RefCell;

/// Method ids shared with FlowNG.html (`MANIFOLD_METHODS`).
pub mod method {
    pub const UMAP: u32 = 1;
    pub const TSNE_BH: u32 = 2;
    pub const TSNE_FFT: u32 = 3;
    pub const PACMAP: u32 = 4;
    pub const PHATE: u32 = 5;
    pub const DENSMAP: u32 = 6;
    pub const DIFFUSION_MAPS: u32 = 7;
    pub const PHENOGRAPH: u32 = 10;
    pub const FLOWSOM: u32 = 11;
}

/// Read parameter `i`, or `default` when absent or NaN.
pub(crate) fn p(params: &[f64], i: usize, default: f64) -> f64 {
    match params.get(i) {
        Some(v) if v.is_finite() => *v,
        _ => default,
    }
}

/// Run one method on a row-major `n x d` matrix. Embeddings return `n * 2`
/// row-major values; clusterings return `n` labels (as f32, -1 = unassigned).
pub fn run(method: u32, data: &[f32], n: usize, d: usize, params: &[f64], seed: u64) -> Result<Vec<f32>, String> {
    if n == 0 || d == 0 {
        return Err("no events or no channels".into());
    }
    if data.len() != n * d {
        return Err(format!("data length {} != n*d {}", data.len(), n * d));
    }
    if data.iter().any(|v| !v.is_finite()) {
        return Err("input contains NaN or infinite values".into());
    }
    progress::install();
    if method < method::PHENOGRAPH {
        progress::begin(progress::NEIGHBOURS);
    }
    match method {
        method::UMAP => embed::umap(data, n, d, params, seed),
        method::TSNE_BH => embed::tsne(data, n, d, params, seed, "bh"),
        method::TSNE_FFT => embed::tsne(data, n, d, params, seed, "fft"),
        method::PACMAP => embed::pacmap(data, n, d, params, seed),
        method::PHATE => embed::phate(data, n, d, params, seed),
        method::DENSMAP => embed::densmap(data, n, d, params, seed),
        method::DIFFUSION_MAPS => embed::diffusion_maps(data, n, d, params, seed),
        method::PHENOGRAPH => phenograph::phenograph(data, n, d, params, seed)
            .map(|l| l.into_iter().map(|v| v as f32).collect()),
        method::FLOWSOM => flowsom::flowsom(data, n, d, params, seed)
            .map(|l| l.into_iter().map(|v| v as f32).collect()),
        _ => Err(format!("unknown method {method}")),
    }
}

// ─── C ABI ──────────────────────────────────────────────────────────────────

thread_local! {
    static RESULT: RefCell<Vec<f32>> = const { RefCell::new(Vec::new()) };
    static ERROR: RefCell<String> = const { RefCell::new(String::new()) };
}

#[no_mangle]
pub extern "C" fn mng_alloc(bytes: usize) -> *mut u8 {
    let mut v: Vec<u8> = Vec::with_capacity(bytes.max(1));
    let ptr = v.as_mut_ptr();
    std::mem::forget(v);
    ptr
}

/// # Safety
/// `ptr` must come from `mng_alloc(bytes)` with the same `bytes`.
#[no_mangle]
pub unsafe extern "C" fn mng_free(ptr: *mut u8, bytes: usize) {
    if !ptr.is_null() {
        drop(Vec::from_raw_parts(ptr, 0, bytes.max(1)));
    }
}

/// # Safety
/// `data` must point at `n * d` f32 values and `params` at `n_params` f64 values.
#[no_mangle]
pub unsafe extern "C" fn mng_run(
    method: u32,
    data: *const f32,
    n: usize,
    d: usize,
    params: *const f64,
    n_params: usize,
    seed: u32,
) -> i32 {
    let data = std::slice::from_raw_parts(data, n * d);
    let params = if n_params == 0 { &[][..] } else { std::slice::from_raw_parts(params, n_params) };
    RESULT.with(|r| r.borrow_mut().clear());
    match run(method, data, n, d, params, seed as u64) {
        Ok(v) => {
            RESULT.with(|r| *r.borrow_mut() = v);
            0
        }
        Err(e) => {
            ERROR.with(|s| *s.borrow_mut() = e);
            1
        }
    }
}

#[no_mangle]
pub extern "C" fn mng_result_ptr() -> *const f32 {
    RESULT.with(|r| r.borrow().as_ptr())
}

#[no_mangle]
pub extern "C" fn mng_result_len() -> usize {
    RESULT.with(|r| r.borrow().len())
}

/// Drop the result buffer once JS has copied it out.
#[no_mangle]
pub extern "C" fn mng_result_clear() {
    RESULT.with(|r| *r.borrow_mut() = Vec::new());
}

#[no_mangle]
pub extern "C" fn mng_error_ptr() -> *const u8 {
    ERROR.with(|s| s.borrow().as_ptr())
}

#[no_mangle]
pub extern "C" fn mng_error_len() -> usize {
    ERROR.with(|s| s.borrow().len())
}

/// All randomness is seeded, so OS entropy is never needed. getrandom 0.3 is
/// built with the "custom" backend on wasm32 (see .cargo/config.toml); failing
/// here makes any accidental unseeded use a loud error.
#[cfg(target_arch = "wasm32")]
#[no_mangle]
unsafe extern "Rust" fn __getrandom_v03_custom(_dest: *mut u8, _len: usize) -> Result<(), getrandom::Error> {
    Err(getrandom::Error::UNSUPPORTED)
}

/// Fixed workload FlowNG times once per session to scale the benchmark's time
/// predictions to this machine: FlowSOM (10x10, rlen 25, no consensus) on
/// 10,000 deterministic synthetic events with 20 channels. Returns a checksum
/// so the work cannot be optimised away.
#[no_mangle]
pub extern "C" fn mng_calibrate() -> f64 {
    let (n, d) = (10_000usize, 20usize);
    let mut s: u64 = 0x2545F4914F6CDD1D;
    let data: Vec<f32> = (0..n * d)
        .map(|i| {
            s ^= s << 13;
            s ^= s >> 7;
            s ^= s << 17;
            ((i / d) % 7) as f32 + (s >> 40) as f32 / (1u64 << 24) as f32
        })
        .collect();
    let params = [10.0, 10.0, 25.0, 10.0, 0.05, 0.01, 0.0];
    match flowsom::flowsom(&data, n, d, &params, 1) {
        Ok(l) => l.iter().map(|&v| v as f64).sum(),
        Err(_) => -1.0,
    }
}
