"""Parte 1 — Árvore de Merkle."""

from minichain import kit
from minichain.crypto import sha256d

A, B, C, D = b"tx0", b"tx1", b"tx2", b"tx3"


def test_single_leaf_root_is_the_leaf():
    """a raiz de uma folha só é a própria folha"""
    assert kit.merkle_root([A]) == A


def test_two_leaves():
    """a raiz de 2 folhas = H(folha0 ‖ folha1)"""
    assert kit.merkle_root([A, B]) == sha256d(A + B)


def test_four_leaves():
    """a raiz de 4 folhas = H( H(a‖b) ‖ H(c‖d) )"""
    assert kit.merkle_root([A, B, C, D]) == sha256d(sha256d(A + B) + sha256d(C + D))


def test_odd_level_duplicates_last():
    """um nível com nº ímpar de nós duplica o último"""
    assert kit.merkle_root([A, B, C]) == sha256d(sha256d(A + B) + sha256d(C + C))


def test_proof_roundtrips_for_every_index():
    """a prova de cada folha verifica contra a raiz"""
    leaves = [A, B, C, D]
    root = kit.merkle_root(leaves)
    for i, leaf in enumerate(leaves):
        assert kit.verify_proof(leaf, kit.merkle_proof(leaves, i), root) is True


def test_proof_has_log2_n_elements():
    """a prova tem log2(n) hashes (8 folhas → 3)"""
    leaves = [b"leaf-%d" % i for i in range(8)]
    assert len(kit.merkle_proof(leaves, 3)) == 3


def test_proof_rejects_wrong_leaf():
    """a prova rejeita uma folha forjada"""
    leaves = [A, B, C, D]
    root = kit.merkle_root(leaves)
    proof = kit.merkle_proof(leaves, 2)
    assert kit.verify_proof(b"forjada", proof, root) is False
