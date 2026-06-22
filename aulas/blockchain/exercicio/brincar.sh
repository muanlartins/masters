#!/usr/bin/env bash
# Passeio visual: minera, adultera, prova com Merkle. Não vale nota.
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Rode ./instalar.sh primeiro."; exit 1; }
exec .venv/bin/python playground.py
