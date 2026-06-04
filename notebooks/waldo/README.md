# Where's Waldo as a Weightless-Unlearning Benchmark

Reproducibility artifact for the paper **"Exact Machine Unlearning on Weightless
Neural Networks"** (ENIAC 2026). It contains a calibrated *synthetic* Where's-Waldo
visual-recognition benchmark and an evaluation harness that scores **machine
unlearning** (data deletion) on weightless neural networks (WiSARD) against
retrain-from-scratch, SISA, data-removal-enabled (DaRE) forests, and gradient
ascent, audited by a membership-inference attack.

## Modules

| File | Role |
|---|---|
| `synthetic.py` | Calibrated scene/character generator: palette, scale, and the difficulty axes (rotation, palette jitter, occlusion, photometric). |
| `characters.py` | Balanced six-class patch dataset (`waldo / odlaw / wenda / wizard / woof / background`) + difficulty presets. |
| `bench.py` | Recognition harness: thermometer/colormask encoders (in Python), model wrappers, a consistent memory metric. |
| `detector.py` | Sliding-window detector + encoder primitives (colormask, stripe). |
| `dare_real.py` | Bridge to the authors' DaRE-forest package (run under Python 3.12). |
| `make_paper_figures.py` | Regenerates the paper's figures into `../../articles/eniac-waldo/figures/`. |

## Notebooks (run each top to bottom, from this directory)

| Notebook | What it produces | Paper |
|---|---|---|
| `00_dataset.ipynb` | the benchmark: six classes, calibration to real pages, difficulty axes, non-triviality check | §3, Fig. 1 |
| `01_encoding_and_tuning.ipynb` | WiSARD encoding grid search (thermometer type/size × address size) | §4.1 |
| `02_batch_benchmark.ipynb` | tuned WiSARD vs tuned logistic regression / random forest on recognition | §4.1 |
| `03_machine_unlearning.ipynb` | **headline:** exact deletion vs gold / SISA / DaRE / gradient-ascent + membership-inference audit | §5, Fig. 2, Fig. 3, Table 1 |
| `04_rew_localizer.ipynb` | weightless sliding-window localizer vs tuned RF-window | §4.2 |

## Reproduce

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# run the headline experiment headless ...
jupyter nbconvert --to notebook --execute 03_machine_unlearning.ipynb \
  --output 03_machine_unlearning.ipynb --ExecutePreprocessor.timeout=1800
# ... or open any notebook in Jupyter and run all cells.

python make_paper_figures.py    # regenerates the paper figures
```

## Notes

- **No external dataset is needed.** All data is synthetic and generated from a seed.
  The palette/scale defaults are *calibrated* to the public Hey-Waldo set
  (Constantinou, 2017, `github.com/vc1492a/Hey-Waldo`), which is **not** redistributed
  here and is not required to reproduce any result.
- **Determinism.** The WiSARD bit-to-tuple mapping is not seeded, so recognition
  accuracy fluctuates ≈0.88–0.92 across runs; deletion cost and exactness are
  deterministic.
- **DaRE baseline.** The real DaRE forest in `03` uses the authors' `dare-rf`
  package through `dare_real.py`, which builds under Python 3.12 (see its header).
  The other baselines run with the pinned `requirements.txt` alone.
- **Character art.** The motivation montage in `00` references copyrighted character
  art (see `assets/characters/SOURCE.md`) that is **not** redistributed; that single
  display cell errors if the images are absent, but it has no effect on the benchmark
  or any reported result.
