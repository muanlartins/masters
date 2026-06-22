"""Parte 5 — Encadeamento e validação da cadeia."""

from minichain import kit, build
from minichain.crypto import gen_keys
from minichain.types import Tx


def _signed(amount=5):
    sk, vk = gen_keys()
    tx = Tx(sender=vk.to_string(), recipient=b"bob", amount=amount)
    kit.sign_tx(tx, sk)
    return tx


def _chain():
    chain = build.genesis(bits=8)
    build.append(chain, [_signed(1)], bits=8)
    build.append(chain, [_signed(2)], bits=8)
    return chain


def test_freshly_built_chain_is_valid():
    """uma cadeia recém-minerada é válida"""
    assert kit.is_valid_chain(_chain()) is True


def test_genesis_alone_is_valid():
    """o bloco gênese sozinho é válido"""
    assert kit.is_valid_chain(build.genesis(bits=8)) is True


def test_tampered_transaction_breaks_the_chain():
    """adulterar uma transação invalida a cadeia"""
    chain = _chain()
    chain[1].txs[0].amount = 999
    assert kit.is_valid_chain(chain) is False


def test_broken_prev_link_breaks_the_chain():
    """quebrar o elo (prev_hash) invalida a cadeia"""
    chain = _chain()
    chain[2].prev_hash = b"\x11" * 32
    assert kit.is_valid_chain(chain) is False
