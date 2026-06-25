#!/usr/bin/env bash
# Roda os testes. Sem argumento: todos. Com argumento: um exercicio.
#   ./testar.sh            -> tudo
#   ./testar.sh cofre      -> so o exercicio 1 (cofre, votacao, crowdfunding,
#                             leilao, moeda, dvp)
#   ./testar.sh dvp --grep atomico  -> filtra por nome do teste (repassado ao mocha)
cd "$(dirname "$0")"
[ -d node_modules ] || { echo "Rode ./instalar.sh primeiro."; exit 1; }
parte=""
if [ -n "$1" ] && [ "${1#-}" = "$1" ]; then parte="$1"; shift; fi
if [ -n "$parte" ]; then exec npx hardhat test "test/$parte.test.js" "$@"; fi
exec npx hardhat test "$@"
