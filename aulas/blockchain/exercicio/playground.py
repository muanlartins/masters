#!/usr/bin/env python3
"""Passeio visual pela mini-blockchain. Rode:  python playground.py

Não vale nota — é para você VER as peças funcionando juntas: minerar, encadear,
adulterar e ver a cadeia quebrar, e provar uma transação com Merkle. Funciona com
o gabarito; conforme você liga suas partes em config.py, passa a usar o seu código.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from minichain import kit, build, config            # noqa: E402
from minichain.crypto import gen_keys, to_hex        # noqa: E402
from minichain.types import Tx                       # noqa: E402

H = to_hex


def short(b):
    return H(b)[:12] + "…"


def pagar(remetente_sk, remetente_vk, para, quanto):
    tx = Tx(sender=remetente_vk.to_string(), recipient=para, amount=quanto)
    kit.sign_tx(tx, remetente_sk)
    return tx


def main():
    ligadas = [k for k, v in config.MINHA.items() if v] or ["(nenhuma — tudo gabarito)"]
    print(f"\nPeças usando o SEU código: {', '.join(ligadas)}\n")

    sk, vk = gen_keys()

    print("1) Minerando uma cadeia de 3 blocos (alvo: 8 zeros)…")
    chain = build.genesis(bits=8)
    build.append(chain, [pagar(sk, vk, b"bob", 10)], bits=8)
    build.append(chain, [pagar(sk, vk, b"carol", 7)], bits=8)
    for i, b in enumerate(chain):
        print(f"   bloco {i}: hash={short(kit.block_hash(b))}  "
              f"prev={short(b.prev_hash)}  nonce={b.nonce}  txs={len(b.txs)}")
    print(f"   cadeia válida? {kit.is_valid_chain(chain)}   "
          f"trabalho acumulado={kit.chain_work(chain)}\n")

    print("2) Adulterando o valor de uma transação do bloco 1…")
    chain[1].txs[0].amount = 999_999
    print(f"   cadeia válida agora? {kit.is_valid_chain(chain)}   "
          "(raiz de Merkle e assinatura não batem mais)\n")

    print("3) Prova de Merkle: provar que uma tx está num bloco sem o bloco inteiro.")
    txs = [pagar(sk, vk, who, 1) for who in (b"a", b"b", b"c", b"d")]
    folhas = [kit.txid(t) for t in txs]
    raiz = kit.merkle_root(folhas)
    prova = kit.merkle_proof(folhas, 2)
    print(f"   raiz do bloco: {short(raiz)}")
    print(f"   prova p/ a tx #2: {len(prova)} hash(es) "
          f"(em vez das {len(txs)} transações)")
    print(f"   verifica? {kit.verify_proof(folhas[2], prova, raiz)}\n")


if __name__ == "__main__":
    main()
