# Roteiro — Etherscan ao vivo (Aula 2, ~10 min)

**Objetivo:** depois dos contratos no Remix VM (sandbox de mentira), mostrar
que **isto existe de verdade, numa rede pública e permanente** — código
verificado, eventos reais, gas real, e um livro-razão que qualquer um lê.

**Sem instalar nada, sem carteira:** ver qualquer coisa no Etherscan é aberto.
Carteira só é preciso para *escrever* (enviar transação) — a gente não vai
fazer isso.

---

## Pré-aula: deixe estas abas abertas e fixadas (fallback se a rede cair)

| # | Aba | URL |
|---|-----|-----|
| 1 | Contrato USDC (código) | `https://etherscan.io/address/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48#code` |
| 2 | Token USDC | `https://etherscan.io/token/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` |
| 3 | Transferência ERC-20 (a pegadinha) | `https://etherscan.io/tx/0xd02ac758c45847ab20482cb43c867dd802b722bed84b3804a24450f12f39700e` |
| 4 | 1ª transação de ETH da história | `https://etherscan.io/tx/0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060` |
| 5 | Endereço do Vitalik | `https://etherscan.io/address/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` |

> **Risco de rede:** o Etherscan tem proteção anti-bot (Cloudflare/captcha) que
> pode aparecer se a rede do campus for por VPN/datacenter — raro em Wi-Fi
> normal. Mitigação: **pré-carregar as abas acima antes da aula** e não ficar
> recarregando. Tudo abaixo funciona deslogado.

---

## 1. O contrato por trás da moeda (~3 min) — aba 1

- Abra o **#code** do USDC. *Falar:* "Lembram do escrow que a gente escreveu?
  Aqui está um contrato **real**, que move bilhões de dólares. O código está
  **aberto e verificado** — o cadeado verde 'Exact Match' diz que o que roda na
  rede é exatamente este código-fonte."
- Mostre a aba **Read Contract**: chame `totalSupply` ou `balanceOf` — **lê o
  estado on-chain sem carteira nenhuma**. *Falar:* "Qualquer um consulta o
  estado; transparência é o default."
- *Aviso pra você não se perder:* o USDC é um **proxy**, então aparecem tabs
  extras "Read/Write **as Proxy**" (leem a implementação real). Se alguém
  perguntar: é um padrão de atualização de contrato; ignore por ora.

## 2. Uma transferência de verdade + os eventos (~3 min) — aba 3

- Abra a transação ERC-20. **A pegadinha:** lá em cima **Value = 0 ETH**...
  mas na seção **"ERC-20 Tokens Transferred"** aparece **7.151,36 USDC**
  movidos. *Falar:* "Nenhum ETH nativo se moveu. O dinheiro andou **dentro de
  uma chamada à função `transfer()` do contrato**."
- O "To" da transação é o **próprio contrato do USDC**, não o destinatário — o
  destinatário real está na seção de tokens. Bom momento pra desfazer a
  confusão "pra quem foi?".
- Abra a tab **Logs**: lá está o **evento `Transfer`** (from, to, amount).
  *Falar:* "Lembram que no Remix cada ação virava um evento no terminal? Aqui é
  o mesmo `Transfer`, só que **gravado pra sempre** num bloco. O resuminho
  bonito lá de cima o Etherscan reconstrói a partir **deste log**."

## 3. Gas real (~2 min) — aba 4

- Abra a **1ª transação de ETH da história** (bloco 46147, agosto de 2015).
  *Falar:* "Está aqui há mais de 10 anos e não sai mais."
- Aponte os campos: **From / To / Value**, e o bloco de **gas**: Gas Limit,
  Gas Used (21.000 = a assinatura de um envio puro de ETH), Gas Price (gwei),
  **Transaction Fee**, Status, Block, Timestamp. Conecte com o conceito de gas
  da Aula 2: "computar/mover custa, e o preço é um leilão."
- *Aviso:* essa página antiga renderiza a taxa de um jeito estranho ("1.05
  ETH"); se preferir números limpos, pegue **uma transação recente ao vivo**
  (abra o último bloco na home → uma linha com Gas Used 21.000 e Value > 0).

## 4. O livro-razão é público (~2 min) — aba 5

- Digite `vitalik.eth` na busca → resolve pro endereço dele. *Falar:* "Não tem
  login, não tem permissão. Qualquer endereço é uma janela aberta."
- Mostre: saldo de ETH, **centenas de tokens** (dropdown Token Holdings),
  coleções de **NFT**, e o **histórico completo** de transações.
- *Gancho de transição para o fecho:* "Isto é o ponto forte — auditável,
  transparente, sem dono. E também o ponto fraco: **tudo** é público, pra
  sempre. Então... você precisa *mesmo* de uma blockchain pra tudo?"
  → emenda na reflexão final da aula.

---

### Caminho alternativo 100% ao vivo (se quiser "acontecendo agora")

Abra o contrato do USDC (aba 1) → tab **Transactions** → clique numa linha
recente. Quase toda transferência de USDC já te dá a pegadinha do §2 (Value 0,
tokens movidos, evento no Logs), com data de hoje. Robusto em qualquer data.
