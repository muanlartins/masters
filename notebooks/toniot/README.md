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

Venv compartilhado em `../../venv/` (Python 3.13). Se você não tem o
venv ainda, recrie a partir do `requirements.txt` na raiz do repo:

```bash
cd ../..                                            # raiz do masters/
python3.13 -m venv venv
source venv/bin/activate
pip install --no-build-isolation -r requirements.txt
```

O `--no-build-isolation` é necessário porque o build C++ do `wisardpkg`
precisa enxergar `pybind11` e `setuptools` do ambiente ativo (build
isolado quebra). O `requirements.txt` já fixa o `wisardpkg` num commit
específico do nosso fork
[`muanlartins/wisardpkg`](https://github.com/muanlartins/wisardpkg) —
inclui `BloomWiSARD`, termômetros ajustados (`Distributive`,
`Gaussian`, `Exponential`, `Stochastic`), `ColorMaskBinarization`,
`Local2DMapping` e ports PyTorch de `BTHOWeN`, `DWN`, `ULEEN`. Ver
o `CLAUDE.md` do fork para detalhes da API.

Para desenvolvimento ativo do próprio `wisardpkg`, clone o fork ao lado
do `masters/` e instale com `pip install -e --no-build-isolation .` —
nesse modo o pacote é importado a partir do seu clone, não do commit
pinado.

## Convenção de saída

Cada integrante salva resultados de sweep em `results/<modelo>/<split>/...json`
com schema único (definido em `PLANO.md` §4) para permitir o merge final.
