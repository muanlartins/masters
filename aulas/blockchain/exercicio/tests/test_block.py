"""Parte 3 — Cabeçalho de 80 bytes e hash do bloco."""

from minichain import kit
from minichain.crypto import sha256d
from minichain.types import Block, Tx


def _block():
    txs = [Tx(b"", b"a", 1), Tx(b"", b"b", 2)]
    return Block(version=1, prev_hash=b"\x00" * 32, txs=txs, timestamp=0, bits=8)


def test_compute_merkle_matches_txids():
    b = _block()
    root = kit.compute_merkle(b)
    assert root == kit.merkle_root([kit.txid(t) for t in b.txs])
    assert b.merkle_root == root


def test_header_is_80_bytes():
    b = _block()
    kit.compute_merkle(b)
    assert len(kit.header_bytes(b)) == 80


def test_block_hash_is_double_sha_of_header():
    b = _block()
    kit.compute_merkle(b)
    assert kit.block_hash(b) == sha256d(kit.header_bytes(b))


def test_nonce_changes_the_hash():
    b = _block()
    kit.compute_merkle(b)
    h0 = kit.block_hash(b)
    b.nonce = 1
    assert kit.block_hash(b) != h0
