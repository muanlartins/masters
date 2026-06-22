#!/usr/bin/env bash
# Roda os testes com saída legível. Sem argumento: todos. Com argumento: uma parte.
#   ./testar.sh            -> tudo
#   ./testar.sh merkle     -> só a Parte 1 (merkle, tx, block, pow, chain, fork)
#   ./testar.sh merkle -s  -> idem, mas mostra seus print() ao vivo
# Flags extras (começando com -) são repassadas ao pytest; -s desliga a captura
# de stdout (sem ele, o pytest engole seus prints e só mostra se o teste falha).
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Rode ./instalar.sh primeiro."; exit 1; }
# --tb=no -p no:cacheprovider --no-header -rN: o relatório do --pretty é a saída;
# silenciamos o traceback e o resumo padrão do pytest.
PYTEST=(.venv/bin/python -m pytest --pretty --tb=no -rN --no-header -p no:cacheprovider)
parte=""
if [ -n "$1" ] && [ "${1#-}" = "$1" ]; then parte="$1"; shift; fi
if [ -n "$parte" ]; then exec "${PYTEST[@]}" "$@" "tests/test_$parte.py"; fi
exec "${PYTEST[@]}" "$@"
