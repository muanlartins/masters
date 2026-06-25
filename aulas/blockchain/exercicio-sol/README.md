# exercicio-sol — contratos inteligentes, peca por peca

Exercicio da Aula 2. Voce implementa, em `contracts/voce/`, contratos em Solidity
que a aula explicou — de um cofre simples ate uma troca atomica (DvP) — ate os
testes ficarem verdes.

Cada exercicio e **independente**: faca so o que quiser, em qualquer ordem. O que
voce nao fizer continua usando a solucao de referencia (`contracts/gabarito/`),
entao a suite sempre roda inteira.

## Rodar

```bash
./instalar.sh          # uma vez: instala o Hardhat e as dependencias (Node 18+)
./progresso.sh         # painel: o que falta e quantos testes passam
./testar.sh cofre      # testa um exercicio  (sem argumento: testa tudo)
./testar.sh dvp --grep atomico   # filtra por nome do teste
```

## Como fazer

1. Abra o exercicio em `contracts/voce/` (ex.: `voce/Cofre.sol`) e implemente os
   `TODO` (o estado e o construtor ja vem prontos).
2. Rode `./testar.sh cofre` ate passar. O cabecalho de cada arquivo explica os
   conceitos; cada `TODO` diz exatamente o que checar e a mensagem de cada
   `require`.
3. Ligue o exercicio em `config.js` (`"cofre": true`). A partir dai os testes
   daquele exercicio passam a rodar contra o **seu** contrato.

## Os exercicios

| # | `voce/…`          | Implementar                          | Ensina |
|---|-------------------|--------------------------------------|--------|
| 1 | `Cofre.sol`       | `depositar`, `sacar`, `saldo`        | `payable`, `msg.value/sender`, `require`, enviar ETH |
| 2 | `Votacao.sol`     | `votar`, `vencedor`                  | `mapping`, prazo (`block.timestamp`), 1 voto por endereco |
| 3 | `Crowdfunding.sol`| `contribuir`, `sacar`, `reembolsar` | estado + tempo + dinheiro; reembolso (checks-effects-interactions) |
| 4 | `Leilao.sol`      | `darLance`, `retirar`, `encerrar`   | leilao ingles; padrao **pull payment** (cada um saca o seu) |
| 5 | `Moeda.sol`       | `transfer`, `approve`, `transferFrom`| ERC-20 (o mesmo padrao do USDC); allowance; eventos |
| 6 | `DvP.sol`         | `liquidar`, `cancelar`              | entrega-contra-pagamento **atomico** (tudo-ou-nada) |

A dificuldade sobe do 1 ao 6, e o DvP fecha o arco: ele troca um token ERC-20
(exercicio 5) por ETH numa unica transacao atomica. A solucao de referencia
esta em `contracts/gabarito/` — so abra se quiser entregar os pontos.

## Como funciona o "meu vs gabarito"

`config.js` lista cada exercicio com `false` (usa o gabarito) ou `true` (usa o
seu). Os testes instanciam o contrato pelo caminho que `kit.js` resolve a partir
desse arquivo — voce nao precisa mexer em `kit.js`. Com tudo em `false` (padrao),
`./testar.sh` ja fica verde: e a prova de que os testes e a referencia sao reais.

> Os contratos das **demos** da aula (counter, escrow, reentrancia) estao em
> `../demos/remix/` e rodam no Remix VM, sem instalar nada. Estes exercicios sao
> a parte "maos a obra" com testes automatizados.
