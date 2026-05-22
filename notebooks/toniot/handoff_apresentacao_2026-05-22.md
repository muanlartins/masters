# Hand-off — Roteiro de apresentação T1 (TON_IoT)

Destinatário: **Claude Desktop**, que vai redigir a prosa dos slides
e o relatório técnico a partir desse documento.

Esse hand-off é **autocontido** — você não precisa abrir os
notebooks pra escrever o esqueleto, mas todos os pointers estão aqui
caso queira verificar um número ou puxar uma figura.

> **Convenção de nome do trabalho**: 6 alunos do mestrado, cada um
> ficou com um modelo da família WNN; um deles é o "coringa"
> (consolidador). Em qualquer artefato público (tabelas, legendas,
> nomes de colunas), **usar tag técnica do modelo/variante** —
> nunca o nome da pessoa. Ex: `wisard`, `cluswisard_purepython`,
> `bthowen_colab`, `bloomwisard_reference`.

---

## 0. Contexto do trabalho em 1 parágrafo

T1 da disciplina, prazo ~junho/2026. **Tarefa**: detecção de anomalia
em telemetria de IoT usando a **família WiSARD** de redes neurais
sem peso (Weightless Neural Networks). Dataset: **TON_IoT**
(UNSW Canberra Cyber), 7 subbases de telemetria (Fridge, GPS_Tracker,
Garage_Door, Motion_Light, Modbus, Thermostat, Weather), com
~31-40 k linhas cada e 2-4 features. Cada integrante implementou
**um modelo WNN**: WiSARD, ClusWiSARD, BloomWiSARD, BTHOWeN, ULEEN.
Cada um rodou um sweep grande (até **2 688 configs por modelo**) sobre
um grid comum de termômetros × tamanhos × address sizes; o coringa
fez merge num único notebook comparativo. **Entrega**: apresentação
~12-15 slides + relatório técnico.

## 1. Onde está cada coisa (mapa do repo)

```
notebooks/toniot/
  PLANO.md                       # source of truth: métricas, grid, schema, ordem
  01_eda_telemetry.ipynb         # EDA com 40+ cells — TUDO sobre o dataset
  02_reference_implementations.ipynb  # gabarito do coringa (5 modelos, full grid)
  03_analise_comparativa.ipynb   # consolidação cross-model — produto principal
  sweep_utils.py                 # loader unificado (2 schemas, .json e .jsonl)
  handoff_apresentacao_2026-05-22.md   # ESTE doc
  handoff_entregas_2026-05-22.md       # status das entregas
  results/
    {wisard,cluswisard,bloomwisard,uleen}/        # entregas
    bthowen/{colab,vscode}/                       # 2 runs da mesma pessoa
    _reference/{wisard,...,uleen}/                # gabarito local
  _entregas/<modelo>/            # sidecars: SESSAO.md, notebook fonte, PNGs
data/toniot/
  Train_Test_IoT_*.csv           # 7 CSVs (não comitados)
```

**Para puxar a "fonte canônica de verdade" de um número**:
- métrica de modelo → `03_analise_comparativa.ipynb` §3 (binário) / §6 (multi).
- estatística de base/feature → `01_eda_telemetry.ipynb` §2-§8.
- decisão metodológica → `PLANO.md`.
- código de uma figura → buscar pelo título no notebook
  (`grep "Pareto" 03_analise_comparativa.ipynb`).

---

## 2. Estudo do dataset — achados pra apresentação

### 2.1 Visão geral das 7 bases

| Base         |     n |  % attack | # features | tipos de ataque |
|--------------|------:|----------:|----------:|----------------:|
| Fridge       | 39 944 |     62.4% | 2 (1 num+1 cat) | 7 |
| Garage_Door  | 39 587 |     62.1% | 2 (1 num+1 cat) | 8 |
| Motion_Light | 39 488 |     62.0% | 2 (1 num+1 cat) | 8 |
| GPS_Tracker  | 38 960 |     61.5% | 2 (lat, long) | 8 |
| Weather      | 39 260 |     61.8% | 3 (temp, pressure, humidity) | 8 |
| Thermostat   | 32 774 |     54.2% | 2 (temp, status) | 7 |
| Modbus       | 31 106 |     51.8% | 4 (registros raw do protocolo) | 6 |

**Pontos pra apresentação**:
- Datasets são **desbalanceados a favor de `attack`** — classe
  majoritária é "ataque" (52-62%), não "normal". Importante porque
  inverte a intuição comum de "anomalia = minoria".
- Bases têm **6-8 tipos de ataque** distintos (DDoS, scanning,
  injection, ransomware, backdoor, XSS, password, MITM) — daí ter
  tarefa multi-classe além da binária.
- **Riqueza de feature é o eixo dominante de dificuldade**.
  Modbus (4 features) e Weather (3) > GPS_Tracker (2) > Fridge,
  Garage_Door, Motion_Light, Thermostat (2 cada, mas baixíssima
  associação com o label).

### 2.2 Achado crucial: **estrutura temporal**

Os dados foram coletados **sequencialmente** — primeiro um bloco de
normal, depois ataque por ataque. Se você split-ar por tempo, o
modelo aprende "depois do timestamp X é ataque", o que é trapaça.
**Por isso usamos split estratificado por `type`, não temporal.**

(Mais detalhe em `01_eda_telemetry.ipynb` §5.)

### 2.3 Achado crucial: **espectro informacional das features**

Análise via **Cramér's V** (associação categórica feature × label)
revela 3 regimes (notebook `03` §7):

| Tier | Bases | Cramér's V máx | F1 atingível | Comentário |
|------|-------|---------------:|-------------:|------------|
| 🟢 forte    | GPS_Tracker, Weather       | 0.57-0.77 | 0.88-0.89 | sinal visível em univariado |
| 🟡→🟢 interações | **Modbus**            | 0.04      | **0.91**  | sinal vive em combinação 4-feature |
| 🟠 fraco    | Fridge, Thermostat, Motion_Light | 0.005-0.020 | 0.50-0.52 | teto baixo independente de modelo |
| 🔴 ruído    | Garage_Door                | 0.000     | 0.45      | feature ≡ label estatisticamente independentes |

**Por que isso é um achado e não trivialidade**: o BTHOWeN colab chegar
a F1=0.45 em Garage_Door **parecia** "ruim mas razoável" até a gente
calcular o **piso da classe majoritária** (sempre prever 1) = F1
macro = 0.38. O modelo está a +0.07 do piso — ou seja, **no chão**.
Lição metodológica: reportar piso majoritário sempre.

### 2.4 Termômetros — a parte interessante de encoding

WNNs leem entrada binária. Feature numérica vira ~`size` bits via
**termômetro**: 4 variantes na nossa fork de `wisardpkg`:

- **Simple** — thresholds equiespaçados entre min e max.
- **Distributive** — thresholds nos quantis (1/size, 2/size, ...).
- **Gaussian** — thresholds na CDF inversa de N(μ, σ) ajustada à coluna.
- **Exponential** — thresholds na CDF inversa exponencial (cauda longa).

(Visual lado-a-lado: notebook `01` §9.1.)

Feature categórica vira one-hot (`cat_bits = ceil(log2(n_classes))`,
mas na prática usamos one-hot completo nas 4-8 categorias).

---

## 3. Métricas — quais e por quê

### 3.1 Qualidade

| Métrica | Quando usar | Por quê |
|---------|-------------|---------|
| **Acurácia** | Sanity check apenas | Engana em desbalanceamento |
| **F1 macro** | **Principal** (binário e multi) | Honesta no desbalanceamento; cada classe pesa igual; bem-definida em multi-classe |
| **F1 weighted** | Companion da macro | Pondera por frequência — útil pra comparar com baseline da classe majoritária |
| **AUC OvR** | Principal pra multi-classe | Mede separabilidade *antes* do threshold; sobrevive em casos onde o argmax colapsa |
| **Matriz de confusão** | Diagnóstico qualitativo | Mostra *qual* ataque o modelo confunde com qual |

**Por que F1 macro acima de tudo**: classe majoritária (`attack`)
domina ~60% dos dados. Acurácia premia chutar `attack` sempre
(score 60%); F1 weighted parcialmente também. F1 macro é o único
que penaliza isso de verdade — sempre prever 1 dá F1 macro =
0.34-0.38, o "piso" da §2.3.

**Por que AUC OvR no multi-classe**: em Modbus multi-classe, a
BTHOWeN tem F1=0.29 mas AUC=0.70 — o modelo *rankeia* certo, só
não decide bem com argmax. Reportar os dois evita conclusão errada
de "multi-classe não funciona".

### 3.2 Custo

| Métrica | Valor reportado |
|---------|-----------------|
| **Memória serializada (bytes)** | Pickle/JSON do modelo treinado. **Eixo da Pareto.** |
| **Memória teórica (bytes)** | Σ RAMs × entradas × tamanho_voto. Escala teórica pra HW embarcado. **Caveat: bugada em BTHOWeN (=0 quando bleach colapsa). Reportar só `serialized`.** |
| **Tempo de treino (s)** | Wall clock, single-core. **Não comparável cross-machine.** |
| **Latência de inferência (µs/sample)** | Mediana de 50 batch-1 inferences. Importante pra IoT edge. |

**Caveat tempo cross-machine**: 3 ambientes diferentes (Colab Xeon,
Ryzen 7 local, pure-Python). Reportamos como **ordem-de-grandeza**
marcando o ambiente — não como número comparável direto.

---

## 4. Abordagem de ML

### 4.1 Pipeline (idêntico pra todos os modelos)

```
CSV → clean_df → split estratificado(seed=0, 70/30, stratify=type)
    → encode_dataset(termômetro nas numéricas + one-hot nas categóricas)
    → fit(X_train, y_train) → predict(X_test)
    → métricas (qualidade + custo)
```

- **Split**: 70/30 estratificado por **`type`** (não por `label`) pra
  garantir que cada classe de ataque apareça em treino e teste.
  `random_state=0` em todas as rodadas (decisão alinhada com o grupo:
  multi-seed média não compensa o custo no T1).
- **Encoding cache**: as encodings (X_train_bin, X_test_bin) são
  cacheadas por `(base, thermo_kind, size)` pra acelerar o sweep.
- **Skipped configs**: se `addressSize > input_bits` (várias bases
  pobres geram 2-5 bits totais), a config é skipada com
  `skipped=True, reason="addressSize > input_bits"`. Não erro.

### 4.2 Modelos (5)

| Modelo | Característica | Hiperparâmetros extras |
|--------|----------------|------------------------|
| **WiSARD** | Baseline clássico; n-tupla → RAMs → voto | `bleaching` ∈ {off, on} |
| **ClusWiSARD** | Discriminadores se subdividem em sub-clusters | `min_score`, `threshold`, `discriminators_limit` |
| **BloomWiSARD** | RAMs substituídas por Bloom filters (memória ↓↓) | `hash_mode` ∈ {murmur, simhash, h3}; `num_hashes`, `filter_size` |
| **BTHOWeN** | Bloom filters + ranqueamento de bits + bleaching otimizado | `filter_entries` ∈ {16, 64, 256, 1024}; `filter_hashes` ∈ {2, 3, 5, 7}; `bleach_value` ajustado |
| **ULEEN** | Treino por gradiente; multi-submodelo com dropout | `n_submodels`, `epochs`, `learning_rate=0.01`, `dropout_p` |

### 4.3 Grid de hiperparâmetros comuns (PLANO §3.1)

- **Termômetro**: Simple, Distributive, Gaussian, Exponential (4)
- **Tamanho do termômetro**: {2, 4, 8, 16, 32, 64} (6)
- **Tamanho do endereço (address size)**: {4, 8, 12, 16, 20, 24, 28, 32} (8)
- **Produto**: 4 × 6 × 8 = **192 configs** × 14 (base × task) = **2 688 por modelo**

**Cobertura efetiva** (algumas entregas usaram grid reduzido por
budget de tempo):

| Modelo       | Configs entregues | Cobertura vs ideal |
|--------------|-------------------:|-------------------:|
| WiSARD       | 5 376  | 100% (full grid) |
| BloomWiSARD  | 4 032 (entrega) + 10 752 (ref) | parcial entrega, full ref |
| ClusWiSARD   | 172 (entrega) + 336 (ref) | grid muito reduzido (pure-Python lento) |
| BTHOWeN      | 672 (colab) + 3 024 (vscode) + 4 032 (ref) | dois runs complementares |
| ULEEN        | 1 008 (entrega v2) + 224 (ref) | grid expandido em 2026-05-22 (2 thermos × 3 sizes × 3 addrs × 2 epochs) |

---

## 5. Resultados

### 5.1 Headline — vencedores por base (binário)

| Base         | Modelo vencedor | F1 | Memória |
|--------------|-----------------|---:|--------:|
| Fridge       | BTHOWeN (ref)   | 0.516 | — (bug) |
| GPS_Tracker  | BTHOWeN (colab) | 0.877 | 23 KB |
| Garage_Door  | BTHOWeN/ULEEN   | 0.450 | 5 KB |
| **Modbus**   | **WiSARD**      | **0.913** | 474 KB |
| Motion_Light | BTHOWeN/ULEEN   | 0.505 | 5 KB |
| Thermostat   | BloomWiSARD     | 0.512 | **104 B** |
| **Weather**  | **WiSARD**      | **0.885** | 131 KB |

### 5.2 Achados esperados

- **Bases ricas dão F1 ≈ 0.88-0.91**, bases pobres saturam em 0.45-0.52
  — limite informacional, não capacidade dos modelos.
- **Multi-classe colapsa nas 4 bases pobres** (F1 ≈ 0.07-0.14),
  sobrevive em Weather (0.83), Modbus (0.83), GPS_Tracker (0.43).
- **Termômetro `Distributive` e `Gaussian`** dominam nas features
  contínuas; `Simple` aparece como ótimo nas categóricas/quase-binárias.
- **BTHOWeN com filtros grandes** (`filter_entries=1024`) acerta bem
  no Pareto médio.

### 5.3 Achados inesperados (os destaques pra apresentação)

1. **WiSARD clássico vence Modbus e Weather binário** — bate todas
   as variantes sofisticadas. F1 = 0.913 (Modbus), 0.885 (Weather).
   *Insight*: pra esses datasets simples, sofisticação arquitetural
   não ajuda; o que importa é grid grande de termômetros + addressSize
   alto (32).

2. **Modbus: lift +0.572 com Cramér's V univariado = 0.04**.
   Aparente paradoxo: nenhuma feature sozinha discrimina, mas
   combinação de 4 features em n-tupla grande sim. **Testemunha
   forte do valor da família WNN** pra dados de protocolo de baixo
   nível. Curva: F1 vs addressSize sobe de 0.69 (addr=16) pra 0.91
   (addr=32).

3. **BloomWiSARD com 104 bytes** vence Thermostat e fica em F1 ≈
   0.85 em Weather/GPS_Tracker. **4-5 ordens de magnitude abaixo**
   dos competidores em memória. Caso pra deploy embarcado.

4. **Garage_Door tem features estatisticamente independentes do
   label** (Cramér's V = 0.000). Nenhum modelo IID consegue passar
   do piso. Não é bug, é teoria informacional.

5. **Hipóteses descartadas**:
   - Features temporais (hora, dia da semana) **não ajudam** nas
     bases pobres — testado.
   - `addressSize` menor **também não ajuda** nas bases pobres —
     o gargalo é informação no input, não capacidade do modelo.

### 5.4 Validação cruzada — entrega × gabarito

(Detalhes em `03_analise_comparativa.ipynb` §8.2.)

- **WiSARD**: Δ ≤ ±0.03 — implementação do integrante **validada
  com confiança alta**.
- **BTHOWeN**: Δ ≤ ±0.06 — validada.
- **BloomWiSARD**: Δ ≤ ±0.09 — pure-Python validada; gaps explicáveis
  pelo grid menor.
- **ULEEN**: Δ ≤ ±0.20 — maior dispersão; causa estocasticidade do
  SGD + grids diferentes de épocas. Reportar ambos lado a lado.
- **ClusWiSARD**: gap esperado; pure-Python tem perfil de
  memória/tempo não-comparável.

---

## 6. Menu de visualizações

A **obrigatória** pelo PLANO.md: **Pareto F1 × memória** (gráfico
principal) e **matrizes de confusão** dos 2-3 melhores. O resto é
menu aberto — abaixo, organizado por capítulo da apresentação, com
ponteiros pro código fonte.

### 6.1 Dataset (slides 2-4)

| Viz | O que mostra | Fonte |
|-----|--------------|-------|
| **V1. Tabela 7-bases** | n, % attack, # features, # attack types | §2.1 acima |
| **V2. Bar horizontal: % attack por base** | Visualiza desbalanceamento | `01_eda` §4.1 (já tem) |
| **V3. Heatmap base × tipo de ataque** | Quais ataques aparecem em quais bases (log-scale) | `01_eda` §4.2 (já tem) |
| **V4. Histogramas por feature numérica** | Sobreposição normal (azul) × attack (vermelho), 1 por base | `01_eda` §6.1 (já tem; 7 figs) |
| **V5. Scatter de pares de features** | Onde duas features numéricas separam classes | `01_eda` §7 (já tem) |
| **V6. Bar: Cramér's V máx por base** | Resume "qualidade do sinal por base", cores por tier 🟢🟠🔴 | §2.3; código em `03` §7.1 |
| **V7. Comparação visual de termômetros lado-a-lado** | 4 termômetros × 2 features (uma simétrica, uma skewed) | `01_eda` §9.1 (já tem) |

**Sugestão de slide**: usar V1 + V2 + V3 num slide só ("visão geral"),
e V6 num slide isolado ("nem todas as bases são iguais — espectro
informacional").

### 6.2 Pipeline & abordagem (slides 5-7)

| Viz | O que mostra | Fonte |
|-----|--------------|-------|
| **V8. Diagrama de pipeline** | CSV → clean → split → encode (termômetro) → fit → metrics. ASCII ou figura. | desenhar |
| **V9. Cobertura de grid (heatmap thermoSize × addressSize)** | Verde onde rodou, vermelho onde skipou, por base | `01_eda` §9.3 (já tem) |
| **V10. Tabela 5 modelos + hiperparâmetros extras** | §4.2 acima | esta seção |

### 6.3 Resultados — Pareto (slides 8-9, **destaque**)

| Viz | O que mostra | Fonte |
|-----|--------------|-------|
| **V11. Pareto F1 × memória (binário, cross-model)** | **GRÁFICO PRINCIPAL.** Scatter + fronteira por modelo (5 cores). X log. | `03` §4 (já tem, cell `b2863b2e`) |
| **V12. Pareto por base** | Small multiples 2×4 com fronteira por base | `03` §4.1 (já tem, cell `92884991`) |
| **V13. Bar grouped: best F1 por base × modelo** | 5 modelos × 7 bases = 35 barras agrupadas; destaca vencedor | construir a partir de `best_per_base(df, 'f1_macro')` |

**Recomendação**: V11 + V12 num slide "Pareto", V13 num slide
"Vencedor por base" (numérico). V11 sozinho na primeira página
dos slides (PLANO §2.3 mandato).

### 6.4 Resultados — confusion matrices (slides 10-11)

| Viz | O que mostra | Fonte |
|-----|--------------|-------|
| **V14. CMs binário, 7 vencedores** | Matriz 2×2 normalizada por linha; uma por base | `03` §5 (já tem, cell `534b3eae`) |
| **V15. CMs multi-classe — sobreviventes** | Weather + Modbus (+GPS_Tracker se couber), normalizadas por linha | `03` §6.1 (já tem, cell `003ea88e`) |

### 6.5 Resultados — case-studies (slides 12-13)

| Viz | O que mostra | Fonte |
|-----|--------------|-------|
| **V16. Modbus: F1 vs addressSize** | Curva do salto +0.347 → +0.572. Linha por termômetro. | construir: `df.query("base=='Modbus' and task=='binary' and model=='WiSARD'")` + groupby(thermo) |
| **V17. Lift por base** | Bar horizontal piso → best, anotando lift acima da barra. Cor por tier. | §7.1 da `03`; construir a partir do `tier_table` |
| **V18. BloomWiSARD: F1 vs memória, todas as bases** | Marca o ponto "104 B vence Thermostat" | filtrar Pareto V12 só Bloom |

### 6.6 Resultados — diagnóstico cross-model (slides 14, backup)

| Viz | O que mostra | Fonte |
|-----|--------------|-------|
| **V19. Tabela validação cruzada** | Δ entrega vs reference por modelo × base | §5.4 acima; §8.2 da `03` |
| **V20. Boxplot train_time por modelo** | Order-of-magnitude (caveat ambiente!) | filtrar por `submission` |
| **V21. Boxplot inference_latency por modelo** | µs/sample, log-scale | idem |
| **V22. Heatmap cobertura por (modelo, base)** | Cell pivot já tá no §2.1 do `03` | `03` §2.1 (já tem, cell `26d27c90`) |

### 6.7 Visualizações já produzidas pelos integrantes (`_entregas/`)

Estão prontas como PNG, podem entrar como anexo/backup:

- `_entregas/bloomwisard/pareto_f1_memory.png`
- `_entregas/bloomwisard/heatmap_f1_numhashes_filtersize_binary.png`
- `_entregas/bloomwisard/confusion_matrices_binary.png`
- `_entregas/cluswisard/pareto_f1_memory.png`
- `_entregas/cluswisard/heatmap_f1_therm_binary.png`
- `_entregas/cluswisard/binary_vs_multiclass.png` (idem em bloom)
- `_entregas/cluswisard/f1_vs_addr_size_binary.png` — **bom candidato
  pra reforçar V16** (mostra que ClusWiSARD também tem o efeito de
  addressSize, embora menor)

---

## 7. Syllabus da apresentação — 14 slides

Ordem sugerida. Cada item: **título + bullet points (3-5) + viz
sugerida**. Tempo-alvo: ~15 min, ~1 min/slide.

### Slide 1 — Capa
- Título: *Detecção de Anomalia em IoT com Redes Neurais sem Peso —
  Comparativo TON_IoT*
- Equipe, disciplina, data
- 1 linha de pitch: "Comparamos 5 modelos da família WiSARD em 7
  bases de telemetria IoT. Achados: WiSARD clássico vence; n-tupla
  grande destrava sinal multi-feature; BloomWiSARD entrega F1 ≈ 0.85
  com 100 bytes."

### Slide 2 — Problema e Dataset
- Bullet 1: detecção de anomalia em telemetria IoT (ataque vs normal,
  + identificar tipo de ataque)
- Bullet 2: **TON_IoT** (UNSW), 7 dispositivos
- Bullet 3: tarefa binária + multi-classe (6-8 tipos por base)
- Viz: **V1 (tabela 7 bases)** + **V2 (bar % attack)** lado a lado

### Slide 3 — Bases não são iguais: espectro informacional
- Bullet 1: dist. de classes vs piso baseline (chave metodológica)
- Bullet 2: Cramér's V revela tier 🟢🟠🔴
- Bullet 3: prévia "vai vir a surpresa do Modbus depois"
- Viz: **V6 (Cramér's V por base, colorido por tier)**

### Slide 4 — Heatmap base × ataque + decisão temporal
- Bullet 1: 8 tipos de ataque cobrem o espaço (DDoS, scanning,
  injection, ransomware, etc)
- Bullet 2: estrutura temporal **descartada** — split estratificado
  por `type`
- Viz: **V3 (heatmap)**

### Slide 5 — Família WiSARD: 5 modelos
- Tabela compacta dos 5 modelos (§4.2) — característica + hiperparâmetros
- Bullet final: "todos compartilham o pipeline; diferem na estrutura
  interna das RAMs"
- Viz: **V10 (tabela 5 modelos)** + opcional diagrama 1-slide do que
  é um discriminador WiSARD

### Slide 6 — Pipeline e encoding
- Bullet 1: thermômetros (4 variantes, V7)
- Bullet 2: one-hot pras categóricas
- Bullet 3: split 70/30 estratificado, seed=0
- Bullet 4: grid 4 × 6 × 8 = 192 configs por (base, task)
- Viz: **V7 (termômetros lado-a-lado)** + **V8 (pipeline)**

### Slide 7 — Métricas
- Tabela §3.1 (qualidade) + §3.2 (custo)
- Destacar **por que F1 macro** (penaliza prever só majoritária)
- Destacar **por que AUC OvR no multi** (sobrevive ao colapso do argmax)
- Sem viz (texto + tabelas)

### Slide 8 — **Pareto cross-model (gráfico principal)**
- Bullet 1: cada ponto = (modelo, config, base)
- Bullet 2: fronteira por modelo; BloomWiSARD domina em memória,
  WiSARD em F1 máximo
- Bullet 3: BTHOWeN ocupa o meio do Pareto
- Viz: **V11 (Pareto global)** em tela cheia

### Slide 9 — Pareto por base + tabela vencedores
- Bullet 1: 7 paretos (bases) — alguns dominados, outros disputados
- Bullet 2: tabela §5.1 (vencedor por base)
- Bullet 3: contagem cross-modelo (BTHOWeN 4, WiSARD 2, BloomWiSARD 1)
- Viz: **V12 (Pareto por base)** + tabela inline §5.1

### Slide 10 — Surpresa #1: **WiSARD clássico vence**
- Bullet 1: F1=0.913 (Modbus), F1=0.885 (Weather) — top em ambos
- Bullet 2: sofisticação não compra performance nesse dataset
- Bullet 3: o que importa é grid largo de encoding + addressSize alto
- Viz: **V13 (bar grouped por modelo × base)** — destaca os 2
  WiSARD vencendo

### Slide 11 — Surpresa #2: **Modbus, n-tupla destrava sinal**
- Bullet 1: Cramér's V univariado = 0.04 (= "feature não discrimina")
- Bullet 2: mas com `addressSize=32`, F1 sobe pra 0.91 (lift +0.572)
- Bullet 3: sinal vive em **combinação 4-feature** — testemunha do
  valor de n-tupla pra dados de protocolo
- Viz: **V16 (F1 vs addressSize, curva Modbus)** + **V17 (lift bar)**

### Slide 12 — Surpresa #3: **BloomWiSARD, 104 bytes**
- Bullet 1: vence Thermostat com 104 B
- Bullet 2: F1 ≈ 0.85 em Weather/GPS_Tracker com 105 B (4-5 ordens
  abaixo dos competidores)
- Bullet 3: caso pra deploy embarcado (microcontrolador classe Cortex-M)
- Viz: **V18 (BloomWiSARD F1 vs mem)** + zoom no Pareto principal

### Slide 13 — Multi-classe (anexo curto)
- Bullet 1: colapsa em 4/7 bases (limite informacional)
- Bullet 2: sobrevive em Weather (0.83), Modbus (0.83), GPS_Tracker (0.43)
- Bullet 3: AUC OvR mostra que ranqueamento funciona mesmo onde
  argmax falha
- Viz: **V15 (CMs multi-classe sobreviventes)** lado a lado

### Slide 14 — Conclusões + trabalhos futuros
- Bullet 1: WNN entrega F1 0.88-0.91 nas 3 bases ricas com 100B-500KB
- Bullet 2: arquiteturas sofisticadas (ClusWiSARD/ULEEN) **não
  superam** WiSARD clássico — possível overhead sem retorno aqui
- Bullet 3: bases pobres (Garage_Door 🔴) precisam de feature
  engineering, não modelo melhor
- Bullet 4: trabalhos futuros — TON_IoT Network (44 features, 211 k
  fluxos), seed multi-rodada com confidence intervals, deploy
  embarcado do BloomWiSARD vencedor

### Backup (opcional, slides 15+)
- B1. Validação cruzada entrega × ref (V19)
- B2. Train time / inference latency com caveats (V20, V21)
- B3. Cobertura de grid por modelo (V22)
- B4. Lista das 8 categorias de ataque do TON_IoT

---

## 8. Riscos / cuidados pro Claude Desktop

1. **Não inventar números.** Toda métrica citada vem do
   `03_analise_comparativa.ipynb` §3, §6, §7 ou desse hand-off §5.
   Se precisar de um número que não tá aqui, peça pro coringa
   rodar uma query no DataFrame.

2. **Caveat BTHOWeN `memory=0`**: o `model_size_bytes()` reporta 0
   quando bleach colapsa o modelo. Já tem nota no §5.1; **não
   plotar essa config na Pareto** — usar `colab`/`vscode` em vez
   de `reference` pra BTHOWeN em qualquer figura de memória.

3. **Caveat tempo cross-machine**: 3 ambientes. Se aparecer no
   slide, marcar o ambiente. ClusWiSARD e BloomWiSARD entrega são
   **pure-Python** (~10-50× mais lento que C++).

4. **Convenção de nomes (estrita)**: tag técnica do modelo/variante,
   **nunca** nome de pessoa do grupo. Se você ver "Karen" em
   algum sidecar, troque por `cluswisard_purepython` (ou similar).

5. **Visualizações já existem no notebook**: pra V3, V4, V5, V7,
   V11, V12, V14, V15, V22 — a imagem PNG pode ser exportada
   direto da última execução do notebook. Você não precisa redesenhar
   nada; só montar slide e legendar.

6. **Para construir V13, V16, V17, V18, V20, V21**: o coringa pode
   acrescentar células no `03_analise_comparativa.ipynb` — peça
   explicitamente. Não tentar inventar a partir do DataFrame só
   com base no hand-off.

7. **Tempo do slide**: ~15 min total → ~1 min/slide → não enche de
   texto. Bullets curtos, número grande, viz visível à distância.

8. **Public-facing**: o trabalho não é confidencial, mas o dataset
   TON_IoT tem licença restritiva — não distribuir CSVs nos
   anexos do slide.
