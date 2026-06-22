"""Primitivas criptográficas — JÁ PRONTAS. Você não precisa mexer aqui.

São as "peças que já existiam" antes do Bitcoin (a linha do tempo da aula):
o hash de mão única (SHA-256) e a assinatura digital (curva elíptica).
"""

import hashlib

from ecdsa import SigningKey, VerifyingKey, SECP256k1


# ── hash ──────────────────────────────────────────────────────────────────
def sha256(b: bytes) -> bytes:
    """SHA-256 simples (32 bytes)."""
    return hashlib.sha256(b).digest()


def sha256d(b: bytes) -> bytes:
    """SHA-256 DUPLO (o "SHA256²" da aula): sha256(sha256(b)).

    O Bitcoin aplica o SHA duas vezes em quase tudo (header, txid, nós da
    árvore de Merkle) por robustez contra ataques de extensão de comprimento.
    """
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def to_hex(b: bytes) -> str:
    return b.hex()


def from_hex(s: str) -> bytes:
    return bytes.fromhex(s)


# ── alvo da prova de trabalho ───────────────────────────────────────────────
def target_from_bits(bits: int) -> int:
    """Alvo T da mineração: exigir `bits` zeros à esquerda equivale a T = 2**(256-bits).

    Um hash de 256 bits "vale" se, como inteiro, for < T. Quanto maior `bits`,
    menor o alvo, mais raro o hash válido, mais trabalho. (O Bitcoin real usa
    uma codificação compacta "nBits"; aqui simplificamos para nº de zeros.)
    """
    return 1 << (256 - bits)


# ── assinatura digital (secp256k1, a mesma curva do Bitcoin) ────────────────
def gen_keys():
    """Gera um par (chave_privada, chave_publica)."""
    sk = SigningKey.generate(curve=SECP256k1)
    return sk, sk.get_verifying_key()


def ec_sign(sk, msg: bytes) -> bytes:
    """Assina `msg` com a chave privada `sk`. Devolve a assinatura (bytes)."""
    return sk.sign(msg)


def ec_verify(pub_bytes: bytes, sig: bytes, msg: bytes) -> bool:
    """True se `sig` é uma assinatura válida de `msg` pela chave pública `pub_bytes`."""
    try:
        VerifyingKey.from_string(pub_bytes, curve=SECP256k1).verify(sig, msg)
        return True
    except Exception:
        return False
