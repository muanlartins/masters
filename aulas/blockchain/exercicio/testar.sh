#!/usr/bin/env bash
# Roda os testes com saída legível. Sem argumento: todos. Com argumento: uma parte.
#   ./testar.sh            -> tudo
#   ./testar.sh merkle     -> só a Parte 1 (merkle, tx, block, pow, chain, fork)
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Rode ./instalar.sh primeiro."; exit 1; }
# --tb=no -p no:cacheprovider --no-header -rN: o relatório do --pretty é a saída;
# silenciamos o traceback e o resumo padrão do pytest.
PYTEST=(.venv/bin/python -m pytest --pretty --tb=no -rN --no-header -p no:cacheprovider)
if [ -n "$1" ]; then exec "${PYTEST[@]}" "tests/test_$1.py"; fi
exec "${PYTEST[@]}"
