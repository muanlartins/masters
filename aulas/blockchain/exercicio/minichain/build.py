"""Montadores de cadeia — JÁ PRONTOS. Usam suas peças (via kit) para construir
blocos e cadeias de verdade, para você brincar no playground e nos testes.

Por que prontos? Porque eles só *orquestram* as peças que VOCÊ implementa
(compute_merkle, mine, block_hash). A lógica interessante está nas partes.
"""

from minichain import kit
from minichain.types import Block, Tx

DEFAULT_BITS = 8          # dificuldade baixinha: minera rápido para a aula/testes
GENESIS_PREV = b"\x00" * 32


def coinbase(recipient=b"miner", amount=50):
    """A transação que paga a recompensa ao minerador (sem remetente nem assinatura)."""
    return Tx(sender=b"", recipient=recipient, amount=amount)


def make_block(chain, txs, bits=DEFAULT_BITS, timestamp=0):
    """Cria, fecha (merkle) e MINERA um bloco que aponta para o topo de `chain`."""
    prev = kit.block_hash(chain[-1])
    block = Block(version=1, prev_hash=prev, txs=txs, timestamp=timestamp, bits=bits)
    kit.compute_merkle(block)
    block.nonce = kit.mine(block, bits)
    return block


def genesis(bits=DEFAULT_BITS):
    """Devolve uma cadeia nova: uma lista com só o bloco gênese (já minerado)."""
    block = Block(version=1, prev_hash=GENESIS_PREV, txs=[coinbase(b"genesis", 0)],
                  timestamp=0, bits=bits)
    kit.compute_merkle(block)
    block.nonce = kit.mine(block, bits)
    return [block]


def append(chain, txs, bits=DEFAULT_BITS, timestamp=0):
    """Minera um bloco com `txs` e o anexa à cadeia. Devolve a própria cadeia."""
    chain.append(make_block(chain, txs, bits=bits, timestamp=timestamp))
    return chain
