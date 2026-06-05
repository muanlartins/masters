# Hand-off: TON_IoT telemetry-leak novelty survey — 2026-05-29

**Purpose.** Consolidate the literature-survey findings that establish the
**novelty** of our central claim: the public TON_IoT *telemetry* subsets
(notably **Fridge** and **Garage_Door**) contain a *deterministic categorical
leak* (Cramér's V = 1.000 between a categorical feature value and the label) that
yields trivial ~100% accuracy, and this leak is a **sub-sampling artifact** —
the authors subsampled "normal" rows (≈35,000 → 15,000 per device) in the public
`Train_Test_IoT_dataset`, which removed exactly the rows that broke the
association, hardening it to determinism.

This doc is for the session that writes `sections/relatedworks.tex` (and the
novelty framing in intro/discussion). It records exact citations, verbatim
quotes, links, and the rhetorical contrast to build. **All four primary PDFs are
saved locally in `articles/toniot-wisard/`** and every quote below was verified
against the actual document (not just an abstract).

Related memory: `project_toniot_leak_novelty.md`, `project_toniot_dataset_versions.md`.

---

## 1. Headline conclusion

**Our telemetry-leak-via-sub-sampling diagnosis appears novel — no direct
precedent found in 2020–2026 literature or grey literature.**

The leakage discourse around TON_IoT exists but is **entirely network/flow-side**
and concerns a *different mechanism* (identifier shortcut features: IP / port /
MAC / high-cardinality SSL-HTTP-DNS text). No surveyed work inspects the
**telemetry** CSVs at the categorical-feature level, mentions Cramér's V on
telemetry, the 35k→15k normal sub-sampling, the Fridge/Garage_Door categorical
determinism, or the Train_Test-vs-Processed distinction as a *leakage* axis.

The foundational dataset paper (Alsaedi et al. 2020), cited >1000×, never
mentions any leakage.

---

## 2. The three literature buckets (the spine of the related-work contrast)

### Bucket A — Documented leakage critiques, but NETWORK-side only (IP/port/labeling)

These are the "known leakage" papers to cite as the contrast. They prove the
community *can* spot leakage in TON_IoT — but only on the network dataset, via
identifier features that **do not exist in the telemetry CSVs**.

**A1. Shaikhanova et al. (2025) — the single cleanest "IP/port = leakage" citation.**
> Shaikhanova, A., Kuznetsov, O., Tokkuliyeva, A., Ayapbergenov, K., Olzhas, S.,
> & Danir, T. (2025). *Security Audit of IoT Device Networks: A Reproducible
> Machine Learning Framework for Threat Detection and Performance Benchmarking.*
> **Sensors**, 25(24), 7519. DOI 10.3390/s25247519.
> - MDPI: https://www.mdpi.com/1424-8220/25/24/7519
> - Open-access PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC12736874/

Verbatim (their §8.5):
> "The original dataset study by Moustafa et al. (2021) achieved 99.97% accuracy
> using GBM, but this result included **IP addresses and port numbers as
> features—attributes that can introduce data leakage and overestimate real-world
> performance**."

Mitigation: they drop 8 high-cardinality text columns on `train_test_network.csv`
— `ssl_subject`, `ssl_issuer`, `http_uri`, `http_user_agent`,
`http_orig_mime_types`, `http_resp_mime_types`, `weird_addl`, `dns_query`. None
exist in telemetry → their critique cannot reach our leak.

**A2. Dharini et al. (2026) — explicit "bias from predefined IP/port" critique.**
> Dharini, N., Janani, V. S., & Katiravan, J. (2026). *Efficient detection of
> intrusions in TON-IoT dataset using hybrid feature selection approach.*
> **Scientific Reports**, 16:7763. DOI 10.1038/s41598-026-37834-y.
> - https://www.nature.com/articles/s41598-026-37834-y

Has a dedicated "Limitations of existing ToN-IoT and NF-ToN-IoT datasets"
section. Verbatim:
> "First, attacks in these datasets were **deliberately launched from predefined
> IP address ranges and port numbers, causing source and destination IPs and
> ports to act as strong attack identifiers rather than behavior-based
> indicators**. This introduces dataset bias and limits generalization to unseen
> attackers operating from different network locations."

Research objective (i): *"To identify and mitigate bias introduced by fixed IP-
and port-based attack generation in the ToN-IoT dataset."* Solution: eliminates
IP/port identifiers, derives a 5-feature behavior-driven set.
**Useful side-citation:** its related work records *"Tareq et al. … windows with
network version of the ToN-IoT dataset achieved 100% accuracy … using inception
time approach"* — i.e. the InceptionTime 100% result, recorded uncritically.

**A3. Raskovalov, Gabdullin & Dolmatov (2022) — the "ships a corrected dataset" critique.**
> Raskovalov, A., Gabdullin, N., & Dolmatov, V. (2022). *Investigation and
> rectification of NIDS datasets and standardized feature set derivation for
> network attack detection with graph neural networks.* **arXiv:2212.13994v2**
> (29 Dec 2022). JSC "Kryptonite".
> - Abstract: https://arxiv.org/abs/2212.13994
> - PDF: https://arxiv.org/pdf/2212.13994

Produces a corrected version **ToN-IoT-R**. Verbatim (§2.1):
> "In all datasets there are **flows where traffic directed outside the test
> network is recorded as some form of attack**, but such traffic should not be
> considered in the analysis and training. There are also **flows labeled as
> attacks that contain normal data exchange with network router and DNS resolver
> (IP: 192.168.1.1)**. To exclude such cases, we filter the full version of
> ToN-IoT ('Processed Network Dataset' files in [3]) and obtain a new version
> labeled as 'ToN-IoT-R'."

Table 1: full ToN-IoT 21,978,630 flows → ToN-IoT-R 18,902,360 after filtering
(MITM drops 1,052 → 0). This is **flow-level mislabeling**, not feature leakage,
and entirely network-side.

**A4. Booij et al. (2022) — the heterogeneity critique (NOT leakage).** Worth
naming so reviewers don't think we missed the most-cited dedicated TON_IoT
critique; clarify it's about cross-dataset generalization, not leakage.
> Booij, T. M., Chiscop, I., Meeuwissen, E., Moustafa, N., & den Hartog, F. T. H.
> (2022). *ToN_IoT: The Role of Heterogeneity and the Need for Standardization of
> Features and Attack Types in IoT Network Intrusion Data Sets.* **IEEE Internet
> of Things Journal**, 9(1), 485–496. DOI 10.1109/JIOT.2021.3085194.
> (Note: co-authored by Moustafa himself.)

### Bucket B — Near-100% on TELEMETRY, accepted UNCRITICALLY (the "nobody noticed" evidence)

These are the papers that *should* have caught our leak and didn't. They are the
direct evidence for the novelty claim.

**B1. Sharrab et al. (2025) — BEST citation: dedicated analysis of Garage Door, 100%, no alarm.**
> Sharrab, Y., Al-Ghuwairi, A.-R., Alomoush, A., Al-Husini, A., Al-Burgan, D., &
> Alsmadi, I. (2025). *Analysis and Evaluation of ToN IoT Windows and Garage Door
> Datasets.* **2025 5th Intelligent Cybersecurity Conference (ICSC)**, pp.
> 214–218. DOI 10.1109/ICSC65596.2025.11140466.
> - https://ieeexplore.ieee.org/document/11140466/
> - PDF saved locally: `Analysis_and_Evaluation_of_ToN_IoT_Windows_and_Garage_Door_Datasets.pdf`

Garage Door classification accuracy (their Table V):
| Algorithm | Accuracy |
|---|---|
| J48 | 99.99% |
| LMT | **100%** |
| RandomForest | 98% |
| HoeffdingTree | **100%** |
| DecisionStump | **67.16%** |

Their interpretation (verbatim, §IV-A): *"These results demonstrate that
traditional classifiers perform well on the ToN IoT datasets … which highlights
the predictive power of the top correlated features."* Conclusion: *"near-perfect
accuracy even with a reduced set of the most correlated features … careful
feature selection can improve model efficiency without compromising detection
performance."* **No mention of leakage, determinism, or any red flag — 100% is
framed as a virtue.**

⚠️ **Two important nuances for how we cite Sharrab (do not overstate):**
1. **Different operating point.** Sharrab reports Garage Door as 591,446 records
   (87% normal) and builds a *"balanced training subset with 35,000 normal
   observations."* That is the **full Processed distribution subsampled to ~35k
   normal**, NOT the public `Train_Test` (15k normal) we analyzed. So Sharrab and
   we sit at the two endpoints of the very sub-sampling axis we claim drives the
   leak. (Per `project_toniot_dataset_versions.md`: at the ~35k level the
   telemetry association is only *partial*, V≈0.569 for analogous features; the
   further 35k→15k cut is what hardens it to V=1.000.)
2. **The DecisionStump=67.16% data point may CORROBORATE our thesis.** A
   one-level (single-split) tree scoring only 67% while full trees hit 100% is
   inconsistent with a single feature being deterministically equal to the label
   *at the 35k operating point* — which is exactly what our sub-sampling argument
   predicts (no single feature is deterministic until the 15k cut). This is a
   strong supporting inference, **but it is reasoned from their table, not from
   our data — VERIFY against our own Garage_Door DecisionStump / single-feature
   numbers before putting it in print.**

**B2. Alotaibi & Ilyas (2023) — 6 telemetry devices combined, 98.64%, no limitations.**
> Alotaibi, Y., & Ilyas, M. (2023). [stacking-ensemble IDS on TON_IoT telemetry].
> **Sensors**, 23(12), 5568.
> - https://pmc.ncbi.nlm.nih.gov/articles/PMC10305290/

Combines all six telemetry device subsets (Fridge, Garage_Door, Thermostat,
GPS_Tracker, Motion_Light, Weather; ~700,389 instances), reports a stacking
ensemble at **98.64%** (their Table 8). No limitations section on the high
accuracy; no mention of leakage / deterministic features / bias. Framed
positively as beating prior 86–97% work.

**B3. InceptionTime per-device (search-surfaced; trace via Dharini's citation of "Tareq et al.").**
Reported per-device telemetry accuracy: weather / thermostat / GPS **100%**,
fridge **99%**, garage **99.4%**, Modbus 99.9%, motion-light 99.5% — uncritical.
(Confirm the exact Tareq et al. citation from Dharini's reference list before use.)

### Bucket C — Came CLOSEST to a telemetry critique, but EXPLICITLY disclaimed a leak

**C1. Benaddi et al. (2025) — attributes near-100% to "separable signatures," rules out a leak.**
> arXiv:2512.19488.
> - https://arxiv.org/abs/2512.19488 / https://arxiv.org/pdf/2512.19488

Verbatim:
> "The near-perfect accuracy … even after source-aware partitioning and strict
> preprocessing, indicates that the limitation lies less in the training pipeline
> than in the dataset structure itself. In the TON_IoT traces, attack signatures
> remain highly separable, enabling … full memorization."
> "**The pipeline prevents leakage**, yet the dataset's restricted adversarial
> diversity and absence of temporal drift likely inflate [results]."

This is a dataset-bias/separability argument that **explicitly disclaims a leak** —
the opposite of our finding. Excellent foil: someone got close to the symptom
and concluded "not a leak."

---

## 3. The novelty framing to build (suggested rhetorical structure)

1. TON_IoT is a flagship IoT-IDS benchmark (>1000 citations on the telemetry
   paper alone).
2. The community *has* identified leakage in it — but only on the **network**
   dataset, via **identifier features** (IP/port: Shaikhanova 2025, Dharini 2026;
   flow mislabeling: Raskovalov 2022). Cite these to show leakage-awareness exists.
3. On the **telemetry** subsets, the literature either (a) reports ~100%
   uncritically as a dataset virtue (Sharrab 2025 on the *exact device*, Garage
   Door; Alotaibi 2023; InceptionTime), or (b) when the perfect separability is
   directly observed, **misattributes** it to "correlated features" /
   "separable signatures" and **explicitly rules out a leak** (Benaddi 2025).
4. Our contribution: a feature-level diagnosis (Cramér's V = 1.000 on
   Fridge/Garage_Door) tracing the determinism to the authors' undocumented
   normal-row sub-sampling (35k→15k) in the public Train_Test subset — a leak
   mechanism distinct from the network-side identifier leakage and, to our
   knowledge, previously unreported on the telemetry data.

One-line version: *"Network-side leakage in TON_IoT is documented and even
corrected (ToN-IoT-R); the telemetry-side categorical leak we identify has gone
unremarked — and where its symptom was observed, it was misdiagnosed as benign
feature separability."*

---

## 4. Caveats / open items for the writing session

- **English-language bias.** Searches were English-only. A non-English thesis or
  workshop paper could be prior art (judged low probability, but state the
  search scope honestly if a reviewer presses).
- **arXiv dates.** Benaddi (2512.19488) and one critique (2601.20548) are
  late-2025/early-2026 — real and past relative to today (2026-05), confirmed;
  earlier auto-flagging as "future-dated" was a mistake.
- **Verify the DecisionStump corroboration (§B1 nuance 2) against our own
  numbers** before asserting it.
- **Confirm the Tareq et al. (InceptionTime) full citation** from Dharini's
  reference list before citing B3.
- The "foundational paper is silent on leakage" point is an absence-of-evidence
  claim — phrase as "makes no mention of" rather than "proves there is none."

## 5. Local assets (in `articles/toniot-wisard/`)

- `Analysis_and_Evaluation_of_ToN_IoT_Windows_and_Garage_Door_Datasets.pdf` (Sharrab 2025)
- `s41598-026-37834-y.pdf` (Dharini 2026)
- `2212.13994v2.pdf` (Raskovalov 2022)
- (Alsaedi 2020 foundational paper — IEEE Access doc 9189760; not yet saved locally)
