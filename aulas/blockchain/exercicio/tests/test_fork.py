"""Parte 6 — Cadeia mais longa / desempate entre forks."""

from minichain import kit, build
from minichain.crypto import gen_keys
from minichain.types import Tx


def _signed(amount=1):
    sk, vk = gen_keys()
    tx = Tx(sender=vk.to_string(), recipient=b"x", amount=amount)
    kit.sign_tx(tx, sk)
    return tx


def _chain(n_extra):
    chain = build.genesis(bits=8)
    for _ in range(n_extra):
        build.append(chain, [_signed()], bits=8)
    return chain


def test_chain_work_sums_difficulty():
    chain = build.genesis(bits=8)
    assert kit.chain_work(chain) == 2 ** 8
    build.append(chain, [_signed()], bits=8)
    assert kit.chain_work(chain) == 2 * 2 ** 8


def test_best_chain_picks_more_accumulated_work():
    short, long = _chain(1), _chain(3)
    assert kit.best_chain([short, long]) is long


def test_best_chain_ignores_invalid_chains():
    good = _chain(1)
    bad = _chain(1)
    bad[1].prev_hash = b"\x00" * 32   # quebra o elo -> cadeia inválida
    assert kit.best_chain([bad, good]) is good
