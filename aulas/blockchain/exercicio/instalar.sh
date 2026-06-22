#!/usr/bin/env bash
# Cria a venv e instala as dependências. Rode uma vez.
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Instale o Python 3 primeiro."; exit 1; }
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "Pronto! Agora rode ./progresso.sh"
