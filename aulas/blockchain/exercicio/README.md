# minichain — construa uma mini-blockchain, peça por peça

Exercício da Aula 1. Você implementa, em `minichain/voce/`, as peças que a aula
explicou — Merkle, assinatura de transações, cabeçalho, mineração (PoW),
encadeamento e cadeia mais longa — até os testes ficarem verdes.

É **opcional e modular**: faça só o que quiser, em qualquer ordem. O que você não
fizer usa a solução de referência, então o sistema sempre roda inteiro.

## Rodar

```bash
./instalar.sh         # uma vez: cria a venv e instala as dependências
./progresso.sh        # painel: o que falta e quantos testes passam
./testar.sh merkle    # testa uma parte, teste a teste  (sem argumento: testa tudo)
./simulacao.sh        # passeio narrado: vê cada peça rodando com os valores reais
```

## Como fazer

1. Abra a parte em `minichain/voce/` (ex.: `voce/merkle.py`) e implemente os `TODO`.
2. Rode `./testar.sh merkle` até passar.
3. Ligue a parte em `minichain/config.py` (`"merkle": True`). A partir daí o
   sistema inteiro passa a usar o **seu** código — inclusive dentro das outras
   peças (seu Merkle entra na sua mineração, etc.).

## As partes

| # | `voce/…`    | Implementar                              |
|---|-------------|------------------------------------------|
| 1 | `merkle.py` | `merkle_root`, `merkle_proof`, `verify_proof` |
| 2 | `tx.py`     | `payload`, `txid`, `sign_tx`, `tx_is_valid`   |
| 3 | `block.py`  | `compute_merkle`, `header_bytes`, `block_hash`|
| 4 | `pow.py`    | `meets_target`, `mine`                        |
| 5 | `chain.py`  | `validate_block`, `is_valid_chain`            |
| 6 | `fork.py`   | `chain_work`, `best_chain`                    |

A criptografia de base (hash, assinatura) já está pronta em `minichain/crypto.py`.
A solução de referência está em `minichain/gabarito/` — só abra se quiser
entregar os pontos.
