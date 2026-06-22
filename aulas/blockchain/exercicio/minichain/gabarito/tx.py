"""Parte 2 — Transações assinadas (REFERÊNCIA)."""

from __future__ import annotations

import struct

from ecdsa import SigningKey

from minichain.crypto import sha256d, ec_sign, ec_verify
from minichain.types import Tx


def payload(tx: Tx) -> bytes:
    return tx.sender + tx.recipient + struct.pack(">Q", tx.amount)


def txid(tx: Tx) -> bytes:
    return sha256d(payload(tx))


def sign_tx(tx: Tx, sk: SigningKey) -> Tx:
    tx.signature = ec_sign(sk, payload(tx))
    return tx


def tx_is_valid(tx: Tx) -> bool:
    if tx.sender == b"":          # coinbase: sem remetente, sem assinatura
        return tx.amount >= 0
    return ec_verify(tx.sender, tx.signature, payload(tx))
