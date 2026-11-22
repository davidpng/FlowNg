//! Progress reporting to the host. On wasm32 every report calls the imported
//! JS function `env.mng_progress(stage, done, total)`, which FlowNG's worker
//! forwards to the page with postMessage while the run continues. Natively it
//! does nothing. Reports are thinned to about 100 per stage.

/// Stage ids shared with FlowNG.html (`MANIFOLD_STAGES`).
pub const NEIGHBOURS: u32 = 1;
pub const GRAPH: u32 = 2;
pub const OPTIMISE: u32 = 3; // == manifolds_rs::wtime::STAGE_OPTIMISE
pub const CLUSTER: u32 = 4;
pub const ASSIGN: u32 = 5;

#[cfg(target_arch = "wasm32")]
mod host {
    #[link(wasm_import_module = "env")]
    extern "C" {
        pub fn mng_progress(stage: u32, done: f64, total: f64);
    }
}

/// Report `done` of `total` for `stage`. Thinned: forwarded at the first and
/// last step and every ~1% in between.
#[inline]
pub fn report(stage: u32, done: usize, total: usize) {
    let step = (total / 100).max(1);
    if done == 0 || done + 1 >= total || done % step == 0 {
        send(stage, done, total);
    }
}

/// Mark the start of a stage whose length is unknown (total = 0).
pub fn begin(stage: u32) {
    send(stage, 0, 0);
}

#[allow(unused_variables)]
fn send(stage: u32, done: usize, total: usize) {
    #[cfg(target_arch = "wasm32")]
    unsafe {
        host::mng_progress(stage, done as f64, total as f64)
    }
}

/// Route manifolds-rs's per-epoch reports here for the duration of one run.
pub fn install() {
    manifolds_rs::wtime::set_progress_hook(Some(report));
}

/// Louvain level `level` of at most `max_levels` (levels usually stop early).
pub fn send_level(level: usize, max_levels: usize) {
    send(CLUSTER, level, max_levels);
}
