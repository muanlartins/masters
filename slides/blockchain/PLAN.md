# Plano de slides — Aula 1: por que blockchain existe

Programação Avançada (6º período) · **Aula 1 de 2** · ~2 h · **português**.
Construído sob `PRESENTATION_GUIDE.md` — §1 manda: cada slide de conteúdo =
**um título-frase** (topo, esquerda, declarativo) + **um** artefato visual +
espaço em branco. Sem bullets, sem caixas de texto, sem legenda no slide. O
professor narra tudo que o slide não mostra.

Demos e roleplay têm roteiro próprio em `aulas/blockchain/`:
`anders-demo/roteiro.md` e `generais-bizantinos/`.

---

## Frase-tese (a âncora — §2.1.1)

> Blockchain resolve **um** problema: concordar sobre um livro-razão
> compartilhado entre desconhecidos que não confiam uns nos outros e não têm
> autoridade central. Todas as peças (hash, assinatura, cadeia) já existiam; o
> que o Bitcoin inventou em 2008 foi **juntá-las num consenso de membro aberto**
> — e isso custa caro, então nem sempre vale a pena.

**Promessa de abertura (≤90 s, §6.1):** *ao fim da aula você vai saber qual foi
a única coisa que o Bitcoin realmente inventou — e por que, sem ela, um banco de
dados comum é mais simples.*

## Framework

Motivação-primeiro (§2.1.2), narrativa em escada: gasto-duplo → livro
distribuído → as peças de cripto → encadeamento → o problema do consenso → a
resposta (PoW) → o custo. Cada degrau sustenta o próximo.

## Teste dos títulos sozinhos (§2.1.4 — lidos em sequência, resumem a aula)

arquivo se copia → banco recria o dono → livro distribuído → hash → assinatura →
encadeamento → mineração → em quem confiar (3f+1) → PoW → Merkle → cabeçalho 80 B →
hash < alvo → ~10 min → cadeia mais longa → refazer o trabalho → não inventou, juntou →
custa um país → 7 tx/s → e se guardar código?

---

## Slide a slide

| # | Tipo | Título-frase | Artefato | Espinha da narração |
|---|------|--------------|----------|----------------------|
| 1 | Capa | *Blockchain, do zero: por que ela existe* | texto | Programação Avançada · Aula 1 de 2. Abrir falando, com a promessa. |
| 2 | Conteúdo | **Dinheiro digital é só um arquivo — e arquivo se copia** | `diagram_double_spend.png` | Mandar um arquivo é copiar, não mover. Eu pago a mesma "moeda" pra duas pessoas (gasto-duplo). Sem ninguém no meio, como impedir? |
| 3 | Conteúdo | **Um banco resolve isso — e te devolve um dono no meio** | `diagram_central_ledger.png` | Um livro-razão central mata o gasto-duplo na hora. Preço: ponto único de confiança, censura e falha. Pode bloquear, errar, cair. |
| 4 | Conteúdo | **Tira o banco: todo mundo guarda uma cópia do livro** | `diagram_distributed_ledger.png` | Replicar o livro em todos remove o dono. Novo problema: milhares de cópias — **como concordam** sobre o que entrou? |
| 5 | Divisor | *Antes, duas peças de criptografia* | texto (~5 s) | Skippável se a turma já viu. Hash e assinatura são o tijolo de tudo. |
| 6 | Conteúdo | **Um hash é uma impressão digital de mão única** | **DEMO ao vivo** (Anders /hash) · backup `diagram_hash.png` | Determinístico, imprevisível, irreversível. Digite, mude 1 letra, avalanche. "Dá pra rodar ao contrário?" Não → segura a mineração. |
| 7 | Conteúdo | **Uma assinatura digital prova quem autorizou** | **DEMO ao vivo** (Anders /signatures) · backup `diagram_signature.png` | Chave privada assina, pública verifica. Sign → assinatura; Verify → verde; muda 1 letra → vermelho. Ninguém forja sem o segredo; ninguém precisa do segredo pra conferir. É o que autoriza uma transação. |
| 8 | Divisor | *Do hash à cadeia* | texto (~5 s) | Agora encadeia. |
| 9 | Conteúdo | **Encadear pelo hash do anterior torna a fraude evidente** | **DEMO ao vivo** (Anders /blockchain) · backup `diagram_hashchain.png` | Edite o bloco 2 → 2–5 ficam vermelhos. Cada bloco aponta pro anterior; mexeu em um, quebra todos os seguintes. |
| 10 | Conteúdo | **Minerar é achar um número que faça o hash começar com zeros** | **DEMO ao vivo** (Anders /block, botão Mine) | Força bruta de nonce, sem atalho. Esse trabalho é o que vai custar energia. |
| 11 | Divisor | *Quem escolhe o próximo bloco?* | texto (~5 s) | Várias cópias, ninguém no comando. |
| 12 | Conteúdo | **Num bando de desconhecidos, em quem você confia?** | **ROLEPLAY** Generais Bizantinos · backup `diagram_generals.png` | Funde o antigo 12+13. Roda a cena (cartões): o traidor conta versões diferentes pra cada um; os leais ouvem ordens opostas e não concordam. Conclusão na legenda: precisa de >2/3 honestos (3f+1) — esse "2/3" volta no PoS. |
| 13 | **Intervalo** | *Intervalo · ~10 min* | texto | Quebra logo após o roleplay, no cliffhanger do consenso. Teaser: "na volta, a resposta de 2008". |
| 14 | Divisor | *A resposta de 2008* | texto (~5 s) | O Nakamoto não confia em general nenhum. |
| 15 | Conteúdo | **Proof of work: tornar "votar" caro a ponto de não dar pra fingir** | `diagram_sybil_pow.png` | A sacada conceitual: identidades são de graça (Sybil) → voto por identidade não vale. Voto por **trabalho** (energia) não dá pra forjar de graça. |
| 16 | Divisor | *Abrindo o capô: as peças, por dentro* | texto (~5 s) | Abre o **bloco técnico** (pós-intervalo): como o Bitcoin funciona de verdade, peça por peça, ao longo da timeline. |
| 17 | Conteúdo | **A árvore de Merkle prova que uma transação está no bloco** | `fig_merkle.png` | (Merkle 1980.) A raiz (no header, lacrada pela mineração) compromete todas as txs; a carteira leve recompõe a raiz a partir de `tx₂` + os irmãos do caminho (`h₃, h₀₁`) e compara — sem ver as outras txs. Prova = 1 irmão por nível = `log₂(n)` hashes (~12 p/ ~4000 txs ≈ 400 B). SPV / carteira leve. |
| 18 | Conteúdo | **O cabeçalho de 80 bytes é o que se faz hash — e é o que encadeia** | `fig_header.png` | (Haber–Stornetta 1991.) Os 6 campos; `hash = SHA256²(header)`; esse hash vira o `prev` do próximo bloco. Refina formalmente o slide 9. |
| 19 | Conteúdo | **Minerar é achar um cabeçalho cujo hash caia abaixo de um alvo** | `fig_pow_target.png` · **retoma Anders /block** | (Hashcash 1997.) A regra real: `SHA256²(header) < T`; em média `≈ 2²⁵⁶/T` tentativas. É o "0000" do slide 10, formalizado — sem atalho. |
| 20 | Conteúdo | **A dificuldade se reajusta para manter ~10 min por bloco** | `fig_difficulty.png` | Retarget a cada 2016 blocos: `T_novo = T_velho·(Δt_real/2 sem)`, limitado ×¼..×4. Responde tecnicamente "por que 10 minutos". |
| 21 | Conteúdo | **Vence a cadeia com mais trabalho acumulado** | **DEMO ao vivo** (Anders /distributed) · backup `diagram_longest_chain.png` | Adultere o peer A → diverge. Desempate objetivo: a história com mais `Σ` trabalho. O consenso de Nakamoto, na prática. |
| 22 | Conteúdo | **Reescrever a história significa refazer todo o trabalho** | `fig_security.png` | Clímax técnico (§11 do whitepaper). Ruína do apostador: `P ≈ (q/p)^z`, cai exponencial com a profundidade `z` → daí "6 confirmações". |
| 23 | Conteúdo | **O Bitcoin não inventou as peças — inventou juntá-las** | `fig_timeline.png` | **Síntese** (agora um *inventário*, não linha de datas). Esquerda = peças reaproveitadas com origem: hash · assinatura · Merkle (1980) · cadeia de hashes = **Haber-Stornetta 1991** · PoW = **Hashcash 1997** · a visão de moeda PoW = **b-money/bit gold 1998**. Direita = a única peça nova: **consenso de membro aberto** = PoW-como-voto + cadeia mais longa + incentivo. Concordar entre desconhecidos anônimos, sem cadastro/autoridade — o que o BFT clássico (3f+1) só fazia com elenco fixo. Fecha o arco dos generais + paga a promessa da abertura. |
| 24 | Divisor | *Quanto custa esse consenso?* | texto (~5 s) | Nada disso é de graça. |
| 25 | Conteúdo | **Esse consenso gasta a eletricidade de um país inteiro** | `fig_energy.png` | Bitcoin ~150 TWh/ano (CBECI), na faixa de Argentina/Polônia. O preço da resistência a Sybil. |
| 26 | Conteúdo | **E faz ~7 transações por segundo, não 65 mil** | `fig_tps.png` | Bitcoin ~7, Ethereum ~15–30, Visa ~1.700 (pico ~65 mil). O teto de escala do design. |
| 27 | Conteúdo / **FINAL** | **Construímos um livro de moedas. E se ele guardasse código?** | `diagram_bridge.png` | Fica no ar pro Q&A. Semente do "quando é exagero?" + gancho da Aula 2 (smart contracts). |

**27 slides** (capa + 6 divisores + 1 intervalo + 19 conteúdo). 6 segmentos ao
vivo (Anders ×5: hash, assinaturas, blockchain, block, distributed + roleplay);
o bloco técnico (17–23) reusa as abas Block/Distributed para ancorar as fórmulas.

**Bloco técnico (16–23) — adicionado a pedido:** a 2ª metade estava magra; este
bloco abre o Bitcoin peça por peça ao longo da timeline (Merkle → cabeçalho →
PoW → dificuldade → cadeia mais longa → segurança), com a fórmula como o próprio
artefato visual e a prosa na legenda editável. Profundidade entre média e
completa: fórmula suficiente pra ver o mecanismo de forma correta, sem
tecnicalidade gratuita.

**Intervalo após o slide 12** (roleplay): a turma quebra no cliffhanger do
consenso e volta na "resposta de 2008". **Atenção ao tempo:** o bloco técnico
adiciona ~20 min densos, então a 2ª metade sobe pra ~50 min; com o bloco cripto
(slides 5–7, skippável) a aula inteira passa de 2 h. Plano: o bloco técnico é a
prioridade nova; o bloco cripto vira o ajuste de tempo (skippa total/parcial
lendo a turma). Se quiser reequilibrar as metades, o intervalo ainda pode ir
pra depois do slide 10.

## Paleta (§3.4 — objeto → cor, fixa em todas as figuras)

| Objeto | Cor |
|--------|-----|
| Cadeia / Bitcoin / "a resposta" | azul `#1f77b4` |
| Autoridade central / risco | vermelho `#d62728` |
| Rede honesta / distribuída | verde `#2ca02c` |
| Traidor / atacante / gasto-duplo | vermelho `#d62728` |
| Energia / custo | laranja `#ff7f0e` |
| Estrutura neutra / texto | cinza `#6b7280` |

## Assets

Gerar via `assets_gen.py` (matplotlib, fontes ≥14 pt, paleta acima):

- **Diagramas:** `diagram_double_spend`, `diagram_central_ledger`,
  `diagram_distributed_ledger`, `diagram_signature`, `diagram_byzantine_3f1`,
  `diagram_sybil_pow`, `diagram_longest_chain`, `diagram_bridge`.
- **Linha do tempo:** `fig_timeline` (1980 Merkle · 1991 Haber–Stornetta ·
  1992/1997 PoW/hashcash · 1998 b-money/bit gold · 2008 Bitcoin).
- **Bloco técnico (fórmula = artefato; mathtext):** `fig_merkle` (árvore +
  prova de inclusão O(log n)), `fig_header` (cabeçalho 80 B → SHA256² → elo),
  `fig_pow_target` (reta dos hashes, `H < T`, `≈ 2²⁵⁶/T`), `fig_difficulty`
  (loop de retarget, `T_novo`), `fig_security` (ruína do apostador `(q/p)^z`).
  Nas figuras, setas usam `->` ASCII (Helvetica não tem `→`); nas legendas do
  pptx o `→` pode ser usado (quem renderiza é o Keynote).
- **Dados (com fonte no rodapé da figura):** `fig_energy` (Bitcoin ~150 TWh/ano
  vs países — CBECI), `fig_tps` (BTC ~7 · ETH ~15–30 · Visa ~1.700/~65 mil).
- **Backups opcionais** (slides de demo ao vivo): `diagram_hash`, `diagram_hashchain`.

## Build

```bash
venv/bin/python slides/blockchain/assets_gen.py   # gera as figuras
venv/bin/python slides/blockchain/build_pptx.py   # -> apresentacao_blockchain_aula1.pptx
```

## Itens em aberto

- Conferir os números de energia/TPS contra a fonte na hora de gerar (ordem de
  grandeza; rotular "fonte: CBECI" / "estimativas" na figura).
- Ensaiar as transições slide↔navegador (Anders) — onde a aula mais pode travar.
