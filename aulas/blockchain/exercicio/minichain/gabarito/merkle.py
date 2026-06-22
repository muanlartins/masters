"""Parte 1 — Árvore de Merkle (REFERÊNCIA)."""

from minichain.crypto import sha256d


def merkle_root(leaves):
    if not leaves:
        raise ValueError("a lista de folhas não pode ser vazia")
    level = list(leaves)
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])  # nº ímpar: duplica o último
        level = [sha256d(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def merkle_proof(leaves, index):
    if not 0 <= index < len(leaves):
        raise IndexError("índice fora da lista de folhas")
    proof = []
    level = list(leaves)
    i = index
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        if i % 2 == 0:
            proof.append(("right", level[i + 1]))  # irmão à direita
        else:
            proof.append(("left", level[i - 1]))    # irmão à esquerda
        level = [sha256d(level[j] + level[j + 1]) for j in range(0, len(level), 2)]
        i //= 2
    return proof


def verify_proof(leaf, proof, root):
    h = leaf
    for side, sibling in proof:
        if side == "left":
            h = sha256d(sibling + h)
        else:
            h = sha256d(h + sibling)
    return h == root
