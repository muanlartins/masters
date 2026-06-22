"""Parte 4 — Mineração / proof of work."""

from minichain import kit
from minichain.types import Block, Tx


def _block(bits):
    b = Block(version=1, prev_hash=b"\x00" * 32, txs=[Tx(b"", b"a", 1)],
              timestamp=0, bits=bits)
    kit.compute_merkle(b)
    return b


def test_meets_target_extremes():
    assert kit.meets_target(b"\x00" * 32, 16) is True   # menor hash possível
    assert kit.meets_target(b"\xff" * 32, 1) is False    # maior hash possível


def test_mine_finds_a_valid_nonce():
    b = _block(bits=12)
    b.nonce = kit.mine(b, 12)
    assert kit.meets_target(kit.block_hash(b), 12) is True


def test_mined_hash_has_the_required_leading_zero_byte():
    b = _block(bits=8)
    b.nonce = kit.mine(b, 8)
    assert kit.block_hash(b)[0] == 0   # 8 bits de zero = primeiro byte nulo
