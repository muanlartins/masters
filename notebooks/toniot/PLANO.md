# Plano: Detecção de Anomalia em IoT com WiSARD e variantes (TON_IoT)

Documento de partida — discutir e iterar antes dos sweeps. As decisões
aqui definem o schema de saída de cada integrante; mudá-las depois
custa caro (re-rodar todos os experimentos).

## 1. Enunciado

Precisamos primeiro entender o que é "detecção de anomalia". Duas
interpretações razoáveis, e vamos analisar as duas em paralelo (mesmo
split, mesmas features, só muda a coluna alvo — o custo extra é baixo):

1. **Classificação binária supervisionada**: `label` indicando 0 para
   `normal` e 1 para qualquer ataque.
2. **Classificação multi-classe supervisionada**: o output é o `tipo`
   de ataque (uma das classes de `type`).

A formulação **(1)** é a mais simples. Pelos dados reais (EDA roda
nos 7 CSVs do TON_IoT telemetria), o desbalanceamento é moderado:
**51.8% a 62.4% de ataque** dependendo da base — ou seja, ataque
geralmente predomina (oposto do que eu esperava de início, mas longe
dos 80% da base de network). Serve de sanity check.

A formulação **(2)** é mais desafiadora e traz o maior valor —
análise por classe, qual ataque o modelo confunde com qual, etc.

> **Observação sobre a telemetria** (confirmado no EDA): cada base
> tem entre **5 e 7 tipos de ataque distintos** (excluindo normal).
> `Modbus` e `Thermostat` não têm `ddos`/`ransomware`; as outras 5
> têm o conjunto cheio. **Mais importante**: o `Thermostat` tem a
> classe `scanning` com apenas **61 amostras** num total de 32 774
> — essa classe minoritária pesa 1/7 no F1 macro, então se o
> modelo errar essas 61, a métrica afunda. Anotar no relatório.

## 2. Métricas

### 2.1 Eficácia

| Métrica | Para que serve |
|---|---|
| **Acurácia** | Total de acertos. Engana em (2) quando uma classe domina, mas é a referência da literatura. |
| **Precisão** | "Das vezes que o modelo previu positivo, quantas acertou?" Em (1), é direto. Em (2), reportar **macro** *e* **weighted**. |
| **Recall** | "Dos casos que eram positivos de verdade, quantos achou?" Mesmo qualificador macro/weighted em (2). |
| **F1 Score** | Equilíbrio harmônico entre precisão e recall. Em (1) é o F1 binário; em (2) reportar **F1 macro** (média por classe, métrica honesta no desbalanceamento) **e F1 weighted** (média ponderada por frequência). |
| **AUC-ROC** | Capacidade de distinguir classes a partir do score, antes de threshold. Em (1) é o AUC binário; em (2) é **One-vs-Rest macro**. |
| **Matriz de confusão** | Artefato visual normalizado por linha — onde a gente vê *qual* ataque o modelo confunde com qual. Vai pro relatório, não pra tabela numérica. |

A insistência em "macro" para (2) é porque sem ele, precision/recall/F1
não estão bem definidos em multi-classe, e a comparação entre integrantes
fica ambígua. Quem usar a `sklearn`, a chamada é
`f1_score(y_true, y_pred, average='macro')` (e `'weighted'` em paralelo).

### 2.2 Custo

| Métrica | O que medir |
|---|---|
| **Memória do modelo (bytes)** | Tamanho do modelo serializado em disco (`pickle` / `save_to_json`) **e** o tamanho teórico em bytes (Σ RAMs × entradas × tamanho_do_voto). O teórico é o que escala pra hardware embarcado; o serializado é o que a gente realmente paga em disco. |
| **Tempo de treino (s)** | Wall clock, single-core. **Atenção**: só é comparável entre integrantes se a máquina for a mesma — ver §2.4. |
| **Latência de inferência (μs / amostra)** | Mediana de 10 k inferências em batch=1. É o que importa pra IoT edge. |

### 2.3 Composição

- **Fronteira de Pareto `(memória, F1 macro)`**: é a forma como BTHOWeN
  e ULEEN reportam. Cada (modelo + configuração) é um ponto; a fronteira
  responde "pra cada orçamento de memória, qual o melhor F1 atingível?".
  É o **gráfico principal** do trabalho — o que vai na primeira página
  da apresentação.

### 2.4 Sobre comparação de tempo entre máquinas

Como cada integrante vai rodar no seu computador, o tempo absoluto **não
é comparável direto**. Duas opções pra contornar:

- **(a)** Combinar de rodar tudo num **Colab compartilhado** (runtime
  CPU, *not* GPU). Mais simples, números diretamente comparáveis.
- **(b)** Cada um roda no seu, mas inclui no JSON um "tempo de
  referência" — quanto a config canônica (Distributive/16/16 em Fridge,
  por exemplo) leva na máquina dele. Aí o coringa pode normalizar a
  posteriori dividindo todos os tempos pelo de referência.

Decisão sugerida: **(a) para apresentação**, com **(b)** como plano B
se o Colab travar. Vale alinhar com todos.

## 3. Hiperparâmetros a variar

### 3.1 Eixos ortogonais comuns a todos os modelos

| Eixo | Valores |
|---|---|
| **Tipo de termômetro** | Simples, Distributivo, Gaussiano, Exponencial (4 opções) |
| **Tamanho do termômetro** (bits/feature) | Potências de 2 de 2 a 64 — `{2, 4, 8, 16, 32, 64}` (6 opções) |
| **Tamanho do endereço** (bits/RAM) | Múltiplos de 4 de 4 a 32 — `{4, 8, 12, 16, 20, 24, 28, 32}` (8 opções) |

Produto cartesiano: **4 × 6 × 8 = 192 configurações** por base por
modelo. Com 7 bases de telemetria e 2 tarefas (binária e
multi-classe), são **~2 700 experimentos por modelo**.

Pra WiSARD, ClusWiSARD e BloomWiSARD esse volume é tranquilo (treino é
basicamente escrita em RAM). Pra **BTHOWeN** e principalmente **ULEEN**
(que tem treinamento gradiente), o integrante deve **podar o grid
principal** — focar em (size, addressSize) intermediários, e justificar
no relatório.

> **Restrição importante** (não óbvia até olhar os dados): o
> `addressSize` não pode exceder o número de bits totais da entrada
> codificada. Várias bases de telemetria têm poucas features e geram
> entradas pequenas — combinações onde `addressSize > input_bits`
> precisam ser **puladas** (não erro, só skip). O `sweep_utils.py`
> faz essa validação; o JSON de resultado registra a config skipada
> com `skipped: true, reason: "addressSize > input_bits"`.
> Ver §3.4 pras contagens.

### 3.2 Hiperparâmetros específicos por modelo (em adição aos eixos comuns)

- **WiSARD**: opcionalmente `negativeEvidence` on/off.
- **ClusWiSARD**: `growthInterval ∈ {5, 10, 20}`, `minScore ∈ {0.1, 0.3, 0.5}`,
  `threshold ∈ {0.7, 0.9}`. Como o produto fica grande, restringir o
  grid principal a `thermoSize ∈ {8, 16}`, `addressSize ∈ {8, 16, 24}`.
- **BloomWiSARD**: `hashMode ∈ {murmur, simhash, h3}`,
  `numHashes ∈ {2, 4, 8}`, `filterSize ∈ {16, 64, 256, 1024}`.
- **BTHOWeN**: a busca binária de bleach já é parte do treino.
  `numFilters ∈ {3, 5, 7}` e `b` (bits do hash) `∈ {4, 6, 8}`.
  Termômetro padrão é Gaussian — registrar separadamente esse caso.
- **ULEEN**: `learning_rate`, `epochs`, dropout, `ensembleSize`.
  Treinamento gradiente; varredura específica deve ser menor — focar em
  `ensembleSize ∈ {1, 3, 5}` e `epochs ∈ {10, 30}`.

### 3.3 Decisões fixas para todos os integrantes

Pra que dois resultados sejam comparáveis cross-model, **tudo abaixo
precisa ser idêntico** entre os integrantes:

- **Limpeza dos CSVs**: aplicar `clean_df()` (função no notebook EDA,
  vai pra `sweep_utils.py`) que:
  - lowercaseia + tira whitespace das colunas e dos valores string;
  - normaliza `sphone_signal` (`'0'`/`'1'`/`'false  '`/`'true  '`) → `Int64` `{0,1}`;
  - parseia `label` como `Int64`.

  **Crítico**: sem isso, `temp_condition` aparenta ter 6 categorias
  quando tem 2, e o encoder gera bits inválidos. Esse bug foi
  encontrado e corrigido durante o EDA.
- **Split**: usar os CSVs `Train_Test_IoT_*` da UNSW tal qual. Eles
  *não* vêm pré-splittados (é tudo um único arquivo); usar
  `train_test_split(random_state=0, test_size=0.3, stratify=df['type'])`.
- **Mapping**: `RandomMapping(seed=0)`. A seed fixa garante que dois
  modelos diferentes vejam o mesmo embaralhamento de bits — diferenças
  no resultado são do modelo, não do mapping.
- **Bleaching**: `BBleaching` (busca binária) ligado por padrão. O
  valor escolhido vai pro JSON em `model_hyperparams`.
- **Fit do termômetro por base**: o termômetro é ajustado em cada base
  separadamente (não há transferência cross-device). Salvar os
  thresholds em `results/encoders/<base>_<tipo>_<size>.json` pra
  reprodutibilidade.
- **Codificação de categóricas**: depende da cardinalidade.
  - **Binárias (2 valores)**: 1 bit só (`door_state`, `light_status`,
    `temp_condition` — todos os casos do TON_IoT telemetria). One-hot
    pra binária gera dois bits **perfeitamente anti-correlacionados**:
    informação zero a mais, mas o dobro do espaço. Pior pra WNN:
    o mapping aleatório pode jogar os dois bits redundantes na mesma
    tupla → invariante constante (`b XOR ¬b = 1`) → capacidade de RAM
    desperdiçada. Convenção determinística: `1` se valor ==
    `sorted(unique_values)[1]`, `0` caso contrário.
  - **k-árias (k>2)**: one-hot tradicional (k bits). Não temos esse
    caso no telemetria.
  - **Já binárias numéricas** (`sphone_signal`, `motion_status`,
    `thermostat_status`): vão direto como 0/1, sem termômetro nem
    one-hot. Já contam como uma feature numérica que `feature_cols`
    devolve, com nunique=2 — o termômetro lida bem desde que size ≥ 2.
  - Os bits categóricos são **concatenados** às barras de termômetro
    pra formar a entrada final. A função `cat_encoded_bits()` (em §3
    do notebook EDA) implementa a política.

### 3.4 Bases — números reais do EDA

7 CSVs `Train_Test_IoT_*.csv` (de ~31 k a ~40 k linhas cada, total
≈ 261 k amostras). Tabela compacta — **`bits@T*` indica o tamanho da
entrada binária da WNN com termômetro de tamanho T**, já somando a
política de bits categóricos (binárias = 1 bit):

| device       |     n | num | cat | card | bits@T8 | bits@T16 | bits@T32 | n_atk | min_class | pct_atk |
|--------------|------:|----:|----:|-----:|--------:|---------:|---------:|------:|----------:|--------:|
| Fridge       | 39944 |   1 |   1 |    1 |       9 |       17 |       33 |     6 |      2042 |    62.4 |
| Garage_Door  | 39587 |   1 |   1 |    1 |       9 |       17 |       33 |     7 |       529 |    62.1 |
| GPS_Tracker  | 38960 |   2 |   0 |    0 |      16 |       32 |       64 |     7 |       550 |    61.5 |
| Modbus       | 31106 |   4 |   0 |    0 |      32 |       64 |      128 |     5 |       529 |    51.8 |
| Motion_Light | 39488 |   1 |   1 |    1 |       9 |       17 |       33 |     7 |       449 |    62.0 |
| Thermostat   | 32774 |   2 |   0 |    0 |      16 |       32 |       64 |     6 |        61 |    54.2 |
| Weather      | 39260 |   3 |   0 |    0 |      24 |       48 |       96 |     7 |       529 |    61.8 |

Features por base:

- **Fridge**: `fridge_temperature` (num) + `temp_condition` (cat: high/low)
- **Garage_Door**: `sphone_signal` (bool 0/1 após limpeza) + `door_state` (cat: closed/open)
- **GPS_Tracker**: `latitude`, `longitude`
- **Modbus**: `fc1_read_input_register`, `fc2_read_discrete_value`,
  `fc3_read_holding_register`, `fc4_read_coil` (4 inteiros grandes)
- **Motion_Light**: `motion_status` (bool 0/1) + `light_status` (cat: on/off)
- **Thermostat**: `current_temperature`, `thermostat_status` (bool 0/1)
- **Weather**: `temperature`, `pressure`, `humidity`

Implicações:

- **Bases pobres em features** (Fridge, Garage_Door, Motion_Light: 9
  bits @ T8, 17 @ T16): vão saturar rápido o `addressSize` — efetivamente,
  `addressSize ∈ {4, 8}` no T8; `{4, 8, 12, 16}` no T16. O resto
  do grid é skipado.
- **Modbus tem entrada grande** (32 bits @ T8): grid completo
  válido, mas as features são inteiros enormes (até 65k+) — a
  escolha de termômetro vai dominar o resultado aqui.
- **Thermostat** com `scanning` de 61 amostras é o pior caso pra F1
  macro; tomar cuidado.

## 4. Schema de Resultado

Pra cada **modelo × base × tarefa**, um arquivo
`results/<modelo>/<base>__<tarefa>.json` (ex.:
`results/wisard/Fridge__binary.json`). Cada arquivo contém um array de
configurações — uma entrada por ponto do grid.

```json
{
  "model": "WiSARD",
  "base": "Fridge",
  "task": "binary",                  // "binary" | "multiclass"
  "encoder": {"type": "Distributive", "size": 16},
  "addressSize": 16,
  "model_hyperparams": {},           // varia por modelo
  "split": {"random_state": 0, "test_size": 0.3, "stratified": true},
  "input": {
    "n_features_num": 1,             // features numericas
    "n_features_cat": 1,             // features categoricas
    "cat_bits": 1,                   // bits gastos pelas categoricas (1 se binaria, k se k-aria)
    "bits_total": 17                 // n_features_num * encoder.size + cat_bits
  },
  "skipped": false,                  // true se addressSize > bits_total
  "skipped_reason": null,
  "metrics": {
    "accuracy": 0.0,
    "precision_macro": 0.0,
    "precision_weighted": 0.0,
    "recall_macro": 0.0,
    "recall_weighted": 0.0,
    "f1_macro": 0.0,
    "f1_weighted": 0.0,
    "auc_roc": 0.0,                  // binary: AUC; multiclass: OvR macro
    "memory_bytes_serialized": 0,
    "memory_bytes_theoretical": 0,
    "train_time_s": 0.0,
    "inference_latency_us": 0.0
  },
  "confusion_matrix": [[...], [...]],
  "labels": ["normal", "attack"],    // ou as classes na ordem da matriz
  "machine": "Colab CPU free-tier",  // pra normalizar tempo entre integrantes
  "wisardpkg_version": "2.0.0a7",
  "timestamp": "2026-05-15T10:00:00Z"
}
```

Quem mexer no schema **avisa todos os outros** antes — uma mudança no
nome de campo invalida o merge final.

## 5. Saída esperada

- **Foco**: apresentação primeiro, relatório técnico em seguida.
- Apresentação: ~10–15 slides. O ponto principal é a fronteira de
  Pareto cross-model + matrizes de confusão dos 2–3 melhores modelos
  na tarefa multi-classe.
- Relatório técnico: o aprofundamento, com tabelas por base e a
  análise por integrante.

## 6. Ordem de trabalho

1. **Todos**: rodam `01_eda_telemetry.ipynb` localmente, confirmam
   que ambiente está OK, baixam os CSVs do TON_IoT pra `data/toniot/`.
2. **Coringa** escreve `02_sweep_template.ipynb` que materializa o
   schema da §4 — carrega base, ajusta encoder, treina modelo, mede
   métricas, salva JSON. Cada integrante copia e adapta pro seu modelo.
3. **Cada integrante** roda seus sweeps (em paralelo) e abre PR com
   seus JSONs em `results/<modelo>/`.
4. **Coringa** escreve `03_analise_final.ipynb` — consolida JSONs,
   produz tabelas, matrizes de confusão e o gráfico de Pareto.
5. Apresentação + relatório.
