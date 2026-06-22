# Roteiro — Simulador Anders Brownworth (Aula 1)

**URLs (duas páginas do mesmo autor):**
- Cadeia: <https://andersbrownworth.com/blockchain/> — abas **Hash → Block →
  Blockchain → Distributed** (slides 6, 10, 9, 21). A aba **Block** é retomada
  no slide 19 p/ ancorar a desigualdade `hash < alvo` do bloco técnico.
- Chaves: <https://andersbrownworth.com/blockchain/public-private-keys/signatures>
  — menu **Keys · Signatures · Transaction** (slide 7).

A superfície de demo da Aula 1. Você dirige; a turma pode abrir no laptop e
adulterar junto (opcional). Ordem na aula: **Hash → Assinaturas → (cadeia)**.

---

## Pré-aula (faça antes — Wi-Fi de campus é o risco #1)

- Teste as quatro abas da cadeia **e** a página de assinaturas no navegador que
  vai usar em aula.
- **Backup offline (recomendado):** rode local, caso a rede caia.
  ```bash
  git clone https://github.com/anders94/blockchain-demo
  cd blockchain-demo && npm install && npm start   # serve em localhost:3000
  ```
- *Opcional:* em laptops rápidos a mineração é quase instantânea. Se quiser que
  ela "demore" um pouco (mais dramático), aumente o número de zeros do alvo em
  `public/javascripts/*` na cópia local.
- Deixe as 4 abas abertas em janelas/abas separadas, na ordem.

## Como ler a interface

- Campo **Hash** fica **verde** quando válido (começa com a quantidade de zeros
  exigida) e **vermelho** quando inválido.
- Botão **Mine** procura um **Nonce** que torne o hash válido (força bruta).
- "Prev" = o hash do bloco anterior (é o que **encadeia**).

---

## Segmento A — Hash (aba **Hash**) — abre o bloco de cripto

1. Digite qualquer coisa no campo **Data** → o hash aparece embaixo, mudando a
   cada tecla.
2. Mude **uma** letra → o hash inteiro muda (efeito avalanche).
3. *Falar:* hash = **impressão digital de mão única**. É **determinístico**
   (mesmo texto → mesmo hash), **imprevisível** (muda 1 bit → muda tudo) e
   **irreversível** (não dá pra voltar do hash pro texto). Pergunte: *"dá pra
   rodar isso ao contrário?"* → não → é por isso que minerar é tentativa e erro.

## Segmento A·2 — Assinaturas (página de chaves) — slide 7

**URL:** <https://andersbrownworth.com/blockchain/public-private-keys/signatures>
Mesmo autor, outra página (menu **Keys · Signatures · Transaction**). A ideia:
**assina-se com a chave privada; confere-se com a pública**.

1. *(opcional, ~10 s)* Abra **Keys**: uma **chave privada** gera uma **chave
   pública**. Gere outra → o par muda junto. *Falar:* a pública é **derivada** da
   privada; você divulga a pública e guarda a privada em segredo.
2. **Sign**: digite uma **mensagem** (ex.: `pago 5 ao Bob`) + a **chave privada**
   → **Sign** → sai a **assinatura** (um blocão hex). *Falar:* só quem tem a
   privada consegue produzir essa assinatura **para essa mensagem**.
3. **Verify**: o lado Verify já vem com **mensagem + chave pública + assinatura**.
   Clique **Verify** → campo fica **verde** = válida. *Falar:* qualquer um confere
   com a **pública**, sem nunca precisar do segredo.
4. **A sacada — adultere:** mude **uma letra** da mensagem (ou troque a chave) e
   **Verify** de novo → fica **vermelho**. *Falar:* a assinatura prova **duas**
   coisas de uma vez — **quem** autorizou (só a privada assina) e que a mensagem
   **não mudou** (1 bit diferente → inválida). É exatamente o que autoriza uma
   transação na blockchain.

> Emenda no slide 6: a assinatura é feita **sobre o hash** da mensagem — por isso
> 1 letra muda tudo (efeito avalanche). Hash + assinatura = o tijolo da próxima
> parte (a cadeia).

---

## Segmento B — Block (aba **Block**) — o que é minerar

1. Mostre os campos: Block, **Nonce**, Data, **Hash**. Digite algo em Data → o
   hash fica **vermelho** (não começa com `0000`).
2. Clique **Mine** → ele varre nonces até o hash ficar **verde**.
3. *Falar:* minerar é só **"chutar um número até o hash bater no alvo"**. Não
   tem atalho — você não consegue calcular o nonce, só testar. **Esse trabalho
   é o que custa energia** (volta nisso no fim da aula).

## Segmento C — Blockchain (aba **Blockchain**) — encadeamento

1. Cinco blocos; cada um carrega em **Prev** o hash do anterior.
2. **Edite o Data do bloco 2** → os blocos **2, 3, 4 e 5 ficam vermelhos** de
   uma vez.
3. *Falar:* mexeu em um bloco, **todos os seguintes quebram** — porque cada um
   depende do hash do anterior. Adulteração vira **evidente**.
4. Clique **Mine** no bloco 2 → ele fica verde, mas **3, 4 e 5 continuam
   vermelhos**. *Falar:* pra "consertar" a fraude você teria que **re-minerar
   todos** — caro de propósito. É aqui que mora a imutabilidade.

## Segmento D — Distributed (aba **Distributed**) — abre o consenso

1. Três peers (A, B, C), cada um com a cadeia inteira, todos verdes/iguais.
2. Adultere um bloco no **peer A** e re-minere → o peer A **diverge** dos outros.
3. *Falar:* agora há **duas versões da história**. Sem banco central, **quem
   está certo?** A regra do Bitcoin: vale a cadeia com **mais trabalho
   acumulado** (a mais longa). → emenda no proof of work / Nakamoto.

> O Segmento D fecha o **bloco técnico** (slide 21, "cadeia mais longa"): depois
> do roleplay + intervalo + as peças por dentro (Merkle, cabeçalho, PoW,
> dificuldade), o Distributed mostra a regra de desempate na prática — vence a
> história com mais trabalho acumulado.
