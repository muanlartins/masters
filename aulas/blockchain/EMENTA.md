# Ementa — Introdução a Blockchain (2 aulas)

**Data:** 2026-06-21 · **Disciplina:** Programação Avançada (graduação, 6º período)
**Turma:** maioria já estagia/trabalha como dev · **Formato:** 2 aulas de 2 h

Material de apoio às aulas vive aqui (`aulas/blockchain/`). Os **slides**
serão construídos depois em `slides/blockchain/`, seguindo o
`PRESENTATION_GUIDE.md` (slide = âncora visual; o autor narra por cima).

---

## Princípios destas aulas (restrições do autor)

1. **Demo simples, conceito fundo.** Tudo que se mostra/faz é simples e
   **já pré-pronto** (modo "show de receitas": as etapas já estão
   prontas, só se executa). A profundidade está na *narração* — cripto e
   consenso explicados com rigor; a demo é só a âncora visual.
2. **Não apressar.** Melhor cobrir menos com calma do que encaixar tudo.
   Cronograma com intervalo e folga embutidos.
3. **Aula introdutória, não vitrine de pesquisa.** Nada de teardown da
   tese / "recriação de blockchain sem blockchain". O "quando não usar"
   entra leve, como reflexão geral.
4. **Interativo e visual** > sintaxe. Histórias (generais bizantinos),
   demos ao vivo (adulterar e ver ficar vermelho), Etherscan real.
5. **Zero live-coding.** Contratos escritos e testados de antemão.

---

## Frase-tese (o arco das duas aulas)

> Blockchain resolve **um** problema específico: concordar sobre um
> registro compartilhado entre partes que não confiam umas nas outras e
> não têm autoridade central, num ambiente adversarial. Toda a maquinaria
> (hash, mineração, gas) existe a serviço disso. Quando há um terceiro
> confiável, ou as partes confiam entre si, coisas mais simples resolvem.

- **Aula 1 — o *porquê*:** do hash ao consenso. Por que blockchain existe.
- **Aula 2 — o *como* (e um *quando não* leve):** da moeda ao
  "computador-mundo"; smart contracts; uma reflexão final sobre quando
  vale a pena.

---

## AULA 1 — Por que blockchain existe (mecânica + consenso)

| Bloco | min | Demo / interativo (pré-pronto) | Profundidade do conceito |
|---|---|---|---|
| **Hook + motivação** — dinheiro digital sem banco; o problema do gasto-duplo | 12 | 1 diagrama (banco central vs. ledger distribuído) | médio — motiva a pergunta |
| **[SKIPPÁVEL] Fundamentos cripto** — hash (mão-única, determinístico, efeito avalanche) + assinatura digital (chave pública/privada) | 18 | **Anders demo — aba Hash** ao vivo: digita, vê o hash mudar; muda 1 letra → hash totalmente diferente | **alto** — bem fundamentado; é a base de tudo |
| **Do hash à cadeia** — bloco, mineração (achar nonce), encadeamento; adulterar quebra a cadeia | 18 | **Anders demo — Block + Blockchain**: editar bloco 2 → blocos 2–5 ficam vermelhos; re-minerar "conserta" | **alto** — encadeamento = evidência de adulteração |
| **O problema do consenso** — como concordar sem confiar em ninguém? | 15 | **Generais Bizantinos — roleplay simples** (traidor manda ordens opostas: os leais não concordam) | alto — só o suficiente p/ *sentir* o problema |
| *intervalo* | 10 | logo após o roleplay — quebra no cliffhanger do consenso | |
| **A resposta de Nakamoto** — PoW dispensa conhecer/confiar nos generais (resistência a Sybil); 1 unidade de trabalho = 1 voto | 8 | — (a sacada conceitual; abre o bloco técnico) | alto — a sacada de 2008 |
| **Por dentro do Bitcoin (técnico)** — como funciona de verdade, peça por peça ao longo da timeline: árvore de Merkle, cabeçalho de 80 B + encadeamento, PoW (`hash < alvo`), dificuldade/retarget (~10 min), cadeia mais longa, segurança (ruína do apostador `(q/p)^z`) | 22 | **Anders — Block/Distributed** reusados p/ ancorar as fórmulas | **alto** — fórmula só o suficiente p/ ver o mecanismo de forma correta |
| **Trade-offs honestos** — energia, throughput; gancho "e quando isto é exagero?" | 12 | 1–2 slides de dados (energia, TPS) | médio |
| **Fecho → Aula 2** — "demos um ledger de moedas; e se ele guardasse *código*?" | 5 | — | — |

*O bloco técnico ("por dentro do Bitcoin") adensa a 2ª metade a pedido. Com ele
a aula passa de 2 h se o **bloco cripto** (skippável) também for dado — esse é o
ajuste de tempo: skippa total/parcial lendo a turma. Sem apressar o técnico.*

---

## AULA 2 — Da moeda ao computador-mundo (smart contracts)

| Bloco | min | Demo / interativo (pré-pronto) | Profundidade do conceito |
|---|---|---|---|
| **Recap + a virada** — ledger de moeda → **máquina de estados replicada** (Ethereum = "computador-mundo"); contas; transação = transição de estado | 12 | 1 diagrama | alto — liga ao consenso da Aula 1 |
| **Smart contracts** — código que roda on-chain, execução sem intermediário; pra que servem; o que **não** conseguem (problema do oráculo) | 15 | exemplo da máquina de vending (Szabo) | **alto** — o conceito central |
| **Gas** — por que computar custa dinheiro (anti-DoS / parada / mercado de taxas) | 8 | — | alto — um "porquê" elegante |
| **Remix VM — "show de receitas"** — contratos prontos, executados passo a passo | 18 | **counter** (toda escrita é uma tx) + **escrow** (`payable`, `require`, confiança programável) | médio — narrar o fluxo, não a sintaxe |
| *intervalo* | 10 | | |
| **The DAO / reentrancy** — exploit **pré-encenado** + o conserto; imutabilidade corta dos dois lados (fork ETH/ETC) | 18 | par vítima+atacante pré-pronto no Remix VM; drenar e consertar | alto — história + a lição |
| **Etherscan** — real, público, permanente | 10 | abrir contrato/tx **já existente** (ex.: token conhecido): hash, gas, eventos | médio |
| **"Você precisa mesmo de blockchain?"** — reflexão simples e geral | 10 | árvore de decisão (Wüst–Gervais) + 2–3 casos do dia a dia | médio — crítico, **sem vender tese** |
| **Fecho** | 5 | slide-síntese fica visível no Q&A | — |

*≈106 min + folga. Sem live-coding: você conduz etapas prontas.*

---

## Material a pré-preparar (checklist)

Organizado por artefato; cada um terá seu lugar nesta pasta. Os **slides**
ficam de fora (vão para `slides/blockchain/` depois).

### Aula 1
- [ ] **Anders Brownworth demo** — self-host (Docker, repo `anders94/blockchain-demo`)
      como backup offline (wifi de campus é o ponto de falha #1). Testar abas
      Hash / Block / Blockchain / Distributed. Opcional: subir a dificuldade
      p/ a mineração não ser instantânea. → `aulas/blockchain/demos/anders/`
- [x] **Roleplay Generais Bizantinos** — roteiro (`roteiro.md`) + cartões
      pré-escritos para imprimir (`cartoes-para-imprimir.md`), determinístico.
      → `aulas/blockchain/generais-bizantinos/`
- [ ] **Diagramas** — (a) banco central vs. ledger distribuído; (b) gasto-duplo.
      Construir em código (casa com o estilo dos slides). → `assets/`
- [ ] **Slides de dados** — energia (Cambridge CBECI, comparações) e TPS
      (Visa vs BTC vs ETH). → gerar no notebook depois.

### Aula 2
- [x] **Contratos Remix** — `01_counter.sol`, `02_escrow.sol`,
      `03_reentrancy.sol` (VulnerableBank + SafeBank + Attacker). Escritos e
      **compilados** (solc 0.8.26, sem erros). Falta só o dry-run no Remix VM.
      → `aulas/blockchain/demos/remix/`
- [x] **Roteiro de execução** ("receita" de cada demo, passo a passo).
      → `aulas/blockchain/demos/remix/README.md`
- [x] **Etherscan** — roteiro com URLs reais e verificadas (USDC, tx ERC-20,
      1ª tx de ETH, vitalik.eth) + caminho ao vivo. → `aulas/blockchain/etherscan/roteiro.md`
- [ ] **Árvore de decisão "preciso de blockchain?"** — redesenhar a figura
      Wüst–Gervais (não screenshot do paper) + 2–3 cartões de caso. → `assets/`

---

## Referências de apoio (para fundamentar a narração — não para a aula)

Só o núcleo; verificadas. Ficam aqui pro autor estudar antes.

- **Consenso:** Lamport-Shostak-Pease 1982 (Generais Bizantinos) · Castro-Liskov 1999 (PBFT) · Douceur 2002 (ataque Sybil).
- **Fundamentos:** Merkle 1980 · Haber-Stornetta 1991 (timestamping, o ancestral do encadeamento) · Nakamoto 2008.
- **Contratos:** Szabo 1997 · Buterin 2014 (whitepaper) · Wood 2014 (yellow paper, gas) · Daian 2016 (DAO/reentrancy).
- **Quando (não) usar:** Wüst-Gervais 2018 ("Do you Need a Blockchain?", a árvore de decisão).

---

## Ordem de construção sugerida (próximos passos)

1. **Contratos Remix** (counter, escrow, par reentrancy + correção) — o que
   dá mais trabalho e mais risco; fazer e testar primeiro.
2. **Roteiro de execução** de cada demo Remix + URLs do Etherscan.
3. **Roleplay dos generais** (roteiro + cartões).
4. **Diagramas e árvore de decisão** (figuras em código).
5. Self-host do Anders demo + testes.
6. Só então: slides em `slides/blockchain/`.
