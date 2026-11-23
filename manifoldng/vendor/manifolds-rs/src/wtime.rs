//! ManifoldNG patch: `std::time::Instant::now()` panics on wasm32-unknown-unknown,
//! and this crate calls it unconditionally for progress logging. On wasm32 this
//! stub reports zero elapsed time; everywhere else it is `std::time::Instant`.

#[cfg(not(target_arch = "wasm32"))]
pub use std::time::Instant;

#[cfg(target_arch = "wasm32")]
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Instant;

#[cfg(target_arch = "wasm32")]
impl Instant {
    pub fn now() -> Self { Instant }
    pub fn elapsed(&self) -> std::time::Duration { std::time::Duration::ZERO }
    pub fn duration_since(&self, _earlier: Instant) -> std::time::Duration { std::time::Duration::ZERO }
}

#[cfg(target_arch = "wasm32")]
impl std::ops::Sub for Instant {
    type Output = std::time::Duration;
    fn sub(self, _rhs: Instant) -> std::time::Duration { std::time::Duration::ZERO }
}

// ─── ManifoldNG patch: progress hook ─────────────────────────────────────────
// Optimiser loops call `progress(stage, done, total)` once per epoch. The
// embedding application installs a hook with `set_progress_hook`; with no hook
// installed this is one relaxed atomic load per epoch.

use std::sync::atomic::{AtomicUsize, Ordering};

/// Stage id passed by the optimiser epoch loops (UMAP, densMAP, t-SNE, PaCMAP, PHATE MDS).
pub const STAGE_OPTIMISE: u32 = 3;

static HOOK: AtomicUsize = AtomicUsize::new(0);

/// Install (or clear, with `None`) the progress hook.
pub fn set_progress_hook(hook: Option<fn(u32, usize, usize)>) {
    HOOK.store(hook.map_or(0, |f| f as usize), Ordering::Relaxed);
}

/// Report progress; forwarded to the hook when one is installed.
#[inline]
pub fn progress(stage: u32, done: usize, total: usize) {
    let h = HOOK.load(Ordering::Relaxed);
    if h != 0 {
        // SAFETY: only ever stores a valid `fn(u32, usize, usize)`.
        let f: fn(u32, usize, usize) = unsafe { std::mem::transmute(h) };
        f(stage, done, total);
    }
}
