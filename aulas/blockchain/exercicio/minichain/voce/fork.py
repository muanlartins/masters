"""Parte 6 — Cadeia mais longa / desempate entre forks.   (slide "vence a cadeia com mais trabalho")

Sem autoridade central, quando há duas versões da história o desempate é
OBJETIVO: vale a cadeia com mais trabalho acumulado. Reescrever a história
significaria refazer todo esse trabalho — e ainda correr na frente da rede.

Quando terminar, ligue "fork": True em config.py.
"""

from __future__ import annotations

from minichain.types import Block
from minichain import kit


def chain_work(chain: list[Block]) -> int:
    """Trabalho acumulado da cadeia = soma de 2**block.bits de cada bloco.

    (Quanto maior `bits`, menor o alvo e mais trabalho esperado; 2**bits é
    proporcional a 1/alvo.)
    """
    raise NotImplementedError("Parte 6: implemente chain_work")


def best_chain(chains: list[list[Block]]) -> list[Block] | None:
    """Dada uma lista de cadeias, devolva a VÁLIDA (kit.is_valid_chain) de maior
    chain_work. Se nenhuma for válida, devolva None."""
    raise NotImplementedError("Parte 6: implemente best_chain")
