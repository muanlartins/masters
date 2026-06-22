"""Parte 1 — Árvore de Merkle (REFERÊNCIA)."""

from __future__ import annotations

from minichain.crypto import sha256d


def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        raise ValueError("a lista de folhas não pode ser vazia")
    level = leaves
    while len(level) > 1:
        if len(level) % 2 == 1:               # nº ímpar: duplica o último
            level = level + [level[-1]]        # nova lista — não muta a entrada
        level = [sha256d(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def merkle_proof(leaves: list[bytes], index: int) -> list[tuple[str, bytes]]:
    if not 0 <= index < len(leaves):
        raise IndexError("índice fora da lista de folhas")
    proof: list[tuple[str, bytes]] = []
    level, i = leaves, index
    while len(level) > 1:
        if len(level) % 2 == 1:
            level = level + [level[-1]]
        if i % 2 == 0:
            proof.append(("right", level[i + 1]))  # posição par: irmão à direita
        else:
            proof.append(("left", level[i - 1]))   # posição ímpar: irmão à esquerda
        level = [sha256d(level[j] + level[j + 1]) for j in range(0, len(level), 2)]
        i //= 2
    return proof


def verify_proof(leaf: bytes, proof: list[tuple[str, bytes]], root: bytes) -> bool:
    h = leaf
    for side, sibling in proof:
        if side == "left":
            h = sha256d(sibling + h)
        else:
            h = sha256d(h + sibling)
    return h == root
