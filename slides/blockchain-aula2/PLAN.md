# Plano de slides — Aula 2: da moeda ao computador-mundo

Programação Avançada (6º período) · **Aula 2 de 2** · ~2 h · **português**.
Construído sob `PRESENTATION_GUIDE.md` — §1 manda: cada slide de conteúdo =
**um título-frase** (topo, esquerda, declarativo) + **um** artefato visual +
espaço em branco. Sem bullets, sem caixas de texto, sem legenda no slide. O
professor narra tudo que o slide não mostra.

Demos têm roteiro próprio em `aulas/blockchain/`: `demos/remix/README.md`
(counter, escrow, reentrância) e `etherscan/roteiro.md`. A ementa bloco-a-bloco
está em `aulas/blockchain/EMENTA.md` (§ AULA 2).

---

## Frase-tese (a âncora — §2.1.1)

> Um contrato inteligente transforma o livro-razão num **computador-mundo**:
> código que roda sem intermediário e se cumpre sozinho. Isso abre usos novos
> — e bugs novos, gravados pra sempre. Mas a pergunta da Aula 1 continua de pé:
> se existe um terceiro confiável, um banco de dados comum é mais simples.

**Promessa de abertura (≤90 s, §6.1):** *ao fim da aula você vai saber o que um
contrato inteligente realmente é, por que cada passo de código custa gas, como
um bug de uma linha levou a comunidade a bifurcar o Ethereum — e como decidir,
na prática, se você precisa mesmo de blockchain.*

## Framework

Continuação em escada da Aula 1: livro de moedas → máquina de estados replicada
→ contrato (se cumpre sozinho) → o que ele não consegue (oráculo) → o custo
(gas) → ver rodando (Remix) → quando dá errado (reentrância/fork) → existe de
verdade (Etherscan) → e a pergunta de fecho (precisa mesmo?). Cada degrau
sustenta o próximo; o último paga a tese das duas aulas.

## Teste dos títulos sozinhos (§2.1.4 — lidos em sequência, resumem a aula)

livro de moedas → e se guardasse código → conta = estado → todo nó concorda →
contrato se cumpre sozinho → não enxerga fora da rede → cada passo custa gas →
counter → escrow → reentrância → correção de uma linha → imutabilidade bifurca →
Etherscan público → token dentro da chamada → árvore de decisão → três casos →
concordar sem confiar.

---

## Slide a slide

| # | Tipo | Título-frase | Artefato | Espinha da narração |
|---|------|--------------|----------|----------------------|
| 1 | Capa | *Da moeda ao computador-mundo* | texto | Programação Avançada · Aula 2 de 2. Abrir falando, com a promessa. |
| 2 | Divisor | *Recap: o que a Aula 1 deixou pronto* | texto (~5 s) | Em 1 min: hash+assinatura+cadeia+PoW = um livro replicado, sem dono, à prova de adulteração. |
| 3 | Conteúdo | **Na Aula 1, um livro de moedas; e se cada entrada guardasse código?** | `diagram_recap.png` | A virada da aula. O mesmo consenso, mas o que se registra agora pode ser **código**. |
| 4 | Conteúdo | **Uma conta é um estado; uma transação é uma transição de estado** | `diagram_state_machine.png` | Ethereum como máquina de estados: o mundo tem um estado global (saldos, dados dos contratos); a única forma de mudá-lo é uma transação. |
| 5 | Conteúdo | **Todo nó roda o mesmo código e concorda no resultado: um computador-mundo** | `diagram_world_computer.png` | Cada nó executa a mesma transição e chega ao mesmo estado — é o consenso da Aula 1, agora sobre execução de código, não só saldos. |
| 6 | Divisor | *Contratos inteligentes* | texto (~5 s) | O que é, afinal, "código que roda on-chain". |
| 7 | Conteúdo | **Um contrato é código que mora na rede e se cumpre sozinho** | `diagram_vending.png` | (Szabo 1997, a máquina de vending.) A regra está no código: pagou ≥ preço → entrega. Sem caixa, sem confiar no vendedor — a execução é o cumprimento. |
| 8 | Conteúdo | **O que ele não consegue: enxergar qualquer coisa de fora da rede** | `diagram_oracle.png` | Determinismo: todo nó precisa do mesmo resultado, então o contrato não chama API, não sabe o dólar nem o placar. Quem traz isso é um **oráculo** — que volta a ser um ponto de confiança. |
| 9 | Conteúdo | **Cada passo de código custa gas — é o que impede o loop infinito** | `fig_gas.png` | Sem preço, um `while(true)` travaria milhares de nós (problema da parada). Gas = orçamento por transação: paga-se pelo trabalho imposto à rede; sobra vira leilão de taxas. |
| 10 | Divisor | *Mãos à obra: contratos rodando* | texto (~5 s) | Abre o "show de receitas" no Remix VM (sandbox no navegador). |
| 11 | Conteúdo | **Counter: toda escrita é uma transação; toda leitura é de graça** | **DEMO** Remix · backup `diagram_counter.png` | `increment` é tx (laranja, gasta gas, vira bloco); ler `count` é call (azul, grátis); `decrement` em 0 → `require` reverte. |
| 12 | Conteúdo | **Escrow: confiança programável — só o árbitro libera o dinheiro** | **DEMO** Remix · backup `diagram_escrow.png` | `payable`/`msg.value`: o contrato guarda 1 ETH. Comprador deposita; nem ele nem o vendedor mexem — só o árbitro chama `release`. Controle de acesso = `require(msg.sender == arbiter)`. |
| 13 | **Intervalo** | *Intervalo · ~10 min* | texto | Quebra antes do clímax: "na volta, o bug de 60 milhões de dólares". |
| 14 | Divisor | *O bug de 60 milhões de dólares* | texto (~5 s) | The DAO, 2016. Consenso correto ≠ contrato correto. |
| 15 | Conteúdo | **Reentrância: o atacante volta a sacar antes de o saldo zerar** | **DEMO** Remix · `diagram_reentrancy.png` | O `withdraw` envia o ETH **antes** de zerar o saldo; o `receive()` do atacante reentra no `withdraw` e saca de novo, em laço, até esvaziar o cofre. Depositou 1, levou 6. |
| 16 | Conteúdo | **A correção é uma linha: zere o saldo antes de enviar** | `diagram_checks_effects.png` | Checks-effects-interactions: muda o estado **antes** de chamar para fora. A única diferença entre o cofre vulnerável e o seguro é a ordem de duas linhas. |
| 17 | Conteúdo | **Imutabilidade corta dos dois lados: desfazer o roubo exigiu bifurcar a rede** | `diagram_fork.png` | $60M / 3,6M ETH. Como a cadeia é imutável, o roubo ficou gravado; a comunidade bifurcou — daí Ethereum (desfez) e Ethereum Classic ("código é lei", manteve). |
| 18 | Divisor | *Isto existe de verdade, numa rede pública* | texto (~5 s) | Sai do sandbox: Etherscan, sem instalar nada, sem carteira. |
| 19 | Conteúdo | **No Etherscan, o mesmo contrato é público, verificado e permanente** | **DEMO** Etherscan · backup `diagram_etherscan.png` | USDC real: código verificado (cadeado "Exact Match"), `Read Contract` sem carteira, eventos gravados pra sempre. O escrow da aula, em escala de bilhões. |
| 20 | Conteúdo | **Uma transferência de token: 0 ETH movido, milhares de dólares dentro de uma chamada** | **DEMO** Etherscan · `diagram_erc20.png` | A pegadinha: `Value = 0 ETH`, mas a seção de tokens mostra 7.151 USDC. O dinheiro andou **dentro** de uma chamada a `transfer()`; o evento `Transfer` no Log é a fonte de tudo. |
| 21 | Divisor | *Você precisa mesmo de blockchain?* | texto (~5 s) | A reflexão de fecho — sem vender tese. |
| 22 | Conteúdo | **A árvore de decisão de Wüst–Gervais** | `fig_decision_tree.png` | (Wüst–Gervais 2018, redesenhada.) Guarda estado? Múltiplos escritores? Dá pra usar um TTP sempre online? Escritores conhecidos/confiáveis? Verificabilidade pública? → cada folha aponta o que usar. |
| 23 | Conteúdo | **Três casos do dia a dia na mesma árvore** | `diagram_cases.png` | Registro interno (um dono) → banco de dados. Pagar um desconhecido sem intermediário → blockchain pública. Consórcio de partes conhecidas que não confiam 100% → permissionada (ou nem isso). |
| 24 | Conteúdo / **FINAL** | **Blockchain resolve um problema: concordar sem confiar. Havendo confiança, o simples vence.** | `fig_synthesis.png` | **Síntese das duas aulas.** Fica no ar pro Q&A. Fecha o arco e paga a promessa da abertura. |

**24 slides** (capa + 6 divisores + 1 intervalo + 16 conteúdo). 4 segmentos ao
vivo: Remix (counter, escrow, reentrância) + Etherscan. O bloco de reentrância
(14–17) é o clímax; o bloco de fecho (21–24) é a reflexão crítica das duas aulas.

**Intervalo após o slide 12** (depois do escrow), no cliffhanger "o bug de 60
milhões". **Atenção ao tempo (EMENTA ≈106 min + folga):** os blocos conceituais
(3–9) são densos — não apressar contas/oráculo/gas; o Remix (11–12) e o
Etherscan (19–20) são "show de receitas", andam rápido seguindo o roteiro.

## Paleta (§3.4 — objeto → cor, fixa em todas as figuras; herda a da Aula 1)

| Objeto | Cor |
|--------|-----|
| Ethereum / estado / computador-mundo / cadeia | azul `#1f77b4` |
| Contrato / código / "se cumpre sozinho" | verde `#2ca02c` |
| Atacante / bug / reentrância / risco | vermelho `#d62728` |
| Gas / custo | laranja `#ff7f0e` |
| Estrutura neutra / banco de dados comum / texto | cinza `#6b7280` |

## Assets

Gerar via `assets_gen.py` (matplotlib, fontes ≥13 pt, paleta acima):

- **Conceituais:** `diagram_recap` (moeda → código), `diagram_state_machine`
  (estado --tx--> estado'), `diagram_world_computer` (todos os nós, mesmo
  estado), `diagram_vending` (Szabo), `diagram_oracle` (limite + ponto de
  confiança de volta), `fig_gas` (orçamento que esvazia / loop infinito para).
- **Backups de demo:** `diagram_counter`, `diagram_escrow`, `diagram_etherscan`.
- **Bloco reentrância:** `diagram_reentrancy` (laço de reentrada),
  `diagram_checks_effects` (errado×certo lado a lado), `diagram_fork` (ETH/ETC).
- **Etherscan:** `diagram_erc20` (Value 0, token dentro da chamada).
- **Fecho:** `fig_decision_tree` (Wüst–Gervais), `diagram_cases` (3 casos),
  `fig_synthesis` (a tese das duas aulas).

Nas figuras, setas usam `->` ASCII (Helvetica não tem `→`); nas legendas do pptx
o `→` pode ser usado (quem renderiza é o Keynote).

## Build

```bash
venv/bin/python slides/blockchain-aula2/assets_gen.py   # gera as figuras
venv/bin/python slides/blockchain-aula2/build_pptx.py   # -> apresentacao_blockchain_aula2.pptx
```

## Itens em aberto

- Conferir o valor da transferência ERC-20 (USDC) contra a tx do roteiro do
  Etherscan na hora de gerar `diagram_erc20` (hoje: ~7.151 USDC).
- Ensaiar as transições slide↔Remix e slide↔Etherscan — onde a aula mais trava.
- A árvore de decisão (slide 22) era o único `[ ]` do checklist da EMENTA;
  agora gerada aqui. Atualizar o checklist quando o deck for revisado.
