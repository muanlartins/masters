"""Parte 4 — Mineração / proof of work (REFERÊNCIA)."""

from __future__ import annotations

from minichain.crypto import target_from_bits
from minichain.types import Block
from minichain import kit


def meets_target(h: bytes, bits: int) -> bool:
    return int.from_bytes(h, "big") < target_from_bits(bits)


def mine(block: Block, bits: int) -> int:
    nonce = 0
    while True:
        block.nonce = nonce
        if meets_target(kit.block_hash(block), bits):
            return nonce
        nonce += 1
