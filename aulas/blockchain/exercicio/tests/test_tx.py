"""Parte 2 — Transações assinadas."""

from minichain import kit
from minichain.crypto import gen_keys
from minichain.types import Tx


def _signed(amount=10):
    sk, vk = gen_keys()
    tx = Tx(sender=vk.to_string(), recipient=b"bob", amount=amount)
    kit.sign_tx(tx, sk)
    return tx


def test_signature_validates():
    """uma transação recém-assinada é válida"""
    assert kit.tx_is_valid(_signed()) is True


def test_tampering_amount_invalidates():
    """mudar o valor depois de assinar invalida a assinatura"""
    tx = _signed(10)
    tx.amount = 999
    assert kit.tx_is_valid(tx) is False


def test_txid_is_32_bytes():
    """o txid tem 32 bytes"""
    assert len(kit.txid(_signed())) == 32


def test_txid_changes_with_content():
    """o txid muda quando o conteúdo muda"""
    assert kit.txid(_signed(1)) != kit.txid(_signed(2))


def test_coinbase_valid_without_signature():
    """a coinbase é válida sem assinatura"""
    cb = Tx(sender=b"", recipient=b"miner", amount=50)
    assert kit.tx_is_valid(cb) is True
