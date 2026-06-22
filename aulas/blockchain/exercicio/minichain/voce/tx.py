"""Parte 2 — Transações assinadas.   (slide de assinaturas / demo Anders "Signatures")

A assinatura prova DUAS coisas de uma vez: quem autorizou (só a chave privada
assina) e que o conteúdo não mudou (1 bit diferente -> assinatura inválida).

Quando terminar, ligue "tx": True em config.py.
"""

import struct

from minichain.crypto import sha256d, ec_sign, ec_verify


def payload(tx):
    """Bytes canônicos que a assinatura cobre: sender + recipient + amount.

    Use struct.pack(">Q", tx.amount) para os 8 bytes do valor (big-endian).
    NÃO inclua tx.signature aqui (a assinatura cobre o payload, não a si mesma).
    """
    raise NotImplementedError("Parte 2: implemente payload")


def txid(tx):
    """Identificador da transação = sha256d(payload(tx)). 32 bytes."""
    raise NotImplementedError("Parte 2: implemente txid")


def sign_tx(tx, sk):
    """Assina: grave ec_sign(sk, payload(tx)) em tx.signature e devolva tx."""
    raise NotImplementedError("Parte 2: implemente sign_tx")


def tx_is_valid(tx):
    """Valida a transação:
      - coinbase (tx.sender == b"") -> válida se tx.amount >= 0 (sem assinatura).
      - caso contrário -> ec_verify(tx.sender, tx.signature, payload(tx)).
    """
    raise NotImplementedError("Parte 2: implemente tx_is_valid")
