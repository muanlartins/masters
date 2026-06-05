# TON_IoT WiSARD — Reproducibility Bundle

Reproducibility package for the technical report *"Reprodução do paper Alsaedi 2020
e avaliação da família WiSARD para detecção de anomalia em IoT (TON_IoT)"*.

This is the `toniot-wisard-repro` branch of the `masters` repo: it contains **only**
the files needed to reproduce the paper (other coursework on `main` is stripped here).

## Layout

| Path | What |
|------|------|
| `articles/toniot-wisard/` | The paper: LaTeX sources (`sections/`), `references.bib`, figures, `main.pdf`, `Makefile`. |
| `notebooks/toniot/` | All code: the deliverable notebook + sweep/benchmark scripts + results. |
| `notebooks/toniot/06_consolidado_grupos.ipynb` | **The deliverable notebook** — produces 21 of the 22 article figures and every result table. |
| `notebooks/toniot/04_figuras_apresentacao.ipynb` | Produces the 1 remaining article figure (`v06_cramers_v_por_base.png`, the per-base Cramér's V in §Dataset). |
| `notebooks/toniot/0{1,2,3,5}_*.ipynb` | Exploratory/context (EDA, reference impls, comparative + literature analysis). Not load-bearing for any reported figure or table. |
| `notebooks/toniot/run_*.py`, `*_utils.py`, `bench_cost.py` | Reproducible drivers (baselines, WiSARD-family grid, cost/memory benchmark). |
| `notebooks/toniot/results/_consolidado/` | The committed result artifacts (`baselines_paper.jsonl`, `bench_cost.json`, `grid/wisard_grid_*.jsonl`). The paper's numbers come straight from these — verifiable without re-running. |
| `notebooks/toniot/requirements.txt` | Pinned environment, incl. the `wisardpkg` fork commit. |

## Dependencies

`wisardpkg` lives in its own repo (<https://github.com/muanlartins/wisardpkg>); the
`requirements.txt` pins the exact commit (with the fitted thermometers, large-address
RAMs, and the `deployedSizeBytes` deployed-memory metric the paper's Pareto uses).

```bash
python3.13 -m venv venv && source venv/bin/activate
pip install --no-build-isolation -r notebooks/toniot/requirements.txt
```

## Data

The raw TON_IoT datasets are **not** committed (size + redistribution). Download the
public `Train_Test_IoT_dataset.zip` from the UNSW Canberra Cyber TON_IoT site and
extract the per-device `Train_Test_IoT_*.csv` files into `data/toniot/`. The committed
`results/_consolidado/` JSONL/JSON let you verify every reported number without the raw
data; the raw CSVs are only needed to re-run the pipeline end-to-end.

## Reproduce

```bash
cd notebooks/toniot
# 1) paper baselines (8 models, paper-faithful protocol)
python run_baselines_paper.py
# 2) WiSARD-family grid (30,020 configs; 7 bases in parallel, resumable)
for b in Fridge Garage_Door GPS_Tracker Modbus Motion_Light Thermostat Weather; do
  python run_wisard_grid.py --base "$b"; done
python run_wisard_grid.py --combined
# 3) cost/memory benchmark (single-fit harness, unified deployed metric)
python bench_cost.py
# 4) consolidate everything + regenerate figures/tables
jupyter nbconvert --to notebook --execute --inplace 06_consolidado_grupos.ipynb
# (and 04 for the Cramér's V figure)
# 5) build the paper
cd ../../articles/toniot-wisard && make
```

The article documents honestly where the public CSVs diverge from the dataset that
produced the paper's Tables 10–13, and reports results under the divergence rather
than claiming an exact match.
