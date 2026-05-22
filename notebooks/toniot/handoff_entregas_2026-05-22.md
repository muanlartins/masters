# Hand-off — Entregas T1 completas em 2026-05-22

Substitui `handoff_entregas_2026-05-21.md` (que cobria as 2 primeiras
entregas). Agora **todas as 5 entregas** estão integradas, mais o
gabarito local (`_reference/`) pra validação cruzada.

> Esse documento **envelhece rápido**. Se ainda servir após a
> apresentação, considere reescrever em vez de só apendar.

---

## 1. Estado das entregas

| Modelo       | Schema                      | Local final                                       | Sidecars em                       |
|--------------|------------------------------|---------------------------------------------------|-----------------------------------|
| WiSARD       | PLANO jsonl                  | `results/wisard/`                                 | `_entregas/wisard/`               |
| ClusWiSARD   | flat json (pure-Python)      | `results/cluswisard/`                             | `_entregas/cluswisard/`           |
| BloomWiSARD  | flat json (pure-Python)      | `results/bloomwisard/`                            | `_entregas/bloomwisard/`          |
| BTHOWeN      | PLANO json (2 runs)          | `results/bthowen/{colab,vscode}/`                 | `_entregas/bthowen/`              |
| ULEEN        | PLANO jsonl (grid expandido¹) | `results/uleen/`                                 | `_entregas/uleen/` (cópia do zip) |

Gabarito local: `results/_reference/{wisard,cluswisard,bloomwisard,bthowen,uleen}/`.

¹ ULEEN entrega foi **expandida em 2026-05-22**: de 8 cfgs/file
(`uleen-reduzido.zip` inicial) pra 72 cfgs/file (`uleen.zip` segundo
envio). Grid: 2 thermos (gaussian, linear) × 3 sizes × 3 addrs × 2
epochs. Os 14 jsonls em `results/uleen/` já refletem essa versão.

## 2. Cobertura efetiva (configs válidas por base × task)

(Pivot do notebook §2.1 — abaixo só as bases ricas.)

| base/task               | WiSARD | ClusWiSARD (pp) | BloomWiSARD (pp) | BTHOWeN (col+vs) | ULEEN |
|-------------------------|-------:|----------------:|-----------------:|-----------------:|------:|
| Weather binary          |    272 |              18 |              432 |          34+204  |     8 |
| Weather multiclass      |    272 |              18 |              432 |          34+204  |     8 |
| Modbus  binary          |    304 |              18 |              432 |          38+216  |     8 |
| GPS_Tracker binary      |    248 |              18 |              432 |          31+192  |     8 |

WiSARD entrega é a mais densa nas bases pobres também (5 376
linhas no DataFrame, vs ~110-4k dos demais).

## 3. Schemas e adaptadores

- `_load_plano_schema` → BTHOWeN (`.json`), WiSARD/ULEEN (`.jsonl`), e
  todos os `_reference/*`.
- `_load_flat_schema` → ClusWiSARD e BloomWiSARD (ambos pure-Python,
  schema flat sem aninhamento). `_FLAT_HP_FIELDS` extrai
  `hash_mode/num_hashes/filter_size` (bloom) ou
  `min_score/threshold/discriminators_limit` (clus) pra
  `model_hyperparams`.
- `load_all_results` agora glob-a `.json` **e** `.jsonl`.

Decisão: **pure-Python ≠ C++ é informacional**, então mantemos
submissions separados (`*_purepython` vs `*_reference`). `train_time_s`
e `inference_latency_us` dessas entregas **não são comparáveis**
cross-implementation.

## 4. Vencedores finais (binário)

| base         | modelo       | F1     | mem (B) | encoder           | addr |
|--------------|--------------|-------:|--------:|-------------------|-----:|
| Fridge       | BTHOWeN ref  | 0.516  | — (bug) | Gaussian(32)      | 16   |
| GPS_Tracker  | BTHOWeN colab| 0.877  | 23 118  | Gaussian(64)      | 32   |
| Garage_Door  | BTHOWeN/ULEEN| 0.450  |  ~5 K   | Gaussian(4)       | 4    |
| **Modbus**   | **WiSARD entrega** | **0.913** | 473 535 | Distributive(64) | 32 |
| Motion_Light | BTHOWeN/ULEEN| 0.505  |  ~5 K   | Gaussian(4)       | 4    |
| Thermostat   | BloomWiSARD entrega | 0.512 | **104** | Distributive(32) | 28   |
| **Weather**  | **WiSARD entrega** | **0.885** | 130 875 | Distributive(64) | 32 |

### Multi-classe (sobreviventes)

| base        | modelo            | F1     | AUC OvR |
|-------------|-------------------|-------:|--------:|
| Weather     | WiSARD entrega    | 0.835  | 0.965   |
| Modbus      | WiSARD entrega    | 0.833  | 0.875   |
| GPS_Tracker | BloomWiSARD entrega | 0.428 | 0.762  |

## 5. Validação cruzada (entrega × ref)

- **WiSARD**: deltas todos ≤ ±0.03. Entrega bate o gabarito em Modbus
  (+0.026) e empata o resto. Implementação validada.
- **BTHOWeN**: deltas ≤ ±0.06. Modbus/Weather a entrega ligeiramente
  à frente (cobertura específica).
- **BloomWiSARD**: gap principal em Modbus (-0.091): a entrega não
  varreu `addressSize=32`. Concorda nas demais.
- **ULEEN**: maior dispersão (-0.12 a +0.20). Causa: estocástico +
  grids diferentes em épocas. Reportar lado a lado.
- **ClusWiSARD**: gap esperado pelo pure-Python. Métricas de
  acurácia concordam (Weather 0.86 / 0.83; Modbus 0.70 / 0.64).

## 6. Decisões aplicadas (vs handoff anterior)

1. **Tempo cross-machine**: abandonado normalizar; reportar como
   ordem-de-grandeza marcando o ambiente (Colab Xeon / Ryzen 7 /
   pure-Python).
2. **Memória oficial**: `memory_bytes_serialized`. `theoretical` no
   BTHOWeN VsCode/reference está bugado.
3. **Garage_Door / Motion_Light**: mantidas. §7 mostra que são
   limite informacional, não bug — Cramér's V = 0.000-0.005.
4. **Multi-classe**: tabela secundária + matrizes de confusão de
   Weather e Modbus.

## 7. Próximos passos

1. Slides da apresentação — usar tabelas do notebook §8 e figuras
   §4/§5/§6.1.
2. Relatório técnico — citar o caveat do `bthowen_reference memory=0`.
3. Citar as plots PNG geradas pelos integrantes (`_entregas/bloomwisard/*.png`,
   `_entregas/cluswisard/*.png`) como evidência adicional.

## 8. Estrutura final do repo (notebooks/toniot)

```
results/
  _reference/                 # gabarito do coringa (5 modelos)
    {wisard,cluswisard,bloomwisard,bthowen,uleen}/
  wisard/         *.jsonl     # entrega
  cluswisard/     *.json      # entrega pure-Python
  bloomwisard/    *.json      # entrega pure-Python
  bthowen/{colab,vscode}/     # 2 runs da mesma pessoa
  uleen/          *.jsonl     # entrega grid reduzido
_entregas/
  {wisard,cluswisard,bloomwisard,bthowen}/   # sidecars
                                              # (uleen sem sidecars)
sweep_utils.py                # loader (json + jsonl, 2 schemas)
02_reference_implementations.ipynb
03_analise_comparativa.ipynb  # ← este aqui é o produto
PLANO.md                      # source of truth
handoff_entregas_2026-05-22.md  # este doc
```
