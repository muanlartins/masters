"""Parte 4 — Mineração / proof of work.   (slide "minerar é achar um hash < alvo")

Minerar é só "chutar um nonce até o hash do cabeçalho cair abaixo de um alvo".
Não há atalho: não dá para calcular o nonce, só testar. Esse trabalho é o que
custa energia — e o que torna reescrever a história caro.

Quando terminar, ligue "pow": True em config.py.
"""

from __future__ import annotations

from minichain.crypto import target_from_bits
from minichain.types import Block
from minichain import kit


def meets_target(h: bytes, bits: int) -> bool:
    """True se o hash `h` (bytes), lido como inteiro, for < alvo.

    alvo = target_from_bits(bits) = 2**(256-bits).
    Dica: int.from_bytes(h, "big").
    """
    raise NotImplementedError("Parte 4: implemente meets_target")


def mine(block: Block, bits: int) -> int:
    """Ache, por força bruta, um nonce que satisfaça o alvo; devolva esse nonce.

    Varie block.nonce a partir de 0; em cada tentativa cheque
    meets_target(kit.block_hash(block), bits). Devolva o primeiro nonce que serve.
    """
    raise NotImplementedError("Parte 4: implemente mine")
