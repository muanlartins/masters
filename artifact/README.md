# Run-level verifiability for sensor fusion: executable artifact

This artifact reproduces Section 5 of the paper. It is an executable protocol
model and microbenchmark suite, not deployable security software. In particular,
fixture private keys are deterministically derived so that runs are
reproducible; anyone with the source can derive them. Their public keys are
nevertheless enrolled in the versioned policy roster, and judges use only the
exact enrolled bytes. The separating traces exercise judge logic and accounting
boundaries, not the assumed security of the underlying primitives.

## What is implemented

Nine **complete stacks** carry evidence for every cumulative conjunct through
the level they claim. A tenth row is deliberately partial: its 16-byte
homomorphic MAC authenticates a linear aggregate but does not preserve
anchored manifest integrity and per-record attribution, so it is not labeled
V4.

| Stack | Claim | Mechanism |
|---|---|---|
| `v0-none` | V0 | no evidence |
| `v1-merkle` | V1 | externally anchored RFC 6962 Merkle root |
| `v1-chain` | V1 | externally anchored hash chain |
| `v2-ed25519` | V2 | per-record Ed25519 signatures |
| `v2-bls` | V2 | BLS12-381 aggregate signature |
| `v3-manifest` | V3 | exact policy check on the full manifest |
| `v3-policy-sample` | V3, probabilistic | verifier-chosen policy positions and Merkle openings |
| `v4-raw` | V4 | ship authenticated observations and recompute `F` |
| `v4-attested` | V4 under modeled `rho_iso` | manifest root, external anchor, and attested report |
| `partial-homomac` | partial, not a V-level | aggregate-only linearly homomorphic MAC |

The sampled stack anchors its root before receiving a 32-byte unpredictable
verifier challenge. The challenge is verifier-held judge state and is not read
from the producer's proof object. The judge rejects missing, reordered, or
substituted openings and checks each opened identifier against the policy
position. A short manifest is rejected deterministically. If an omitted record
is replaced by an authentic duplicate so that the length remains correct, one
defective position is detected with probability exactly `k/n`. Hash draws use
32-bit rejection sampling, so the position distribution has no modulo bias.

Every G1 anchor signs the policy digest, a 16-byte unique run ID, a fresh
32-byte auditor-held state, and the manifest root. The trusted anchor service
must issue fresh state and unique run IDs; the auditor records the anchor
receipt before accepting the output. Judges require the independently held
state, so the signature alone is not treated as a timestamp. Deterministic
fixture values exercise this boundary without claiming a deployed service.

Five circuits in `circuits/fusion.circom` are compiled with circom and proved
with Groth16 over BN254: input binding, arithmetic mean, excursion count, mean
kinetic temperature (MKT), and mean with EdDSA attribution inside the circuit.
The MKT circuit constrains its declared 0--35 degrees Celsius band at scale
`2^16` and uniquely pins the fixed-point logarithm witness. Integer divisions
and the logarithm round down with constrained remainders. The policy's degree-12
fixed-point approximation differs from the floating-point formula by 1.8 mK on
the reported trace.

Four separating traces live in `vfusion/attacks.py`. Additional proof-object
mutations in `scripts/audit_tests.py` check cases that prose-to-number matching
cannot catch, including an empty sampled opening set and uncharged attestation
fields.

## Accounting rules

Two definitions make the online numbers comparable.

- **`B_ev`** is the complete bidirectional online verification transcript beyond the
  pre-provisioned policy `P` and claimed output `y`. Device and proof
  verification keys reside in `P`; commitments, signatures, challenges,
  openings, observations, and proofs are charged. If setup material is not
  pre-provisioned, report `B_total(R) = B_ev + B_P/R` over `R` runs.
- **`M_P` and `M_J`** are protocol bytes retained between record arrivals under
  the stated streaming schedule. They are algorithmic buffering coordinates,
  not process RSS and not library working memory. A signature emitted with its
  record adds no retained state; a Merkle frontier does.

The policy canonically serializes its parameters, roster version, per-device
Ed25519 and BLS keys, and anchor/attestation service keys; `Policy.digest()`
binds that serialization. Adversarial tests replace an enrolled key and
substitute a roster after anchoring.

Primitive counts and byte counts are exact for the declared implementation and
serialization. The attestation row is a cost model: it assumes an isolated
acquisition path that admits enrolled inputs, enforces the policy, and protects
the attestation key. Its 208-byte transcript charges a manifest root, 48-byte
run context, a separate external root anchor, and the attestation report. No secure element or
physical-attack evaluation is present.
Prover RSS in the circuit table is measured separately as the median of three
process runs.

## Reproducing

From a clean extraction:

```sh
cd artifact
make deps
make all CIRCOM=/path/to/circom
```

`circom` is not distributed on npm. Install version 2.2.3 from the official
iden3 releases and pass its path if needed. `make deps` uses `npm ci`; the two
direct Python dependencies are pinned in `requirements.txt`. `make all`
generates the previously gitignored circuit entry points, runs all experiments,
regenerates `../tables/*.tex`, and checks the prose.

The proof run downloads about 260 MB of powers of tau. The attributed circuit
at `n=60` has 549,392 constraints and exceeds the setup included here, so its
count comes from compilation and no proving figure is reported. Individual
stages are `make stacks`, `make sampling`, `make circuits`, `make snark`,
`make tables`, and `make verify`. The last command is offline and fast: it runs
the adversarial proof-object checks and validates every numeric prose claim
against the committed JSON.

## Cross-checks

- Python/circomlibjs Poseidon binding equals the public `cM` signal produced by
  every circuit.
- Circuit operator outputs match the Python references on the fixed trace: the
  excursion count is 12, and MKT is 280.97 K versus 280.97183 K in floating
  point.
- The MKT witness satisfies both remainder inequalities that make its
  fixed-point logarithm unique; the circuit rejects values outside 0--35 C.
- The RFC 6962 implementation agrees between recursive and streaming forms for
  every index at `n` in `{1,2,3,5,7,60,64,1000}`, and forged leaves fail.

## Determinism and measured state

Protocol traces use `trace.DEFAULT_SEED = 20260904`. Challenge trials enumerate
2,000 fixed 32-byte values and report Wilson 95% intervals. Groth16 proofs are
randomized, so snarkjs proof JSON varies by a few bytes; structural proof size
remains 128 bytes. For the attributed `n=12` statement, snarkjs proof and public
JSON total 983 bytes, while normalized compressed binary is 128 proof bytes plus
96 public bytes. Its verification key is 3,290 bytes as JSON or 352 bytes
normalized. Prover
RSS and wall time vary by host, which is why the JSON records the measurement
environment and all three RSS samples.

`build/` and `node_modules/` are generated and intentionally excluded from a
supplementary archive. They are not needed because `scripts/prepare_circuits.py`
recreates the circuit entry points and witness fixture. From the article root,
use `make artifact-zip`, not `make zip`, to create the supplementary archive.
That archive also carries `sections/` and the generated `tables/` beside the
artifact so that prose-to-data checks and table regeneration remain
self-contained; run the commands above from its `artifact/` directory.
The artifact software is released under the MIT License in `LICENSE`. The
double-blind review snapshot is available at
<https://anonymous.4open.science/r/edge-fusion/>.

## Layout

```text
vfusion/      model, primitives, stacks, attacks, and cost accounting
circuits/     binding and fusion circuit templates
scripts/      experiment drivers, generators, adversarial checks, claim checks
results/      measured JSON used to regenerate the paper tables
```
