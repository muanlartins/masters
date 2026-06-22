"""Parte 3 — Cabeçalho de 80 bytes e hash do bloco.   (slide "o cabeçalho de 80 bytes")

O hash do bloco é o SHA256² do cabeçalho — e é esse hash que vira o "prev" do
próximo bloco (o elo da corrente). O cabeçalho NÃO contém as transações: contém
só a RAIZ de Merkle delas.

Quando terminar, ligue "block": True em config.py.
"""

from __future__ import annotations

import struct

from minichain.crypto import sha256d
from minichain.types import Block
from minichain import kit


def compute_merkle(block: Block) -> bytes:
    """Calcule e GRAVE block.merkle_root a partir dos txids das transações; devolva-a.

    Use kit.merkle_root([...]) sobre os kit.txid(t) de cada t em block.txs.
    (Chamando via kit, isto usa o SEU Merkle/tx se você os tiver ligado.)
    """
    raise NotImplementedError("Parte 3: implemente compute_merkle")


def header_bytes(block: Block) -> bytes:
    """Serialize o cabeçalho de 80 bytes, EXATAMENTE nesta ordem:

        version    -> 4 bytes  (struct.pack(">I", ...))
        prev_hash  -> 32 bytes
        merkle_root-> 32 bytes
        timestamp  -> 4 bytes  (">I")
        bits       -> 4 bytes  (">I")
        nonce      -> 4 bytes  (">I")
    """
    raise NotImplementedError("Parte 3: implemente header_bytes")


def block_hash(block: Block) -> bytes:
    """Hash do bloco = sha256d(header_bytes(block))."""
    raise NotImplementedError("Parte 3: implemente block_hash")
