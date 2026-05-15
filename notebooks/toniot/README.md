# notebooks/toniot

Detecção de anomalia em IoT usando WiSARD e variantes sobre o
**TON_IoT** (UNSW Canberra Cyber).

## Conteúdo

| Arquivo | Papel |
|---|---|
| `01_eda_telemetry.ipynb` | Exploratório das 7 subbases de telemetria (Fridge, GPS_Tracker, Motion_Light, Garage_Door, Modbus, Thermostat, Weather) — distribuição de classes, distribuições de feature, correlações, séries temporais, sugestões de codificação para WNN. Detecta `data/toniot/` automaticamente. |
| `PLANO.md` | Documento de discussão: o que entendemos por "anomaly detection" neste trabalho, quais métricas medir, quais eixos ortogonais varrer, e como dividir os modelos entre os integrantes. **Ler antes de começar os sweeps.** |

## Dados

- Esperados em `../../data/toniot/` (caminho relativo aos notebooks).
- Não comitar os CSVs no repo — são grandes e a página da UNSW restringe redistribuição.
- Links e instruções: ver a primeira seção do `01_eda_telemetry.ipynb`
  ou a página oficial em
  <https://research.unsw.edu.au/projects/toniot-datasets>.

Subbases relevantes:

- `Train_Test_IoT_*.csv` — 7 CSVs de telemetria (uma por dispositivo).
  Pequenos, mais didáticos, ótimos para varredura rápida.
- `Train_Test_Network.csv` — ~211 k fluxos, 44 colunas, 10 classes
  (normal + 9 ataques). Mais difícil, escala mais real.
- `Train_Test_Linux_*.csv`, `Train_Test_Windows_*.csv` — logs de SO.

Recomendação: começar pelas 7 de telemetria, escalar para o network
depois que os pipelines estiverem estáveis.

## Ambiente

Venv compartilhado em `../../venv/`. `wisardpkg` é a versão local
(`../../wisardpkg/`) — inclui `BloomWiSARD`, termômetros ajustados
(`Distributive`, `Gaussian`, `Exponential`, `Stochastic`) e ports
PyTorch de `BTHOWeN`, `DWN`, `ULEEN`. Ver
`../../wisardpkg/CLAUDE.md` para detalhes.

## Convenção de saída

Cada integrante salva resultados de sweep em `results/<modelo>/<split>/...json`
com schema único (definido em `PLANO.md` §4) para permitir o merge final.
