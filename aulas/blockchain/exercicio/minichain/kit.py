"""Resolvedor: para cada função, devolve a SUA versão ou a do GABARITO.

NÃO precisa mexer aqui. Toda peça do sistema chama as outras através do `kit`
(ex.: o PoW faz `kit.block_hash(...)`), então a escolha "minha vs gabarito"
de `config.py` vale automaticamente em todo lugar — inclusive dentro do seu
próprio código.
"""

import importlib

from minichain import config

# nome da função pública -> parte a que ela pertence
_PART_OF = {
    "merkle_root": "merkle", "merkle_proof": "merkle", "verify_proof": "merkle",
    "payload": "tx", "txid": "tx", "sign_tx": "tx", "tx_is_valid": "tx",
    "compute_merkle": "block", "header_bytes": "block", "block_hash": "block",
    "meets_target": "pow", "mine": "pow",
    "validate_block": "chain", "is_valid_chain": "chain",
    "chain_work": "fork", "best_chain": "fork",
}

# parte -> módulo (todos têm o mesmo nome em gabarito/ e voce/)
_MODULE_OF = {
    "merkle": "merkle", "tx": "tx", "block": "block",
    "pow": "pow", "chain": "chain", "fork": "fork",
}

_cache = {}


def _resolve(fname):
    part = _PART_OF[fname]
    use_mine = config.MINHA[part]
    key = (fname, use_mine)
    if key not in _cache:
        pkg = "voce" if use_mine else "gabarito"
        mod = importlib.import_module(f"minichain.{pkg}.{_MODULE_OF[part]}")
        _cache[key] = getattr(mod, fname)
    return _cache[key]


def __getattr__(name):
    # PEP 562: resolve kit.<funcao> dinamicamente conforme config.MINHA
    if name in _PART_OF:
        return _resolve(name)
    raise AttributeError(f"module 'minichain.kit' has no attribute {name!r}")
