"""Parte 2 — Transações assinadas (REFERÊNCIA)."""

import struct

from minichain.crypto import sha256d, ec_sign, ec_verify


def payload(tx):
    return tx.sender + tx.recipient + struct.pack(">Q", tx.amount)


def txid(tx):
    return sha256d(payload(tx))


def sign_tx(tx, sk):
    tx.signature = ec_sign(sk, payload(tx))
    return tx


def tx_is_valid(tx):
    if tx.sender == b"":          # coinbase: sem remetente, sem assinatura
        return tx.amount >= 0
    return ec_verify(tx.sender, tx.signature, payload(tx))
