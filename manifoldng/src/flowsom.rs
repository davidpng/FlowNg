//! FlowSOM (Van Gassen et al. 2015, Cytometry A): a self-organising map of
//! xdim x ydim codes trained on the events, then consensus hierarchical
//! metaclustering of the codes (ConsensusClusterPlus-style: average linkage,
//! Euclidean, 90% resampling), and each event takes its code's metacluster.
//!
//! Parameters: [xdim=10, ydim=10, rlen=10, n_meta=10, alpha_start=0.05,
//! alpha_end=0.01, consensus_reps=100].
//! Labels are renumbered by metacluster size (0 = largest).

use rand::rngs::StdRng;
use rand::seq::index::sample;
use rand::{Rng, SeedableRng};

use crate::p;

#[inline]
fn dist2(a: &[f32], b: &[f32]) -> f32 {
    let mut s = 0f32;
    for i in 0..a.len() {
        let t = a[i] - b[i];
        s += t * t;
    }
    s
}

fn nearest(codes: &[f32], d: usize, x: &[f32]) -> usize {
    let mut best = 0;
    let mut bd = f32::INFINITY;
    for (c, code) in codes.chunks_exact(d).enumerate() {
        let dd = dist2(code, x);
        if dd < bd {
            bd = dd;
            best = c;
        }
    }
    best
}

/// Train the SOM. Mirrors FlowSOM's `SOM()` online algorithm: rlen * n updates
/// at random events, learning rate falling linearly alpha_start..alpha_end,
/// neighbourhood radius (Chebyshev grid distance, as FlowSOM's "maximum")
/// falling linearly from the 0.67 quantile of grid distances to 0.
pub fn train_som(data: &[f32], n: usize, d: usize, xdim: usize, ydim: usize, rlen: usize, alpha: (f32, f32), rng: &mut StdRng) -> Vec<f32> {
    let nc = xdim * ydim;
    let grid: Vec<(i32, i32)> = (0..nc).map(|c| ((c % xdim) as i32, (c / xdim) as i32)).collect();
    // Initial codes: random distinct events (FlowSOM's default "sample" init).
    let mut codes = vec![0f32; nc * d];
    let picks = sample(rng, n, nc.min(n));
    for (c, e) in picks.iter().enumerate() {
        codes[c * d..(c + 1) * d].copy_from_slice(&data[e * d..(e + 1) * d]);
    }
    for c in picks.len()..nc {
        let e = rng.random_range(0..n);
        codes[c * d..(c + 1) * d].copy_from_slice(&data[e * d..(e + 1) * d]);
    }
    let mut gd: Vec<f32> = Vec::with_capacity(nc * nc);
    for a in &grid {
        for b in &grid {
            gd.push(((a.0 - b.0).abs().max((a.1 - b.1).abs())) as f32);
        }
    }
    let mut sorted = gd.clone();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let r0 = sorted[((sorted.len() - 1) as f32 * 0.67) as usize].max(1.0);

    let total = (rlen * n).max(1);
    for step in 0..total {
        crate::progress::report(crate::progress::OPTIMISE, step, total);
        let frac = step as f32 / total as f32;
        let a = alpha.0 - (alpha.0 - alpha.1) * frac;
        let r = r0 * (1.0 - frac);
        let e = rng.random_range(0..n);
        let x = &data[e * d..(e + 1) * d];
        let w = nearest(&codes, d, x);
        for c in 0..nc {
            if gd[w * nc + c] <= r {
                let code = &mut codes[c * d..(c + 1) * d];
                for j in 0..d {
                    code[j] += a * (x[j] - code[j]);
                }
            }
        }
    }
    codes
}

/// Average-linkage agglomerative clustering on a dense distance matrix, cut
/// to `k` clusters. O(m^3) but m is the number of SOM codes (~100).
pub fn hclust_average(dist: &[f64], m: usize, k: usize) -> Vec<usize> {
    let mut members: Vec<Vec<usize>> = (0..m).map(|i| vec![i]).collect();
    let mut active: Vec<bool> = vec![true; m];
    let mut dm = dist.to_vec();
    let mut alive = m;
    while alive > k.max(1) {
        let (mut bi, mut bj, mut bd) = (0, 0, f64::INFINITY);
        for i in 0..m {
            if !active[i] {
                continue;
            }
            for j in (i + 1)..m {
                if active[j] && dm[i * m + j] < bd {
                    bd = dm[i * m + j];
                    bi = i;
                    bj = j;
                }
            }
        }
        let (si, sj) = (members[bi].len() as f64, members[bj].len() as f64);
        for t in 0..m {
            if active[t] && t != bi && t != bj {
                let v = (dm[bi * m + t] * si + dm[bj * m + t] * sj) / (si + sj);
                dm[bi * m + t] = v;
                dm[t * m + bi] = v;
            }
        }
        let moved = std::mem::take(&mut members[bj]);
        members[bi].extend(moved);
        active[bj] = false;
        alive -= 1;
    }
    let mut lab = vec![0usize; m];
    let mut next = 0;
    for i in 0..m {
        if active[i] {
            for &x in &members[i] {
                lab[x] = next;
            }
            next += 1;
        }
    }
    lab
}

/// Consensus metaclustering of SOM codes.
pub fn consensus_meta(codes: &[f32], m: usize, d: usize, k: usize, reps: usize, rng: &mut StdRng) -> Vec<usize> {
    let k = k.clamp(1, m);
    let mut full = vec![0f64; m * m];
    for i in 0..m {
        for j in 0..m {
            full[i * m + j] = (dist2(&codes[i * d..(i + 1) * d], &codes[j * d..(j + 1) * d]) as f64).sqrt();
        }
    }
    if reps == 0 || m <= k {
        return hclust_average(&full, m, k);
    }
    let mut together = vec![0f64; m * m];
    let mut both = vec![0f64; m * m];
    let take = ((m as f64) * 0.9).round().max(k as f64) as usize;
    for _ in 0..reps {
        let mut idx: Vec<usize> = sample(rng, m, take.min(m)).into_vec();
        idx.sort_unstable();
        let s = idx.len();
        let mut sub = vec![0f64; s * s];
        for a in 0..s {
            for b in 0..s {
                sub[a * s + b] = full[idx[a] * m + idx[b]];
            }
        }
        let lab = hclust_average(&sub, s, k);
        for a in 0..s {
            for b in 0..s {
                both[idx[a] * m + idx[b]] += 1.0;
                if lab[a] == lab[b] {
                    together[idx[a] * m + idx[b]] += 1.0;
                }
            }
        }
    }
    let cons: Vec<f64> = (0..m * m)
        .map(|t| if both[t] > 0.0 { 1.0 - together[t] / both[t] } else { 1.0 })
        .collect();
    hclust_average(&cons, m, k)
}

pub fn flowsom(data: &[f32], n: usize, d: usize, params: &[f64], seed: u64) -> Result<Vec<i32>, String> {
    let xdim = (p(params, 0, 10.0) as usize).max(1);
    let ydim = (p(params, 1, 10.0) as usize).max(1);
    let rlen = (p(params, 2, 10.0) as usize).max(1);
    let k = (p(params, 3, 10.0) as usize).max(1);
    let alpha = (p(params, 4, 0.05) as f32, p(params, 5, 0.01) as f32);
    let reps = p(params, 6, 100.0) as usize;
    let mut rng = StdRng::seed_from_u64(seed);
    let codes = train_som(data, n, d, xdim, ydim, rlen, alpha, &mut rng);
    let m = xdim * ydim;
    crate::progress::begin(crate::progress::CLUSTER);
    let meta = consensus_meta(&codes, m, d, k, reps, &mut rng);
    crate::progress::begin(crate::progress::ASSIGN);
    let labels: Vec<usize> = data.chunks_exact(d).map(|x| meta[nearest(&codes, d, x)]).collect();
    Ok(crate::phenograph::order_by_size(&labels, 1))
}
