# Roteiro — Guerreiros Bizantinos (Aula 1, ~12 min)

**Objetivo:** fazer a turma *sentir* o problema do consenso (concordar sem
confiar em ninguém) e abrir o caminho para o proof of work.

**Por que é seguro fazer ao vivo:** é **pré-encenado**. Cada voluntário
recebe um cartão dizendo exatamente o que falar (ver
`cartoes-para-imprimir.md`). O resultado é garantido — você só conduz e narra.

---

## 0. Conceito (você explica antes — ~2 min)

- N generais cercam uma cidade. Só vencem se **todos atacarem juntos** (ou
  todos recuarem). Se metade ataca e metade recua, o exército dividido é
  destruído. A decisão *qual* importa menos que **estarem todos de acordo**.
- Eles só se falam por **mensageiro**. O problema: alguns generais podem ser
  **traidores**, mandando mensagens conflitantes de propósito.
- **A pergunta:** dá pra garantir que todos os generais *leais* cheguem à
  **mesma** decisão, mesmo com traidores no meio?

## 1. Montagem (~1 min)

- 3 voluntários à frente, em "cantos" separados: **1 Comandante**, **2 Tenentes**
  (T1 e T2).
- Entregue os cartões. **Não revele quem é o traidor.**
- Resto da turma = observadores. Use o quadro pra anotar o que cada um recebe.

## 2. Cena 1 — o comandante dá a ordem (~3 min)

- O **Comandante** lê o cartão e passa a ordem para cada tenente.
  *(No cartão dele — traidor — está escrito: "ATACAR" para T1, "RECUAR" para T2.)*
- Anote no quadro: **T1 recebeu ATACAR · T2 recebeu RECUAR**.
- **Falar:** "Os dois tenentes são leais e vão obedecer. T1 ataca, T2 recua.
  Metade do exército ataca sozinha → destruída. O traidor venceu sem dar um tiro."

## 3. Cena 2 — "então é só comparar as ordens!" (~3 min)

- Provoque a turma: "como resolver? Deixa os tenentes conversarem entre si."
- T1 e T2 trocam o que ouviram (está nos cartões):
  - **T1:** "O comandante me disse **ATACAR**."
  - **T2:** "O comandante me disse **RECUAR**."
- Agora cada tenente tem uma **contradição**. Pergunte ao T1:
  *"Quem está mentindo — o comandante ou o T2?"*
- **Ponto-chave (o coração da aula):** T1 **não tem como saber**. Do ponto de
  vista dele, dois mundos são **idênticos**:
  - **(a)** o comandante é traidor e mandou ordens diferentes; **ou**
  - **(b)** o comandante é leal (mandou ATACAR pra todos) e **o T2** é o
    traidor, mentindo que ouviu RECUAR.
  - Mesmas mensagens chegando, dois culpados possíveis → **nenhuma regra
    decide certo nos dois casos ao mesmo tempo.**

## 4. O resultado (~2 min)

- Com **3 generais, 1 único traidor já quebra tudo.**
- Teorema (Lamport, Shostak, Pease, 1982): para tolerar **f** traidores você
  precisa de pelo menos **3f + 1** generais — ou seja, **mais de 2/3 leais**.
- Esse "2/3" reaparece em **todo** protocolo BFT até hoje — e na finalidade do
  Ethereum em Proof of Stake.

## 5. A ponte para o Bitcoin (~1 min — o gancho)

- O Bitcoin **não confia em general nenhum.** A sacada do Nakamoto: tornar
  "mandar uma ordem" **caro** (proof of work).
- Você não consegue fingir ser mil generais de graça (ataque **Sybil**), e
  todo mundo obedece à cadeia com **mais trabalho acumulado**.
- → emenda direto no próximo bloco: **proof of work / consenso de Nakamoto.**

---

### Variação opcional (se sobrar tempo / turma engajada)

Rode a Cena 1 de novo com o **2º jogo de cartões** (`cartoes-para-imprimir.md`),
onde **o traidor é o T2** (não o comandante). T1 leal vai receber *exatamente
as mesmas mensagens* da Cena 2 original — provando ao vivo que os dois mundos
são indistinguíveis. Pule se a turma já entendeu pela narração.
