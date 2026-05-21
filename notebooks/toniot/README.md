# notebooks/toniot

Detecção de anomalia em IoT usando WiSARD e variantes sobre o
**TON_IoT** (UNSW Canberra Cyber).

## Conteúdo para direcionamento do trabalho

| Arquivo                  | Papel                                                                                                                                                                                                                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `01_eda_telemetry.ipynb` | Exploratório das 7 subbases de telemetria (Fridge, GPS_Tracker, Motion_Light, Garage_Door, Modbus, Thermostat, Weather) — distribuição de classes, distribuições de feature, correlações, séries temporais, sugestões de codificação para WNN. Detecta `data/toniot/` automaticamente. |
| `PLANO.md`               | Documento de discussão: o que entendemos por "anomaly detection" neste trabalho, quais métricas medir, quais eixos ortogonais varrer, e como dividir os modelos entre os integrantes. **Ler antes de começar os sweeps.**                                                              |

## Pré-requisitos

- **dataset**
  - fazer o download
- **uv** (gerenciador de pacotes, ambientes virtuais e versões do Python)
  - instalar o uv
  - configurar ambiente

## Dataset (TON_IoT)

Os CSVs não estão versionados — são grandes e a UNSW restringe redistribuição.

1. Acesse <https://research.unsw.edu.au/projects/toniot-datasets> e faça o download.
2. Coloque os arquivos em `data/toniot/`:

```
data/
└── toniot/
    ├── Train_Test_IoT_Fridge.csv
    ├── Train_Test_IoT_Garage_Door.csv
    ├── Train_Test_IoT_GPS_Tracker.csv
    ├── Train_Test_IoT_Modbus.csv
    ├── Train_Test_IoT_Motion_Light.csv
    ├── Train_Test_IoT_Thermostat.csv
    └── Train_Test_IoT_Weather.csv
```

Os notebooks detectam o caminho `../../data/toniot/` automaticamente a partir de `notebooks/toniot/`.

## Instalar o uv

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Outras plataformas e métodos alternativos: <https://docs.astral.sh/uv/getting-started/installation/>

## Configuração do ambiente Python

```bash
uv sync
```

O `uv sync` cria o ambiente virtual em `.venv/`, instala a versão correta do python e todas as dependências declaradas em `pyproject.toml` e compila o `wisardpkg` (extensão C++/pybind11) automaticamente. Nenhum passo adicional é necessário.

> **Nota sobre o wisardpkg:** a versão usada é o fork `muanlartins/wisardpkg@muanlartins`, que adiciona `BloomWiSARD`, termômetros ajustáveis (`Distributive`, `Gaussian`, `Exponential`) e ports PyTorch de `BTHOWeN`, `DWN` e `ULEEN`. O build requer `pybind11` e `setuptools`, declarados em `[tool.uv.extra-build-dependencies]` no `pyproject.toml`.

## Executar os notebooks

O projeto usa **VS Code** com a extensão Jupyter. Após `uv sync`, selecione o interpretador `.venv` no VS Code (`Ctrl+Shift+P` → _Python: Select Interpreter_ → `./.venv/bin/python`) e abra qualquer `.ipynb` normalmente.

## Convenção de saída

Cada integrante salva resultados de sweep em `results/<modelo>/<split>/...json`
com schema único (definido em `PLANO.md` §4) para permitir o merge final.
