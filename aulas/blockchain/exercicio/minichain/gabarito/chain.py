"""Parte 5 — Encadeamento e validação da cadeia (REFERÊNCIA)."""

from __future__ import annotations

from minichain.types import Block
from minichain import kit

GENESIS_PREV = b"\x00" * 32


def validate_block(block: Block, prev_block: Block | None) -> bool:
    # 1. ligação com o anterior
    if prev_block is None:
        if block.prev_hash != GENESIS_PREV:
            return False
    elif block.prev_hash != kit.block_hash(prev_block):
        return False
    # 2. a raiz de Merkle bate com as transações
    if block.merkle_root != kit.merkle_root([kit.txid(t) for t in block.txs]):
        return False
    # 3. a prova de trabalho é válida
    if not kit.meets_target(kit.block_hash(block), block.bits):
        return False
    # 4. todas as transações são válidas
    return all(kit.tx_is_valid(t) for t in block.txs)


def is_valid_chain(chain: list[Block]) -> bool:
    prevs = [None, *chain[:-1]]   # o antecessor de cada bloco (None no gênese)
    return all(validate_block(block, prev) for block, prev in zip(chain, prevs))
