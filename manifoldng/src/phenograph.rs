//! PhenoGraph (Levine et al. 2015, Cell): kNN graph, Jaccard-weighted shared
//! nearest neighbour graph, then Louvain community detection.
//!
//! Parameters: [k=30, resolution=1.0, min_cluster_size=10, max_levels=20].
//! Labels are renumbered by cluster size (0 = largest). Clusters smaller than
//! `min_cluster_size` get label -1 ("unassigned"), as in the reference
//! implementation's `min_cluster_size`.

use manifolds_rs::prelude::*;
use rand::rngs::StdRng;
use rand::seq::SliceRandom;
use rand::SeedableRng;

use crate::p;

/// Undirected weighted graph in CSR form. Each edge appears in both rows.
/// Self-loops (from aggregation) appear once, in `self_w`.
pub struct Graph {
    pub offsets: Vec<usize>,
    pub targets: Vec<u32>,
    pub weights: Vec<f64>,
    pub self_w: Vec<f64>,
}

impl Graph {
    fn n(&self) -> usize {
        self.self_w.len()
    }
}

/// kNN indices (excluding self) for every event.
pub fn knn(data: &[f32], n: usize, d: usize, k: usize, seed: u64) -> Result<Vec<Vec<usize>>, String> {
    let mat = faer::MatRef::from_row_major_slice(data, n, d);
    let nn = NearestNeighbourParams::<f32>::default();
    let (idx, _dist) = run_ann_search(mat, k, "nndescent".to_string(), &nn, seed as usize, 0).map_err(|e| e.to_string())?;
    Ok(idx)
}

/// Jaccard SNN graph: w(i,j) = |N(i) ∩ N(j)| / |N(i) ∪ N(j)| for every kNN edge,
/// symmetrised by keeping each unordered pair once.
pub fn jaccard_graph(nbrs: &[Vec<usize>]) -> Graph {
    let n = nbrs.len();
    // Sorted neighbour lists for merge intersection.
    let sorted: Vec<Vec<u32>> = nbrs
        .iter()
        .map(|v| {
            let mut s: Vec<u32> = v.iter().map(|&x| x as u32).collect();
            s.sort_unstable();
            s.dedup();
            s
        })
        .collect();
    let mut edges: Vec<(u32, u32, f64)> = Vec::with_capacity(n * nbrs.first().map_or(0, |v| v.len()));
    for i in 0..n {
        for &j in &sorted[i] {
            let (a, b) = if (i as u32) < j { (i as u32, j) } else { (j, i as u32) };
            if a == b {
                continue;
            }
            let (sa, sb) = (&sorted[a as usize], &sorted[b as usize]);
            let (mut x, mut y, mut inter) = (0, 0, 0usize);
            while x < sa.len() && y < sb.len() {
                match sa[x].cmp(&sb[y]) {
                    std::cmp::Ordering::Less => x += 1,
                    std::cmp::Ordering::Greater => y += 1,
                    std::cmp::Ordering::Equal => {
                        inter += 1;
                        x += 1;
                        y += 1;
                    }
                }
            }
            let union = sa.len() + sb.len() - inter;
            if inter > 0 && union > 0 {
                edges.push((a, b, inter as f64 / union as f64));
            }
        }
    }
    edges.sort_unstable_by(|p, q| (p.0, p.1).cmp(&(q.0, q.1)));
    edges.dedup_by(|p, q| p.0 == q.0 && p.1 == q.1);
    from_edges(n, &edges, vec![0.0; n])
}

fn from_edges(n: usize, edges: &[(u32, u32, f64)], self_w: Vec<f64>) -> Graph {
    let mut deg = vec![0usize; n + 1];
    for &(a, b, _) in edges {
        deg[a as usize + 1] += 1;
        deg[b as usize + 1] += 1;
    }
    for i in 0..n {
        deg[i + 1] += deg[i];
    }
    let offsets = deg.clone();
    let mut fill = deg;
    let mut targets = vec![0u32; offsets[n]];
    let mut weights = vec![0f64; offsets[n]];
    for &(a, b, w) in edges {
        let (a, b) = (a as usize, b as usize);
        targets[fill[a]] = b as u32;
        weights[fill[a]] = w;
        fill[a] += 1;
        targets[fill[b]] = a as u32;
        weights[fill[b]] = w;
        fill[b] += 1;
    }
    Graph { offsets, targets, weights, self_w }
}

/// One level of Louvain local moving. Returns the community of each node and
/// whether any node moved.
fn local_moving(g: &Graph, resolution: f64, rng: &mut StdRng) -> (Vec<usize>, bool) {
    let n = g.n();
    // k_i = weighted degree (self-loop counted twice, as in modularity).
    let k: Vec<f64> = (0..n)
        .map(|i| g.weights[g.offsets[i]..g.offsets[i + 1]].iter().sum::<f64>() + 2.0 * g.self_w[i])
        .collect();
    let m2: f64 = k.iter().sum();
    if m2 <= 0.0 {
        return ((0..n).collect(), false);
    }
    let mut comm: Vec<usize> = (0..n).collect();
    let mut tot: Vec<f64> = k.clone();
    let mut order: Vec<usize> = (0..n).collect();
    order.shuffle(rng);

    let mut w_to = vec![0f64; n];
    let mut touched: Vec<usize> = Vec::new();
    let mut moved_any = false;
    loop {
        let mut moved = 0usize;
        for &i in &order {
            let ci = comm[i];
            touched.clear();
            for e in g.offsets[i]..g.offsets[i + 1] {
                let c = comm[g.targets[e] as usize];
                if w_to[c] == 0.0 {
                    touched.push(c);
                }
                w_to[c] += g.weights[e];
            }
            tot[ci] -= k[i];
            let own = w_to[ci];
            let mut best = ci;
            let mut best_gain = own - resolution * tot[ci] * k[i] / m2;
            for &c in &touched {
                let gain = w_to[c] - resolution * tot[c] * k[i] / m2;
                if gain > best_gain + 1e-12 {
                    best_gain = gain;
                    best = c;
                }
            }
            tot[best] += k[i];
            if best != ci {
                comm[i] = best;
                moved += 1;
            }
            for &c in &touched {
                w_to[c] = 0.0;
            }
        }
        if moved == 0 {
            break;
        }
        moved_any = true;
    }
    (comm, moved_any)
}

/// Collapse communities into nodes. Returns the new graph and the renumbered
/// community of each old node.
fn aggregate(g: &Graph, comm: &[usize]) -> (Graph, Vec<usize>) {
    let n = g.n();
    let mut map = vec![usize::MAX; n];
    let mut nc = 0;
    let mut renum = vec![0usize; n];
    for i in 0..n {
        let c = comm[i];
        if map[c] == usize::MAX {
            map[c] = nc;
            nc += 1;
        }
        renum[i] = map[c];
    }
    let mut self_w = vec![0f64; nc];
    let mut edges: Vec<(u32, u32, f64)> = Vec::new();
    for i in 0..n {
        let ci = renum[i];
        self_w[ci] += g.self_w[i];
        for e in g.offsets[i]..g.offsets[i + 1] {
            let j = g.targets[e] as usize;
            if j < i {
                continue; // each undirected edge once
            }
            let cj = renum[j];
            let w = g.weights[e];
            if ci == cj {
                self_w[ci] += w;
            } else {
                let (a, b) = if ci < cj { (ci, cj) } else { (cj, ci) };
                edges.push((a as u32, b as u32, w));
            }
        }
    }
    edges.sort_unstable_by(|p, q| (p.0, p.1).cmp(&(q.0, q.1)));
    let mut merged: Vec<(u32, u32, f64)> = Vec::with_capacity(edges.len());
    for e in edges {
        match merged.last_mut() {
            Some(last) if last.0 == e.0 && last.1 == e.1 => last.2 += e.2,
            _ => merged.push(e),
        }
    }
    (from_edges(nc, &merged, self_w), renum)
}

/// Multi-level Louvain. Returns a community id per node (not yet size-ordered).
pub fn louvain(g: Graph, resolution: f64, max_levels: usize, seed: u64) -> Vec<usize> {
    let mut rng = StdRng::seed_from_u64(seed);
    let mut labels: Vec<usize> = (0..g.n()).collect();
    let mut g = g;
    for level in 0..max_levels {
        crate::progress::send_level(level, max_levels);
        let (comm, moved) = local_moving(&g, resolution, &mut rng);
        if !moved {
            break;
        }
        let (ng, renum) = aggregate(&g, &comm);
        for l in labels.iter_mut() {
            *l = renum[*l];
        }
        if ng.n() == g.n() {
            break;
        }
        g = ng;
    }
    labels
}

/// Renumber by size (0 = largest); clusters below `min_size` become -1.
pub fn order_by_size(labels: &[usize], min_size: usize) -> Vec<i32> {
    let nc = labels.iter().copied().max().map_or(0, |m| m + 1);
    let mut size = vec![0usize; nc];
    for &l in labels {
        size[l] += 1;
    }
    let mut ids: Vec<usize> = (0..nc).collect();
    ids.sort_by(|&a, &b| size[b].cmp(&size[a]).then(a.cmp(&b)));
    let mut rank = vec![-1i32; nc];
    let mut next = 0;
    for &c in &ids {
        if size[c] >= min_size.max(1) {
            rank[c] = next;
            next += 1;
        }
    }
    labels.iter().map(|&l| rank[l]).collect()
}

pub fn phenograph(data: &[f32], n: usize, d: usize, params: &[f64], seed: u64) -> Result<Vec<i32>, String> {
    let k = (p(params, 0, 30.0) as usize).clamp(2, n.saturating_sub(1).max(2));
    let resolution = p(params, 1, 1.0);
    let min_size = p(params, 2, 10.0) as usize;
    let max_levels = p(params, 3, 20.0) as usize;
    if n < 3 {
        return Ok(vec![0; n]);
    }
    crate::progress::begin(crate::progress::NEIGHBOURS);
    let nbrs = knn(data, n, d, k, seed)?;
    crate::progress::begin(crate::progress::GRAPH);
    let g = jaccard_graph(&nbrs);
    drop(nbrs);
    let labels = louvain(g, resolution, max_levels, seed);
    Ok(order_by_size(&labels, min_size))
}
