# Hand-off — Entregas T1 recebidas em 2026-05-21

Documento de consolidação das **duas primeiras entregas** do trabalho de
detecção de anomalia em IoT (TON_IoT). Serve pra:

1. Acelerar a leitura das próximas sessões (humano ↔ Claude Code).
2. Dar contexto pros 3 integrantes restantes (WiSARD puro, BloomWiSARD,
   ULEEN) sobre o formato esperado e armadilhas já encontradas.
3. Registrar decisões em aberto que dependem do grupo.

> Esse documento **envelhece rápido**. Se ainda servir após o
> recebimento do 3º envio, considere reescrever em vez de só apendar.

---

## 1. O que foi recebido

| Modelo      | Integrante (suposto)  | Origem                                     | Local final                                       |
|-------------|-----------------------|--------------------------------------------|---------------------------------------------------|
| ClusWiSARD  | Karen (path do `SESSAO.md`) | `T1_ClusWiSARD-20260521T203742Z-3-001.zip` | `results/cluswisard/`                             |
| BTHOWeN     | ?                     | `results_bthowen-20260521T203736Z-3-001.zip` | `results/bthowen/{colab,vscode}/`               |

Sidecars (notebook de origem, script, log, `SESSAO.md`, report HTML)
em `notebooks/toniot/_entregas/<modelo>/` — não fazem parte do schema
canônico, mas servem de evidência.

A 3ª pasta do BTHOWeN (`Results BTHOWen vscode`, sem o "R" do "Results")
era byte-identical ao `Results BTHOWeN VsCode local`. Descartada como
upload duplicado.

---

## 2. Cobertura de grid (vs PLANO §3)

`PLANO.md` §3.1 pede **4 termômetros × 6 sizes × 8 address_sizes = 192
configs** por (base × task), com 7 bases × 2 tarefas → **2 688
configs por modelo**.

### 2.1 ClusWiSARD (`results/cluswisard/`)

| Eixo            | Esperado                                | Entregue                |
|-----------------|-----------------------------------------|-------------------------|
| Termômetros     | Simple, Distributive, Gaussian, Exponential | Distributive, Gaussian (2/4)   |
| Sizes           | {2, 4, 8, 16, 32, 64}                   | {8, 16, 32} (3/6)       |
| Address sizes   | {4, 8, 12, 16, 20, 24, 28, 32}          | {4, 8, 16} (3/8)        |
| Bases           | 7                                       | 5 (faltam Garage_Door, Motion_Light — 0 configs por terem só 2 bits)  |
| Total           | 2 688                                   | 172                     |
| **`skipped` registrado?** | sim                            | **não** (campo ausente; bases vazias ficam `[]`) |

Comentário do `SESSAO.md`: rodou em **pure-Python wisardpkg
reimplementado**, pois `python3-dev` não estava disponível no ambiente
da Karen para compilar o fork C++. A entrega tem o módulo
(`_entregas/cluswisard/wisardpkg_purepython.py`) e é funcionalmente
equivalente, mas **~10-50× mais lenta** — `train_time_s` e
`inference_latency_us` não são comparáveis cross-model.

### 2.2 BTHOWeN — run **Colab** (`results/bthowen/colab/`)

| Eixo                | Esperado                                | Entregue                |
|---------------------|-----------------------------------------|-------------------------|
| Termômetros         | Gaussian (PLANO §3.2 isenta BTHOWeN dos demais) | Gaussian (OK) |
| Sizes               | 6                                       | {2, 4, 8, 16, 32, 64} (OK) |
| Address sizes       | 8                                       | {4, 8, 12, 16, 20, 24, 28, 32} (OK) |
| `filter_entries`    | {16, 64, 256, 1024} (4)                 | 1024 (1/4)              |
| `filter_hashes`     | {2 ou 3 ou …}; PLANO §3.2 sugere {3, 5, 7} | 2 (1/3)             |
| Total entries       | —                                       | 672 (48 por base × task) |
| `skipped` registrado? | sim                                  | **sim** (266 skipped, 406 válidos) |
| `metrics`           | 12 campos                               | todos preenchidos       |
| `machine`           | obrigatório                             | "Google Colab CPU — Intel(R) Xeon(R) CPU @ 2.20GHz 13GB RAM" |

### 2.3 BTHOWeN — run **VsCode local** (`results/bthowen/vscode/`)

| Eixo                | Esperado                                | Entregue                |
|---------------------|-----------------------------------------|-------------------------|
| Termômetros         | Gaussian                                | Gaussian (OK)           |
| Sizes               | 6                                       | {2, 4, 8, 16, 32, 64} (OK) |
| Address sizes       | 8                                       | **{4, 6, 8} (3/8)**     |
| `filter_entries`    | {16, 64, 256, 1024}                     | {16, 64, 256, 1024} (OK) |
| `filter_hashes`     | {3, 5, 7}                               | {3, 5, 7} (OK)          |
| Total entries       | —                                       | 3 024                   |
| `skipped` registrado? | sim                                  | **sim** (1176 skipped, 1848 válidos) |
| `machine`           | obrigatório                             | "AMD Ryzen 7 5825U with Radeon Graphics 15GB RAM" |

Comentário: os dois runs do BTHOWeN são **complementares**. Colab varreu
o eixo de `addressSize` mas fixou os filtros; VsCode varreu os filtros
mas só `addressSize ∈ {4,6,8}`. Pra apresentação, mergir como uma única
fronteira de Pareto BTHOWeN com todos os pontos válidos (3868 totais).

> Pra `Garage_Door` e `Motion_Light` no run VsCode: **todos** os 216
> entries por (base × task) ficam `skipped=True` (input < addressSize).
> Esperado.

### 2.4 Resumo visual

Roda `03_analise_comparativa.ipynb` §2 — gera tabela pivot
`coverage_summary` com `n_valid/n_total` por (base × task) × (modelo,
submission).

---

## 3. Auditoria de schema (vs PLANO §4)

### 3.1 BTHOWeN

**Cumpre o schema** (Colab) ou **cumpre com extensões** (VsCode duplica
`filter_entries`/`filter_hashes` top-level — o loader consolida dentro
de `model_hyperparams`). Todos os 12 campos de `metrics` preenchidos.
Não há trabalho de remapeamento.

> **Bug suspeito**: `memory_bytes_theoretical` no run VsCode dá valores
> minúsculos (ex: 8 bytes pro Modbus). A fórmula provavelmente esquece
> de multiplicar pelo `filter_entries` ou pelo número de RAMs. Não
> bloqueante — usar só o `memory_bytes_serialized` na Pareto.

### 3.2 ClusWiSARD

**Schema flat e diferente** — sem aninhamento, com nomes próprios
(`dataset` vs `base`, `thermometer_type` vs `encoder.type`, etc.). O
loader em `sweep_utils.py` (`_load_clus_flat`) faz o remapeamento.
Campos **ausentes**: `machine`, `timestamp`, `wisardpkg_version`,
`memory_bytes_theoretical`, `cat_bits`, `n_features_*`.

**Decisão**: não pedir re-envio. A entrega traz métricas comparáveis
(F1, AUC), e o custo de re-rodar (~horas) supera o ganho de uniformizar
campos não-críticos. As lacunas estão documentadas no notebook §2.3.

---

## 4. Decisões em aberto (alinhar no grupo)

1. **Comparação de tempo cross-machine** — PLANO §2.4 propôs (a)
   Colab compartilhado, (b) cada um roda no seu + tempo de
   referência. As entregas atuais não trouxeram tempo de referência.
   A Karen rodou pure-Python (não comparável de jeito nenhum). O
   BTHOWeN tem dois ambientes (Colab Xeon vs Ryzen 7 local). Sugiro
   **abandonar a normalização** e reportar tempo só como
   *ordem-de-grandeza* no relatório técnico, marcando o ambiente.
2. **Métrica de memória oficial** — `memory_bytes_serialized` é o que
   sobreviveu nas três entregas. O `memory_bytes_theoretical` parece
   bugado no BTHOWeN VsCode e é nulo no CLUS. Sugiro usar
   `serialized` na Pareto e mencionar o teórico só em apêndice.
3. **Garage_Door / Motion_Light** — bases patológicas (2-3 bits).
   ClusWiSARD desistiu (0 configs); BTHOWeN Colab gerou 23-25 configs
   válidas mas com F1 ≈ 0.45-0.50 (basicamente chute). Pergunta pro
   prof: **podemos excluí-las** da análise principal e mencionar só
   como case-study negativo?
4. **Multi-classe colapsada** — F1 macro ≈ 0.10 em quase tudo (exceto
   Weather, F1 ≈ 0.73). Era esperado (PLANO §3.4: classe `scanning`
   do Thermostat com 61 amostras). Pra apresentação, sugiro:
   - **Tabela principal**: F1 binário.
   - **Tabela secundária**: F1 macro multi-classe + AUC OvR (que
     sobrevive bem mesmo com F1 baixo).
   - **Matriz de confusão** multi-classe só do Weather.

---

## 5. O que está pronto no repo

- `notebooks/toniot/sweep_utils.py` — loader unificado. Lê os dois
  schemas e devolve DataFrame canônico.
- `notebooks/toniot/03_analise_comparativa.ipynb` — executável
  end-to-end, mostra cobertura, ranking e Pareto. 3 figuras
  embarcadas. **Re-executar conforme novos modelos chegam.**
- `notebooks/toniot/results/{cluswisard,bthowen/{colab,vscode}}/` —
  entregas oficiais.
- `notebooks/toniot/_entregas/{cluswisard,bthowen}/` — sidecars
  (SESSAO.md, notebook fonte, runner script, HTML report).
- `.gitignore` ajustado: comita os JSONs das entregas dos integrantes,
  ignora só os resultados regeneráveis do próprio coringa (em
  `results/wisard/`).

## 6. Próximos passos

1. **Decidir** os 4 pontos em aberto da §4 (5 min de chamada).
2. **Cobrar** os 3 integrantes restantes (WiSARD, BloomWiSARD, ULEEN).
   Recomendação pra eles:
   - Schema "tipo BTHOWeN" foi o que ficou mais saudável — pedir que
     copiem o template de `results/bthowen/colab/Fridge__binary.json`.
   - Registrar `skipped=true` em vez de omitir; o loader confia nisso
     pra distinguir "ainda não rodou" de "não dá pra rodar".
   - Pode rodar parcial; mas avise quais axes ficaram de fora.
3. **Iterar** o notebook §6 (observações) à medida que novos modelos
   chegam — esse vira a base da seção "Resultados" da apresentação.
