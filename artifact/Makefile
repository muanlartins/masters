# Reproduce every measurement the paper reports.
#
#   make deps      install Node and Python dependencies
#   make ptau      fetch the powers-of-tau files the circuits need
#   make all       run every experiment and regenerate the paper's tables
#   make verify    re-check every numeric claim in the prose
#
# circom is not on npm; set CIRCOM=/path/to/circom if it is not on PATH.

BOOTSTRAP_PY ?= python3
PY      ?= .venv/bin/python
CIRCOM  ?= circom
PTAU_URL = https://storage.googleapis.com/zkevm/ptau
N        = 60

.PHONY: all deps ptau prepare circuits stacks sampling snark tables verify clean

all: stacks sampling snark tables verify

deps:
	npm ci
	$(BOOTSTRAP_PY) -m venv .venv
	$(PY) -m pip install -r requirements.txt

ptau: build/pot15.ptau build/pot16.ptau build/pot17.ptau

build/pot%.ptau:
	mkdir -p build
	curl -sSL -o $@ $(PTAU_URL)/powersOfTau28_hez_final_$*.ptau

prepare:
	$(PY) scripts/prepare_circuits.py

circuits: prepare
	mkdir -p build
	for c in binding mean excursion mkt; do \
	  CIRCOM=$(CIRCOM) $(CIRCOM) build/main_$${c}_$(N).circom --r1cs --wasm \
	    -o build -l node_modules -l circuits; \
	done
	$(CIRCOM) build/main_attributed_60.circom --r1cs -o build -l node_modules -l circuits
	$(CIRCOM) build/main_attributed_12.circom --r1cs --wasm -o build -l node_modules -l circuits

stacks:
	$(PY) scripts/run_stacks.py
	$(PY) scripts/bls_separation.py

sampling:
	$(PY) scripts/sampling_mc.py

snark: ptau circuits
	CIRCOM=$(CIRCOM) $(PY) scripts/snark_bench.py
	CIRCOM=$(CIRCOM) $(PY) scripts/compile_only.py attributed 60

tables:
	$(PY) scripts/make_tables.py

verify:
	$(PY) scripts/audit_tests.py
	$(PY) scripts/verify_paper.py

clean:
	rm -rf build/*.zkey build/*.wtns build/*_js build/*.r1cs __pycache__ vfusion/__pycache__
