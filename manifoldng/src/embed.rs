//! Thin wrappers over manifolds-rs. Each takes a row-major `n x d` matrix and a
//! positional f64 parameter vector (NaN or missing = default) and returns
//! `n * 2` row-major coordinates.
//!
//! Parameter order (FlowNG.html builds the same vectors):
//! - UMAP:      [k=15, min_dist=0.1, spread=1.0, n_epochs=0 (crate default)]
//! - t-SNE:     [perplexity=30, n_epochs=0 (crate default), theta=0.5]
//! - PaCMAP:    [n_near=10]
//! - PHATE:     [k=5, n_landmarks=2000]
//! - densMAP:   [k=15, min_dist=0.1, lambda=2.0]
//! - DiffMaps:  [k=15, n_landmarks=2000]

use manifolds_rs::*;

use crate::p;

const SILENT: usize = 0;

fn to_rows(cols: Vec<Vec<f32>>, n: usize) -> Result<Vec<f32>, String> {
    if cols.len() < 2 || cols.iter().any(|c| c.len() != n) {
        return Err(format!("unexpected embedding shape: {} columns", cols.len()));
    }
    let mut out = vec![0f32; n * 2];
    for i in 0..n {
        out[2 * i] = cols[0][i];
        out[2 * i + 1] = cols[1][i];
    }
    Ok(out)
}

fn opt_usize(params: &[f64], i: usize) -> Option<usize> {
    let v = p(params, i, 0.0);
    if v >= 1.0 { Some(v as usize) } else { None }
}

pub fn umap(data: &[f32], n: usize, d: usize, params: &[f64], seed: u64) -> Result<Vec<f32>, String> {
    let k = p(params, 0, 15.0) as usize;
    let min_dist = p(params, 1, 0.1) as f32;
    let spread = p(params, 2, 1.0) as f32;
    let mut prm = UmapParams::<f32>::new_default_2d(Some(min_dist), Some(spread));
    prm.k = k;
    if let Some(e) = opt_usize(params, 3) {
        prm.optim_params.n_epochs = e;
    }
    let cols = manifolds_rs::umap((data, n, d), None, &prm, seed as usize, SILENT).map_err(|e| e.to_string())?;
    to_rows(cols, n)
}

pub fn tsne(data: &[f32], n: usize, d: usize, params: &[f64], seed: u64, approx: &str) -> Result<Vec<f32>, String> {
    let perplexity = p(params, 0, 30.0) as f32;
    let mut prm = TsneParams::<f32>::new_default_2d(Some(perplexity));
    if let Some(e) = opt_usize(params, 1) {
        prm.optim_params.n_epochs = e;
    }
    prm.optim_params.theta = p(params, 2, prm.optim_params.theta as f64) as f32;
    let cols = manifolds_rs::tsne((data, n, d), None, &prm, approx, seed as usize, SILENT).map_err(|e| e.to_string())?;
    to_rows(cols, n)
}

pub fn pacmap(data: &[f32], n: usize, d: usize, params: &[f64], seed: u64) -> Result<Vec<f32>, String> {
    let n_near = p(params, 0, 10.0) as usize;
    let prm = PacmapParams::<f32>::new_default_2d(Some(n_near));
    let cols = manifolds_rs::pacmap((data, n, d), None, &prm, seed as usize, SILENT).map_err(|e| e.to_string())?;
    to_rows(cols, n)
}

pub fn phate(data: &[f32], n: usize, d: usize, params: &[f64], seed: u64) -> Result<Vec<f32>, String> {
    let k = p(params, 0, 5.0) as usize;
    let mut prm = PhateParams::<f32>::new_default_2d(Some(k));
    prm.diffusion_params.n_landmarks = Some(p(params, 1, 2000.0) as usize);
    let cols = manifolds_rs::phate((data, n, d), None, prm, seed as usize, SILENT).map_err(|e| e.to_string())?;
    to_rows(cols, n)
}

pub fn densmap(data: &[f32], n: usize, d: usize, params: &[f64], seed: u64) -> Result<Vec<f32>, String> {
    let min_dist = p(params, 1, 0.1) as f32;
    let lambda = p(params, 2, 2.0) as f32;
    let mut prm = DensmapParams::<f32>::new_default_2d(Some(min_dist), None, Some(lambda));
    prm.umap_params.k = p(params, 0, 15.0) as usize;
    let cols = manifolds_rs::densmap((data, n, d), None, &prm, seed as usize, SILENT).map_err(|e| e.to_string())?;
    to_rows(cols, n)
}

pub fn diffusion_maps(data: &[f32], n: usize, d: usize, params: &[f64], seed: u64) -> Result<Vec<f32>, String> {
    let mut prm = DiffusionMapsParams::<f32>::default();
    prm.k = p(params, 0, 15.0) as usize;
    prm.n_landmarks = Some(p(params, 1, 2000.0) as usize);
    let cols = manifolds_rs::diffusion_maps((data, n, d), None, prm, seed as usize, SILENT).map_err(|e| e.to_string())?;
    to_rows(cols, n)
}
