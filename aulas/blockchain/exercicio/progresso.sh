#!/usr/bin/env bash
# Painel: o que falta e quantos testes passam por parte.
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Rode ./instalar.sh primeiro."; exit 1; }
exec .venv/bin/python progresso.py
