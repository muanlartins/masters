"""Parte 6 — Cadeia mais longa / desempate entre forks (REFERÊNCIA)."""

from minichain import kit


def chain_work(chain):
    # 2**bits é proporcional a 1/alvo => ao trabalho esperado por bloco
    return sum(2 ** block.bits for block in chain)


def best_chain(chains):
    valid = [c for c in chains if kit.is_valid_chain(c)]
    if not valid:
        return None
    return max(valid, key=chain_work)
