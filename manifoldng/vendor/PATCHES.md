# Vendored crates and patches

These crates are copied unchanged from crates.io except for the patches below,
which make them build and run on `wasm32-unknown-unknown`. `Cargo.toml` points
at them with `[patch.crates-io]`. Licences are kept in each folder.

| Crate | Version | Licence | Why vendored |
|---|---|---|---|
| manifolds-rs | 0.10.1 | MIT | `std::time::Instant::now()` panics on wasm32 |
| ann-search-rs | 0.13.1 | MIT | same |
| atomic-wait | 1.1.0 | BSD-2-Clause | no wasm32 platform module (pulled in by faer → spindle) |

## manifolds-rs and ann-search-rs

- New file `src/wtime.rs`: on wasm32 an `Instant` stub whose `now()` and
  `elapsed()` return zero; elsewhere it re-exports `std::time::Instant`. The
  crates only use `Instant` to time progress messages, so results do not change.
- `pub mod wtime;` added to `src/lib.rs`.
- Every `use std::time::Instant;` (and the grouped forms in `manifolds-rs/src/lib.rs`,
  `ann-search-rs/src/cpu/hnsw.rs`, `ann-search-rs/src/cpu/nndescent.rs`) changed to
  `use crate::wtime::Instant;`.

- manifolds-rs only: a progress hook in `src/wtime.rs` (`set_progress_hook`,
  `progress(stage, done, total)`), called once per epoch at the top of each
  CPU optimiser loop (`training/umap_optimisers.rs` x3, `umap_optimiser_v06.rs`,
  `tsne_optimiser.rs` x2, `pacmap_optimiser.rs` x2, `mds_optimiser.rs`; each
  line is marked `// ManifoldNG patch`). With no hook installed it is one
  atomic load per epoch.

To re-apply on a newer version: copy the crate from `~/.cargo/registry/src/*/`,
then repeat these steps (`grep -rn "std::time" src` finds every timer site,
`grep -rn "ManifoldNG patch" src` every progress call).

## atomic-wait

- New file `src/fallback.rs`, selected in `src/lib.rs` for every target without
  a platform module. `wait` returns at once (the API allows spurious wake-ups),
  `wake_one`/`wake_all` do nothing. Correct for a single-threaded wasm module,
  where no other thread can be waiting.

## getrandom

Not vendored. `.cargo/config.toml` selects getrandom 0.3's `custom` backend for
wasm32, and `src/lib.rs` defines `__getrandom_v03_custom` to always fail. All
randomness in ManifoldNG is seeded, so OS entropy is never requested.
