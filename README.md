# Run-Level Verifiability for Sensor Fusion

This is the anonymous review package for *Run-Level Verifiability for Sensor
Fusion: Cumulative Guarantees and Capture-Resilience Profiles*.

- `main.pdf` is the submitted manuscript.
- `artifact/README.md` contains the reproduction instructions.
- `artifact/results/` contains the committed measurements used by the paper.
- `sections/` and `tables/` support the prose-to-data consistency checks.
- `artifact/LICENSE` releases the artifact software under the MIT License.

For the fast offline checks, enter `artifact/` and run:

```sh
make verify
```

For full reproduction, including circuit compilation and proof generation,
follow `artifact/README.md`.
