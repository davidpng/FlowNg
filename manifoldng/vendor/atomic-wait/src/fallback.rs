// ManifoldNG patch: single-threaded fallback for targets without a futex
// (wasm32-unknown-unknown). `wait` may return spuriously by contract, so
// returning at once is correct; callers re-check the atomic in a loop.
use core::sync::atomic::AtomicU32;

#[inline]
pub fn wait(_atomic: &AtomicU32, _value: u32) {
    core::hint::spin_loop();
}

#[inline]
pub fn wake_one(_ptr: *const AtomicU32) {}

#[inline]
pub fn wake_all(_ptr: *const AtomicU32) {}
