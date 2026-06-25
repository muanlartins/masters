#!/usr/bin/env bash
# Instala o Hardhat e as dependencias. Rode uma vez.
set -e
cd "$(dirname "$0")"
command -v npm >/dev/null || { echo "Instale o Node.js (18+) primeiro."; exit 1; }
npm install --silent
echo "Pronto! Agora rode ./progresso.sh"
