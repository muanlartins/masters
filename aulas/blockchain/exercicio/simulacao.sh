#!/usr/bin/env bash
# Simulação narrada: percorre cada peça mostrando o que é feito e como.
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Rode ./instalar.sh primeiro."; exit 1; }
exec .venv/bin/python simulacao.py
