# Demos Remix — Aula 2 (smart contracts)

Tudo aqui roda no **Remix VM** (sandbox no navegador). Modo "show de
receitas": os contratos já estão prontos; em aula você só segue os passos.

---

## O que é o Remix / Remix VM

- **Remix** = IDE no navegador: <https://remix.ethereum.org>. **Não instala
  nada.**
- **Remix VM** = uma blockchain de mentira embutida no próprio navegador.
  Deploy instantâneo, **10 contas com 100 ETH falsos**, sem MetaMask, sem
  faucet, sem internet para o deploy. **Tudo reseta ao recarregar a página.**
- A parte "isto é real e público" da aula é feita **no Etherscan**, separado
  (ver `../../etherscan/`) — não precisamos de testnet aqui.

## Setup (1 minuto, faça antes da aula)

1. Abra <https://remix.ethereum.org>.
2. **File Explorer** (ícone de arquivos, canto sup. esquerdo): arraste os
   `.sol` desta pasta para dentro, ou crie um arquivo novo e cole o conteúdo.
3. Aba **Solidity Compiler**: deixe a versão **0.8.x** e clique **Compile**
   (ou ative *Auto compile*).
4. Aba **Deploy & Run Transactions**: em **Environment**, escolha
   **"Remix VM (Cancun)"**. As 10 contas aparecem no topo.

## Como ler a interface (o que apontar em aula)

- **Account** (dropdown) = quem está enviando a transação (o `msg.sender`).
  Trocar de conta = trocar de "usuário".
- **Value** + unidade (Wei / Gwei / **Ether**) = quanto ETH a transação leva
  junto (`msg.value`). **Sempre confira a unidade** antes de clicar.
- **Botão laranja** = transação (muda estado, gasta gas). **Botão azul** =
  *call* (só lê estado, de graça).
- **Terminal** (embaixo) = log de cada transação: gas usado, eventos, e os
  **reverts** (quando um `require` falha).

---

## Receita 1 — Counter (aquecimento, ~4 min)

**Conceito:** estado on-chain; transação vs. leitura; gas; revert.

1. Compile `01_counter.sol`. Deploy **Counter**.
2. Abra o contrato em *Deployed Contracts*. Clique **count** (azul) → `0`.
3. Clique **increment** 3×. Clique **count** → `3`.
   - *Falar:* cada `increment` foi uma **transação** (apareceu no terminal,
     gastou gas); ler `count` é **grátis** (azul, não vira bloco).
4. Clique **decrement** com count em 0 → **revert** "count ja esta em zero".
   - *Falar:* `require` é a trava; transação revertida não altera nada (mas
     gasta o gas até falhar).

---

## Receita 2 — Escrow (~6 min)

**Conceito:** confiança programável; `payable`/`msg.value`; controle de acesso.

Use 3 contas (copie os endereços do topo):
`account[0]` = **comprador**, `account[1]` = **vendedor**, `account[2]` = **árbitro**.

1. Compile `02_escrow.sol`.
2. Com **account[0]** selecionada, no campo do construtor preencha
   `_seller = account[1]`, `_arbiter = account[2]` → **Deploy**.
3. Ainda como **account[0]**: **Value = 1 Ether** → clique **deposit**.
   - *Falar:* o contrato agora **guarda** 1 ETH; o saldo de account[0] caiu.
4. Tente **release** como account[0] → **revert** "somente o arbitro".
   - *Falar:* nem comprador nem vendedor mexe no dinheiro; só o árbitro decide.
5. Troque para **account[2]** (árbitro) → clique **release** → o **vendedor**
   (account[1]) recebe 1 ETH (veja o saldo subir no topo).
6. *(Opcional)* Refaça o deploy e mostre o caminho **refund** (devolve ao
   comprador).

---

## Receita 3 — Reentrancy: o bug da The DAO (a estrela, ~15 min)

**Conceito:** consenso correto ≠ contrato correto; imutabilidade corta dos
dois lados (foi o que causou o fork ETH/ETC em 2016). Arquivo: `03_reentrancy.sol`.

### Parte A — o ataque

1. Compile `03_reentrancy.sol` (os 3 contratos vão aparecer no dropdown).
2. Como **account[0]**, deploy **VulnerableBank**.
3. Encha o "cofre" (dinheiro de outras vítimas): como **account[0]**,
   **Value = 5 Ether** → **deposit**. Clique **getBalance** → `5000000000000000000`
   (5 ETH).
4. Troque para **account[9]** (o atacante). Deploy **Attacker** passando
   `_bank =` **endereço da VulnerableBank** (copie no ícone de cópia do
   contrato deployado).
5. Como **account[9]**: **Value = 1 Ether** → clique **attack**.
6. Mostre o estrago:
   - **VulnerableBank → getBalance** = `0`.
   - **Attacker → getBalance** = `6 ETH` (depositou 1, levou 6).
   - *Falar:* o `receive()` do atacante **re-entrou** no `withdraw` várias
     vezes **antes** de o saldo ser zerado — sacou 1 ETH por vez até esvaziar.
7. Como **account[9]**, clique **collect** → os 6 ETH vão para a conta dona.

### Parte B — a correção (uma linha)

8. Como **account[0]**, deploy **SafeBank**. Encha igual: **Value = 5 Ether**
   → **deposit**.
9. Como **account[9]**, deploy um **novo Attacker** apontando para o endereço
   da **SafeBank**.
10. Como **account[9]**: **Value = 1 Ether** → **attack** → a transação
    **REVERTE** ("falha no envio"). **SafeBank → getBalance** continua `5 ETH`.
    Nada roubado.
11. Mostre lado a lado os dois `withdraw` no código: a **única** diferença é a
    **ordem** — zerar o saldo **antes** de enviar (checks-effects-interactions).

> *Gancho:* "$60M / 3,6M ETH sumiram assim em 2016. Como a blockchain é
> imutável, o roubo ficou gravado pra sempre — a comunidade teve que
> **bifurcar a rede** pra desfazer. É daí que vêm o Ethereum e o Ethereum
> Classic." → leva ao fecho "você precisa mesmo de blockchain?".
