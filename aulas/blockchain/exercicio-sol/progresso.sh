#!/usr/bin/env bash
# Painel: o que falta e quantos testes passam por exercicio.
cd "$(dirname "$0")"
[ -d node_modules ] || { echo "Rode ./instalar.sh primeiro."; exit 1; }
exec node progresso.js
