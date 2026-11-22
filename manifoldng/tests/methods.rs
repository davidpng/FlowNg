//! Native tests: every method runs, is deterministic per seed, and the
//! clusterings recover well-separated synthetic populations.

use manifoldng::{method, run};

/// 4 well-separated Gaussian blobs in d dimensions, deterministic.
fn blobs(n: usize, d: usize) -> (Vec<f32>, Vec<usize>) {
    let mut s: u64 = 0x9E3779B97F4A7C15;
    let mut u = || {
        s ^= s << 13;
        s ^= s >> 7;
        s ^= s << 17;
        (s >> 11) as f64 / (1u64 << 53) as f64
    };
    let mut x = Vec::with_capacity(n * d);
    let mut lab = Vec::with_capacity(n);
    for i in 0..n {
        let k = i % 4;
        lab.push(k);
        for j in 0..d {
            let g = (-2.0 * (u() + 1e-12).ln()).sqrt() * (2.0 * std::f64::consts::PI * u()).cos();
            let c = if j % 4 == k { 8.0 } else { 0.0 };
            x.push((c + 0.5 * g) as f32);
        }
    }
    (x, lab)
}

fn ari(a: &[usize], b: &[f32]) -> f64 {
    use std::collections::HashMap;
    let c2 = |x: f64| x * (x - 1.0) / 2.0;
    let (mut ab, mut ca, mut cb) = (HashMap::new(), HashMap::new(), HashMap::new());
    for i in 0..a.len() {
        let bi = b[i] as i64;
        *ab.entry((a[i], bi)).or_insert(0f64) += 1.0;
        *ca.entry(a[i]).or_insert(0f64) += 1.0;
        *cb.entry(bi).or_insert(0f64) += 1.0;
    }
    let sij: f64 = ab.values().map(|&v| c2(v)).sum();
    let sa: f64 = ca.values().map(|&v| c2(v)).sum();
    let sb: f64 = cb.values().map(|&v| c2(v)).sum();
    let exp = sa * sb / c2(a.len() as f64);
    (sij - exp) / ((sa + sb) / 2.0 - exp)
}

#[test]
fn phenograph_recovers_blobs_and_is_deterministic() {
    let (x, lab) = blobs(2000, 8);
    let a = run(method::PHENOGRAPH, &x, 2000, 8, &[], 7).unwrap();
    let b = run(method::PHENOGRAPH, &x, 2000, 8, &[], 7).unwrap();
    assert_eq!(a, b);
    assert!(ari(&lab, &a) > 0.95, "ARI {}", ari(&lab, &a));
}

#[test]
fn flowsom_recovers_blobs_and_is_deterministic() {
    let (x, lab) = blobs(2000, 8);
    let prm = [5.0, 5.0, 10.0, 4.0];
    let a = run(method::FLOWSOM, &x, 2000, 8, &prm, 7).unwrap();
    let b = run(method::FLOWSOM, &x, 2000, 8, &prm, 7).unwrap();
    assert_eq!(a, b);
    assert!(ari(&lab, &a) > 0.95, "ARI {}", ari(&lab, &a));
    // Labels ordered by size: label 0 is the largest cluster.
    let count = |l: f32| a.iter().filter(|&&v| v == l).count();
    assert!(count(0.0) >= count(1.0) && count(1.0) >= count(2.0));
}

#[test]
fn embeddings_have_shape_and_are_finite() {
    let (x, _) = blobs(600, 8);
    for m in [method::UMAP, method::TSNE_BH, method::TSNE_FFT, method::PACMAP, method::DENSMAP] {
        let y = run(m, &x, 600, 8, &[], 3).unwrap();
        assert_eq!(y.len(), 1200, "method {m}");
        assert!(y.iter().all(|v| v.is_finite()), "method {m}");
    }
}

#[test]
fn rejects_bad_input() {
    assert!(run(method::UMAP, &[1.0, f32::NAN], 1, 2, &[], 0).is_err());
    assert!(run(method::UMAP, &[1.0, 2.0, 3.0], 2, 2, &[], 0).is_err());
    assert!(run(99, &[1.0, 2.0], 1, 2, &[], 0).is_err());
}
