#!/usr/bin/env bash
# Roda os testes. Sem argumento: todos. Com argumento: uma parte.
#   ./testar.sh            -> tudo
#   ./testar.sh merkle     -> só a Parte 1 (merkle, tx, block, pow, chain, fork)
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Rode ./instalar.sh primeiro."; exit 1; }
if [ -n "$1" ]; then exec .venv/bin/python -m pytest "tests/test_$1.py"; fi
exec .venv/bin/python -m pytest
