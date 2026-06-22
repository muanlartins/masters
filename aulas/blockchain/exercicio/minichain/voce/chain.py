"""Parte 5 — Encadeamento e validação da cadeia.   (slide "encadeamento" / Anders Blockchain)

Cada bloco carrega o hash do anterior. Mexeu num bloco, todos os seguintes
quebram — porque o hash de um entra no cabeçalho do próximo. Validar a cadeia
é re-checar cada elo do zero.

Quando terminar, ligue "chain": True em config.py.
"""

from minichain import kit

GENESIS_PREV = b"\x00" * 32


def validate_block(block, prev_block):
    """True se `block` é válido em relação a `prev_block` (None no gênese). Cheque:

      1. ligação: se prev_block é None, block.prev_hash == GENESIS_PREV;
                  senão, block.prev_hash == kit.block_hash(prev_block).
      2. merkle:  block.merkle_root == kit.merkle_root([kit.txid(t) for t in block.txs]).
      3. trabalho: kit.meets_target(kit.block_hash(block), block.bits).
      4. txs:     todas as transações com kit.tx_is_valid(t) == True.
    """
    raise NotImplementedError("Parte 5: implemente validate_block")


def is_valid_chain(chain):
    """True se TODOS os blocos de `chain` (lista, do gênese ao topo) passam em
    validate_block, cada um contra o seu antecessor."""
    raise NotImplementedError("Parte 5: implemente is_valid_chain")
