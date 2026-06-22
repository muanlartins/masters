"""Os dois tipos de dado do sistema — JÁ PRONTOS (só os campos; a lógica é sua).

São contêineres de dados puros (dataclasses). A lógica que opera sobre eles
(calcular hash, validar, minerar) é o que você implementa em `minichain/voce/`.
"""

from dataclasses import dataclass, field


@dataclass
class Tx:
    """Uma transação: `sender` paga `amount` para `recipient`, e assina.

    - sender:    chave pública (bytes) de quem envia. b"" significa COINBASE
                 (a transação que cria a recompensa do minerador; não tem
                 remetente nem assinatura).
    - recipient: endereço (bytes) de quem recebe.
    - amount:    inteiro >= 0.
    - signature: preenchida por sign_tx (Parte 2).
    """

    sender: bytes
    recipient: bytes
    amount: int
    signature: bytes = b""


@dataclass
class Block:
    """Um bloco: um cabeçalho de 80 bytes + a lista de transações.

    Campos do cabeçalho (Parte 3): version, prev_hash, merkle_root, timestamp,
    bits, nonce. `txs` é o corpo; `merkle_root` resume `txs` num só hash.
    """

    version: int
    prev_hash: bytes
    txs: list
    timestamp: int
    bits: int
    nonce: int = 0
    merkle_root: bytes = b""
