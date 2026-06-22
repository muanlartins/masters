"""Parte 2 — Transações assinadas.   (slide de assinaturas / demo Anders "Signatures")

A assinatura prova DUAS coisas de uma vez: quem autorizou (só a chave privada
assina) e que o conteúdo não mudou (1 bit diferente -> assinatura inválida).

Quando terminar, ligue "tx": True em config.py.
"""

from __future__ import annotations

import struct

from ecdsa import SigningKey

from minichain.crypto import sha256d, ec_sign, ec_verify
from minichain.types import Tx


def payload(tx: Tx) -> bytes:
    """Bytes canônicos que a assinatura cobre: sender + recipient + amount.

    Use struct.pack(">Q", tx.amount) para os 8 bytes do valor (big-endian).
    NÃO inclua tx.signature aqui (a assinatura cobre o payload, não a si mesma).
    """
    raise NotImplementedError("Parte 2: implemente payload")


def txid(tx: Tx) -> bytes:
    """Identificador da transação = sha256d(payload(tx)). 32 bytes."""
    raise NotImplementedError("Parte 2: implemente txid")


def sign_tx(tx: Tx, sk: SigningKey) -> Tx:
    """Assina: grave ec_sign(sk, payload(tx)) em tx.signature e devolva tx."""
    raise NotImplementedError("Parte 2: implemente sign_tx")


def tx_is_valid(tx: Tx) -> bool:
    """Valida a transação:
      - coinbase (tx.sender == b"") -> válida se tx.amount >= 0 (sem assinatura).
      - caso contrário -> ec_verify(tx.sender, tx.signature, payload(tx)).
    """
    raise NotImplementedError("Parte 2: implemente tx_is_valid")
