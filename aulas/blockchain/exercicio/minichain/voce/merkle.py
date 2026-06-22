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

    A árvore sobe de baixo para cima, um NÍVEL de cada vez. Um nível é só uma
    lista de hashes: você começa com as folhas (o nível de baixo) e, a cada
    passo, gera o nível de cima com METADE dos nós — até sobrar 1, que é a raiz.

    Para passar de um nível ao de cima:
      - se o nível tem nº ÍMPAR de nós, DUPLIQUE o último (assim fica par);
      - emparelhe os nós lado a lado (0 com 1, 2 com 3, …); o pai de cada par é
        sha256d(esquerdo + direito). A lista dos pais é o próximo nível.

    Com 1 folha só não há o que emparelhar: a raiz é a própria folha.
    Dica: sha256d já está importado; um laço `while len(nivel) > 1` resolve.
    """
    raise NotImplementedError("Parte 1: implemente merkle_root")


def merkle_proof(leaves: list[bytes], index: int) -> list[tuple[str, bytes]]:
    """Prova de inclusão da folha em `index`: lista de (lado, hash_do_irmão).

    Suba os MESMOS níveis de merkle_root, mas guardando, em cada nível, só o
    IRMÃO do nó onde você está (aquele com quem ele se emparelha):
      - posição PAR  -> o irmão está à direita (posição+1): guarde ("right", irmão);
      - posição ÍMPAR-> o irmão está à esquerda (posição-1): guarde ("left", irmão).
    Depois de emparelhar, sua posição no nível de cima vira posição // 2.

    Repita até chegar à raiz, aplicando a mesma duplicação do último quando o
    nível tiver nº ímpar. Resultado: ~log2(n) pares (1 irmão por nível).
    """
    raise NotImplementedError("Parte 1: implemente merkle_proof")


def verify_proof(leaf: bytes, proof: list[tuple[str, bytes]], root: bytes) -> bool:
    """True se, combinando `leaf` com os irmãos de `proof`, chega-se em `root`.

    Comece com h = leaf e, para cada (lado, irmão) da prova, recomponha o pai:
      - lado == "left"  (irmão à esquerda): h = sha256d(irmão + h);
      - lado == "right" (irmão à direita):  h = sha256d(h + irmão).
    No fim, a prova vale se h == root.
    """
    raise NotImplementedError("Parte 1: implemente verify_proof")
