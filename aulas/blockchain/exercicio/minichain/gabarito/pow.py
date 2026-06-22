"""Parte 4 — Mineração / proof of work (REFERÊNCIA)."""

from minichain.crypto import target_from_bits
from minichain import kit


def meets_target(h, bits):
    return int.from_bytes(h, "big") < target_from_bits(bits)


def mine(block, bits):
    nonce = 0
    while True:
        block.nonce = nonce
        if meets_target(kit.block_hash(block), bits):
            return nonce
        nonce += 1
