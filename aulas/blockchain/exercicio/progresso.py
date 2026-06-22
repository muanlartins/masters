#!/usr/bin/env python3
"""Seu painel de progresso. Rode:  python progresso.py

Mostra, parte a parte: se você ligou em config.py ([VOCÊ]) ou ainda usa o
gabarito ([gabarito]), e quantos testes daquela parte passam.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from minichain import config  # noqa: E402

PARTS = [
    ("merkle", "Parte 1 · Árvore de Merkle",          "tests/test_merkle.py"),
    ("tx",     "Parte 2 · Transações assinadas",      "tests/test_tx.py"),
    ("block",  "Parte 3 · Cabeçalho & hash do bloco", "tests/test_block.py"),
    ("pow",    "Parte 4 · Mineração (proof of work)", "tests/test_pow.py"),
    ("chain",  "Parte 5 · Encadeamento & validação",  "tests/test_chain.py"),
    ("fork",   "Parte 6 · Cadeia mais longa (forks)", "tests/test_fork.py"),
]


def run(path):
    r = subprocess.run(
        [sys.executable, "-m", "pytest", path, "--no-header",
         "--tb=no", "-p", "no:cacheprovider"],
        cwd=HERE, capture_output=True, text=True,
    )
    out = r.stdout + r.stderr
    passed = int((re.search(r"(\d+) passed", out) or [0, 0])[1])
    failed = int((re.search(r"(\d+) failed", out) or [0, 0])[1])
    errors = int((re.search(r"(\d+) error", out) or [0, 0])[1])
    total = passed + failed + errors
    return passed, total


def main():
    print("\n  minichain — seu progresso")
    print("  " + "─" * 52)
    mine_done = 0
    for key, title, path in PARTS:
        is_mine = config.MINHA[key]
        passed, total = run(path)
        tag = "[VOCÊ]    " if is_mine else "[gabarito]"
        mark = "✓" if passed == total and total else "✗"
        if is_mine and passed == total and total:
            mine_done += 1
        print(f"  {title:<36} {tag}  {passed}/{total} {mark}")
    print("  " + "─" * 52)
    print(f"  Partes suas concluídas: {mine_done}/{len(PARTS)}"
          "   (ligue cada uma em config.py ao terminar)\n")


if __name__ == "__main__":
    main()
