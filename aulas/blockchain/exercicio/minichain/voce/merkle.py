"""Parte 1 — Árvore de Merkle.   (slide: "a árvore de Merkle prova que uma tx está no bloco")

A raiz de Merkle resume TODAS as transações de um bloco num único hash de 32 B.
Com ela, uma carteira leve prova que uma transação está no bloco baixando só
~log2(n) hashes — e não o bloco inteiro.

Quando terminar, ligue "merkle": True em config.py.
"""

from __future__ import annotations

from minichain.crypto import sha256d


def merkle_root(leaves: list[bytes]) -> bytes:
    """Raiz de Merkle (32 bytes) de uma lista de folhas (cada folha são bytes).

    Regra (estilo Bitcoin):
      - 1 folha   -> a raiz é a própria folha.
      - senão     -> emparelhe e calcule pai = sha256d(esq + dir), subindo
                     nível a nível até sobrar 1 nó.
      - nº ÍMPAR de nós num nível -> DUPLIQUE o último antes de emparelhar.
    Dica: sha256d já está importado.
    """
    raise NotImplementedError("Parte 1: implemente merkle_root")


def merkle_proof(leaves: list[bytes], index: int) -> list[tuple[str, bytes]]:
    """Prova de inclusão da folha em `index`: lista de (lado, hash_do_irmão).

    `lado` é "left" se o irmão fica à esquerda da posição atual, "right" se à
    direita. Há 1 irmão por nível => a prova tem ~log2(n) elementos.
    Use a mesma regra de duplicação do ímpar de merkle_root.
    """
    raise NotImplementedError("Parte 1: implemente merkle_proof")


def verify_proof(leaf: bytes, proof: list[tuple[str, bytes]], root: bytes) -> bool:
    """True se, dobrando `leaf` com os irmãos de `proof`, chega-se em `root`.

    Para cada (lado, irmão): se lado == "left",  h = sha256d(irmão + h);
                             se lado == "right", h = sha256d(h + irmão).
    No fim, compare h com root.
    """
    raise NotImplementedError("Parte 1: implemente verify_proof")
