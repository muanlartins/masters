# Imagens para gerar / exportar — Apresentação T1 TON_IoT

Este documento é o briefing para pedir ao Claude Code que produza as imagens dos placeholders do `.pptx`. Está dividido em duas listas:

- **Lista A — Exportar PNG do notebook** (figuras já existem no `03_analise_comparativa.ipynb` ou `01_eda_telemetry.ipynb`).
- **Lista B — Construir nova figura** (precisa adicionar célula no notebook 03).

Para todas: salvar PNG em alta resolução (≥ 150 dpi, mínimo 1200×800 px) com **fundo branco**, fontes grandes (≥ 14 pt nos labels), e SEM título dentro da figura (o slide já tem o título da asserção). Eixos e legendas sim, título matplotlib não.

Sugestão de nomenclatura: `figs/v01_attack_pct.png`, `figs/v03_heatmap_base_attack.png`, etc. — facilita o passo de inserção no `.pptx` depois.

---

## Lista A — Exportar PNG (figuras existentes)

### V2 — Bar horizontal: % attack por base
- **Onde está**: `01_eda_telemetry.ipynb` §4.1
- **Slide destino**: 2
- **Tamanho destino no slide**: 4.0″ × 3.4″
- **O que mostrar**: 7 barras horizontais (uma por base), valor de `% attack`. Eixo X de 0 a 100%. Linha vertical pontilhada em 50% como referência ("piso de chute"). Ordenar do maior pro menor.
- **Nota**: marcar visualmente que todas estão acima de 50% (ataque é classe majoritária).

### V3 — Heatmap base × tipo de ataque
- **Onde está**: `01_eda_telemetry.ipynb` §4.2
- **Slide destino**: 4
- **Tamanho destino**: 5.3″ × 3.4″
- **O que mostrar**: 7 bases (linhas) × 8 tipos de ataque (colunas). Valor da célula = contagem; **log-scale** na intensidade da cor. Células vazias claramente marcadas (ex: cinza claro).

### V6 — Bar Cramér's V máx por base
- **Onde está**: `03_analise_comparativa.ipynb` §7.1
- **Slide destino**: 3
- **Tamanho destino**: 3.5″ × 3.4″
- **O que mostrar**: 7 barras horizontais. Cor por tier: verde (Forte: GPS_Tracker, Weather), amarelo (Interações: Modbus), laranja (Fraco: Fridge, Thermostat, Motion_Light), vermelho (Ruído: Garage_Door). Anotar Modbus com asterisco ou destaque visual — "quebra a regra".

### V8 — Diagrama de pipeline
- **Onde**: não existe ainda; **pode ser desenhado em PowerPoint** sem precisar passar pelo Claude Code.
- **Slide destino**: 6
- **Tamanho destino**: 9.0″ × 1.4″
- **O que mostrar**: caixas horizontais conectadas por setas — `CSV → clean_df → split estratificado (70/30) → encode (termômetro + one-hot) → fit → métricas`. Estilo simples, paleta da apresentação (deep blue `#065A82` para caixas, terracotta `#B85042` para setas).
- **Alternativa**: se preferir gerar via matplotlib + graphviz, OK também.

### V11 — Pareto F1 macro × memória (cross-model)
- **Onde está**: `03_analise_comparativa.ipynb` cell `b2863b2e`
- **Slide destino**: 8 — **gráfico central da apresentação**
- **Tamanho destino**: 9.0″ × 3.4″ (tela cheia)
- **O que mostrar**: scatter de todas as configs válidas, cor por modelo (5 cores distintas). Fronteira de Pareto por modelo desenhada como linha. Eixo X (memória serializada em bytes) em **log-scale**. Eixo Y (F1 macro) linear, 0 a 1. Legenda das cores no canto inferior direito.
- **Polish**: exclude bthowen_reference (bug `memory=0`).

### V12 — Small multiples: Pareto por base
- **Onde está**: `03_analise_comparativa.ipynb` cell `92884991`
- **Slide destino**: 9
- **Tamanho destino**: 5.3″ × 3.6″
- **O que mostrar**: grade 2 × 4 (uma célula vazia OK), uma Pareto por base. Mesma codificação de cores que V11. Título de cada painel = nome da base.

### V15 — Matrizes de confusão multi-classe (sobreviventes)
- **Onde está**: `03_analise_comparativa.ipynb` cell `003ea88e`
- **Slide destino**: 14
- **Tamanho destino**: 5.5″ × 3.6″
- **O que mostrar**: lado a lado, CMs multi-classe de **Weather** e **Modbus** (e GPS_Tracker se couber). Normalizadas por linha. Anotar valores nas células (% ou frações).

---

## Lista B — Construir nova figura (adicionar célula no notebook 03)

### V13 — Best F1 por modelo × base (bar grouped)
- **Slide destino**: 10
- **Tamanho destino**: 5.5″ × 3.6″
- **Construção**: a partir de `best_per_base(df, 'f1_macro')`, agrupar por base no eixo X e modelo na cor. 5 cores (modelos) × 7 grupos (bases) = 35 barras. Destacar visualmente as barras de WiSARD em Modbus e Weather (borda dourada/contorno mais grosso, ou hatching).
- **Notas**: ordenar bases pelo F1 médio descendente para impacto visual. Adicionar linha horizontal tracejada em ~0.38 marcando "piso baseline" (sempre prever 1).

### V16 — Modbus: F1 vs addressSize (linha por termômetro)
- **Slide destino**: 11
- **Tamanho destino**: 5.5″ × 3.6″
- **Construção**: filtrar `df.query("base=='Modbus' and task=='binary' and model=='wisard'")`. Eixo X = `address_size` (4, 8, 12, 16, 20, 24, 28, 32). Eixo Y = F1 macro. Uma linha por termômetro (4 cores: Simple, Distributive, Gaussian, Exponential). Marcar visualmente o salto entre addr=16 e addr=32 (área sombreada ou anotação "+0.22").
- **Notas**: usar `groupby(['address_size', 'thermometer_type']).f1_macro.max()` se há múltiplas configs por ponto.

### V17 — Lift por base (piso → best F1)
- **Slide destino**: 12
- **Tamanho destino**: 5.5″ × 3.6″
- **Construção**: barras horizontais, uma por base. Cada barra cresce do **piso baseline** (sempre prever 1, ~0.34-0.38) até o **best F1 atingido**. Anotar o delta acima da barra. Cor da barra por tier informacional (verde / amarelo / laranja / vermelho — mesma do V6).
- **Ordenar** decrescente pelo lift, para destacar Modbus no topo.

### V18 — BloomWiSARD: F1 vs memória, todas as bases
- **Slide destino**: 13
- **Tamanho destino**: 5.5″ × 3.6″
- **Construção**: filtrar `df.query("model=='bloomwisard'")`. Scatter F1 macro × memória serializada (log). Cor por base (7 cores). **Anotação destacada** no ponto Thermostat 104 B (seta + label "104 B, F1 = 0.512 — vence Thermostat"). Anotação secundária no ~105 B Weather/GPS_Tracker.
- **Polish**: ressaltar visualmente que toda a nuvem de pontos está em ~ 10²–10⁴ bytes, 4-5 ordens abaixo dos competidores no Pareto principal.

### V20 — Boxplot train_time_s por modelo (backup B2)
- **Slide destino**: backup B2
- **Tamanho destino**: 4.4″ × 3.6″
- **Construção**: boxplot agrupado por `submission` (não por `model`), pra deixar visíveis os 3 ambientes (Colab vs VsCode vs pure-Python). Eixo Y em **log-scale** (segundos). Anotar o ambiente embaixo de cada caixa.

### V21 — Boxplot inference_latency_us por modelo (backup B2)
- **Slide destino**: backup B2
- **Tamanho destino**: 4.4″ × 3.6″
- **Construção**: idem V20, mas com `inference_latency_us`. Y em log-scale (µs). Mesma anotação de ambiente.

---

## Workflow sugerido para inserir as imagens no .pptx depois

1. Gerar todas as PNGs e salvar em uma pasta única (ex: `figs/`).
2. Abrir o `.pptx` no PowerPoint, navegar slide a slide até o placeholder.
3. Clicar com o botão direito no placeholder (caixa cinza tracejada) → **Inserir Imagem** → escolher o PNG correspondente.
4. Arrastar pra ajustar à área do placeholder; depois apagar o placeholder (a caixa cinza).
5. Alternativa programática: se quiser, posso gerar um script `insert_images.js` (pptxgenjs ou python-pptx) que substitui os placeholders pelas imagens automaticamente uma vez que elas existam — me peça quando as PNGs estiverem prontas.

---

## Resumo de produção — atualizado 2026-05-22

**Todas as PNGs já estão geradas em `notebooks/toniot/figs/`** pelo
`04_figuras_apresentacao.ipynb`. Pra regenerar:

```bash
cd notebooks/toniot
../../venv/bin/jupyter nbconvert --to notebook --execute \
    04_figuras_apresentacao.ipynb --output 04_figuras_apresentacao.ipynb
```

| Item | Slide | Arquivo                              | Tamanho |
|------|------:|--------------------------------------|--------:|
| V2   | 2     | `figs/v02_attack_pct.png`            | 44 KB |
| V3   | 4     | `figs/v03_heatmap_base_attack.png`   | 79 KB |
| V6   | 3     | `figs/v06_cramers_v_por_base.png`    | 45 KB |
| V8   | 6     | (desenhar no PowerPoint)             | —     |
| V11  | 8     | `figs/v11_pareto_cross_model.png`    | 285 KB |
| V12  | 9     | `figs/v12_pareto_por_base.png`       | 354 KB |
| V13  | 10    | `figs/v13_best_f1_modelo_base.png`   | 62 KB |
| V14  | 11    | `figs/v14_cms_binarios.png`          | 112 KB |
| V15  | 14    | `figs/v15_cms_multiclass.png`        | 170 KB |
| V16  | 11    | `figs/v16_modbus_f1_vs_addrsize.png` | 85 KB |
| V17  | 12    | `figs/v17_lift_por_base.png`         | 43 KB |
| V18  | 13    | `figs/v18_bloomwisard_f1_mem.png`    | (refeita: strip por base, mem é constante ~100 B) |
| V20  | bk    | `figs/v20_train_time_boxplot.png`    | 66 KB |
| V21  | bk    | `figs/v21_inference_latency_boxplot.png` | 68 KB |
| **vC** | bônus | `figs/vC_associacao_features.png`  | 206 KB — Cramér's V feature×feature×label por base, pedido extra pra entender estrutura do dataset |

### Detalhe sobre V18 (mudança de design)

A intenção original era um scatter F1 × memória em log scale. Descobrimos
ao gerar que **todas as configs do BloomWiSARD ficam em 99-106 bytes**
(a Bloom comprime tudo independente da cfg). Log scale ficou sem sentido,
então redesenhei como **strip plot por base** com a memória anotada nos
vencedores. Visualmente é mais forte: "olha, 100 B atinge F1=0.88 em
GPS_Tracker e Weather".
