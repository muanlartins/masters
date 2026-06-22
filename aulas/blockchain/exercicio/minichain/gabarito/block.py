"""Parte 3 — Cabeçalho de 80 bytes e hash do bloco (REFERÊNCIA)."""

import struct

from minichain.crypto import sha256d
from minichain import kit


def compute_merkle(block):
    block.merkle_root = kit.merkle_root([kit.txid(t) for t in block.txs])
    return block.merkle_root


def header_bytes(block):
    return (
        struct.pack(">I", block.version)    # 4
        + block.prev_hash                   # 32
        + block.merkle_root                 # 32
        + struct.pack(">I", block.timestamp)  # 4
        + struct.pack(">I", block.bits)       # 4
        + struct.pack(">I", block.nonce)      # 4  -> 80 bytes
    )


def block_hash(block):
    return sha256d(header_bytes(block))
