## Section 4 Pareto re-analysis — headline numbers

### F4RM-WiSARD-cuckoo vs tabular ML baselines

| Baseline | Coverage (# datasets) | Strict dominate | Mixed (F4RM contributes) | Strictly dominated by baseline | Mean % envelope from F4RM |
|---|---:|---:|---:|---:|---:|
| DT | 21 | 11 | 10 | 0 | 74.1% |
| RF | 21 | 9 | 12 | 0 | 89.3% |
| XGBoost | 21 | 6 | 15 | 0 | 89.0% |
| LightGBM | 21 | 6 | 15 | 0 | 83.6% |
| CatBoost | 21 | 3 | 18 | 0 | 90.3% |
| MLP | 21 | 14 | 7 | 0 | 90.5% |
| FT-Transformer | 21 | 18 | 3 | 0 | 98.5% |

### F4RM-WiSARD-cuckoo vs prior weightless

| Baseline | Coverage (# datasets) | Strict dominate | Mixed (F4RM contributes) | Strictly dominated by baseline | Mean % envelope from F4RM |
|---|---:|---:|---:|---:|---:|
| BTHOWeN | 21 | 1 | 20 | 0 | 72.1% |
| DWN | 21 | 12 | 9 | 0 | 96.4% |
| ULEEN | 21 | 4 | 17 | 0 | 77.5% |

### F4RMS vs tabular ML baselines

| Baseline | Coverage (# datasets) | Strict dominate | Mixed (F4RM contributes) | Strictly dominated by baseline | Mean % envelope from F4RM |
|---|---:|---:|---:|---:|---:|
| DT | 21 | 0 | 17 | 4 | 13.4% |
| RF | 21 | 6 | 13 | 2 | 58.5% |
| XGBoost | 21 | 6 | 13 | 2 | 66.9% |
| LightGBM | 21 | 6 | 12 | 3 | 57.7% |
| CatBoost | 21 | 2 | 16 | 3 | 60.6% |
| MLP | 21 | 0 | 18 | 3 | 41.9% |
| FT-Transformer | 21 | 12 | 8 | 1 | 83.8% |

### F4RMS vs prior weightless

| Baseline | Coverage (# datasets) | Strict dominate | Mixed (F4RM contributes) | Strictly dominated by baseline | Mean % envelope from F4RM |
|---|---:|---:|---:|---:|---:|
| BTHOWeN | 21 | 0 | 20 | 1 | 43.5% |
| DWN | 21 | 4 | 15 | 2 | 66.4% |
| ULEEN | 21 | 0 | 17 | 4 | 37.2% |

---

### Best-operating-point summary (focus pairs)

**F4RM-WiSARD-cuckoo vs DT:**

| Criterion | n_comparable | F4RM wins | Baseline wins | Ties |
|---|---:|---:|---:|---:|
| best_acc | 21 | 16 | 4 | 1 |
| best_mem_at_iso_acc | 21 | 16 | 5 | 0 |
| best_acc_per_log_mem | 21 | 18 | 2 | 1 |
| best_acc_at_small_budget | 20 | 12 | 7 | 1 |
| best_acc_at_medium_budget | 21 | 16 | 4 | 1 |

**F4RM-WiSARD-cuckoo vs XGBoost:**

| Criterion | n_comparable | F4RM wins | Baseline wins | Ties |
|---|---:|---:|---:|---:|
| best_acc | 21 | 6 | 15 | 0 |
| best_mem_at_iso_acc | 21 | 19 | 2 | 0 |
| best_acc_per_log_mem | 21 | 21 | 0 | 0 |
| best_acc_at_small_budget | 0 | 0 | 0 | 0 |
| best_acc_at_medium_budget | 4 | 2 | 2 | 0 |

**F4RM-WiSARD-cuckoo vs BTHOWeN:**

| Criterion | n_comparable | F4RM wins | Baseline wins | Ties |
|---|---:|---:|---:|---:|
| best_acc | 21 | 20 | 1 | 0 |
| best_mem_at_iso_acc | 21 | 13 | 5 | 3 |
| best_acc_per_log_mem | 21 | 6 | 15 | 0 |
| best_acc_at_small_budget | 21 | 17 | 3 | 1 |
| best_acc_at_medium_budget | 21 | 20 | 1 | 0 |

**F4RM-WiSARD-cuckoo vs DWN:**

| Criterion | n_comparable | F4RM wins | Baseline wins | Ties |
|---|---:|---:|---:|---:|
| best_acc | 21 | 18 | 3 | 0 |
| best_mem_at_iso_acc | 21 | 17 | 4 | 0 |
| best_acc_per_log_mem | 21 | 19 | 1 | 1 |
| best_acc_at_small_budget | 21 | 18 | 3 | 0 |
| best_acc_at_medium_budget | 21 | 15 | 4 | 2 |

---

### Memory-band wins (focus pairs)

**F4RM-WiSARD-cuckoo vs DT:**

| Band | n_both | F4RM wins | Baseline wins | Ties |
|---|---:|---:|---:|---:|
| <1KB | 0 | 0 | 0 | 0 |
| 1-10KB | 20 | 12 | 7 | 1 |
| 10-100KB | 13 | 12 | 1 | 0 |
| 100KB-1MB | 3 | 3 | 0 | 0 |
| >1MB | 0 | 0 | 0 | 0 |

**F4RM-WiSARD-cuckoo vs XGBoost:**

| Band | n_both | F4RM wins | Baseline wins | Ties |
|---|---:|---:|---:|---:|
| <1KB | 0 | 0 | 0 | 0 |
| 1-10KB | 0 | 0 | 0 | 0 |
| 10-100KB | 4 | 2 | 2 | 0 |
| 100KB-1MB | 6 | 1 | 5 | 0 |
| >1MB | 1 | 0 | 1 | 0 |

**F4RM-WiSARD-cuckoo vs BTHOWeN:**

| Band | n_both | F4RM wins | Baseline wins | Ties |
|---|---:|---:|---:|---:|
| <1KB | 20 | 7 | 12 | 1 |
| 1-10KB | 21 | 17 | 3 | 1 |
| 10-100KB | 14 | 14 | 0 | 0 |
| 100KB-1MB | 1 | 1 | 0 | 0 |
| >1MB | 0 | 0 | 0 | 0 |

**F4RM-WiSARD-cuckoo vs DWN:**

| Band | n_both | F4RM wins | Baseline wins | Ties |
|---|---:|---:|---:|---:|
| <1KB | 0 | 0 | 0 | 0 |
| 1-10KB | 21 | 18 | 3 | 0 |
| 10-100KB | 18 | 12 | 4 | 2 |
| 100KB-1MB | 0 | 0 | 0 | 0 |
| >1MB | 0 | 0 | 0 | 0 |

---

**Notes:**

- `n_partial_dominates` columns in the summary CSV are 0 by design: the spec's definition of `partial_dominates` is subsumed by `mixed` once `strict_dominates` is taken to mean *F is the only contributor to the joint envelope*. We preserve the column for schema-compatibility.
- `mean_pct_envelope_from_f4rm` is averaged only over datasets where both systems had ≥1 frontier point.
- Memory-band ties use a 0.1pp accuracy band; head-to-head memory ties use a 0.95–1.05 ratio band per the spec.