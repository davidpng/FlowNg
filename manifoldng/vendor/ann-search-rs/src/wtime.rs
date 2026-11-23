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
