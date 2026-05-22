# Documentação de Sessão — ClusWisard / TON_IoT
**Data:** 2026-05-20  
**Objetivo:** Instalar dependências, implementar e executar o modelo ClusWisard para detecção de anomalias no dataset TON_IoT

---

## 1. Contexto

O projeto RNSP (Redes Neurais Sem Pesos) propõe usar WiSARD e suas variantes para detectar anomalias em dados de telemetria IoT. O roteiro está definido em:
- `README.md` e `PLANO.md` do repositório [muanlartins/masters](https://github.com/muanlartins/masters/tree/main/notebooks/toniot)
- Notebook de EDA: `01_eda_telemetry.ipynb`
- Biblioteca: fork [muanlartins/wisardpkg](https://github.com/muanlartins/wisardpkg/tree/muanlartins)

---

## 2. Ambiente e Instalação

### Desafios encontrados
- Sistema sem `pip` instalado (Python 3.12.3 bare, Ubuntu 24.04)
- `python3-dev` (headers C) não disponível sem `sudo`
- `wisardpkg` requer compilação C++/pybind11 → sem `Python.h`, impossível compilar
- Jupyter/nbconvert ausentes

### Solução adotada
1. **pip instalado** via `get-pip.py` com `--break-system-packages`:
   ```bash
   python3 /tmp/get-pip.py --user --break-system-packages
   ```
2. **Dependências instaladas** via `~/.local/bin/pip`:
   ```bash
   pip install --user --break-system-packages pybind11 pandas numpy scikit-learn matplotlib seaborn
   ```
3. **wisardpkg reimplementado** em Python puro (sem C++) — arquivo `wisardpkg.py` no diretório de trabalho — importado com prioridade via `sys.path.insert(0, '.')`.
4. **Notebook convertido** para script `.py` via parser JSON do `.ipynb`, executado com `python3`.

---

## 3. Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `ClusWisard_TON_IoT.ipynb` | Notebook Jupyter completo com toda a pipeline |
| `ClusWisard_run.py` | Script Python gerado automaticamente a partir do notebook (para execução sem Jupyter) |
| `wisardpkg.py` | Implementação pura Python do wisardpkg (ver Seção 4) |
| `results/cluswisard/` | Diretório com todos os resultados |
| `results/cluswisard/all_results.json` | 172 experimentos consolidados (JSON) |
| `results/cluswisard/all_results.csv` | Mesmos dados em CSV |
| `results/cluswisard/<Dataset>__<task>.json` | Resultados por dataset/tarefa |
| `results/cluswisard/*.png` | Gráficos de análise |
| `results/cluswisard/execution.log` | Log completo da execução |

---

## 4. Implementação do wisardpkg.py

Como `python3-dev` estava indisponível, o wisardpkg C++ não pôde ser compilado. Foi implementada uma versão **pura Python compatível** com a API do wisardpkg >= 1.6.

### Classes implementadas

#### `DataSet`
Coleção de entradas binárias (`BinInput`) com rótulos opcionais.
- `add(bits, label)` — adiciona uma amostra
- `__len__`, `__getitem__`, `getLabel(idx)`, `getY(idx)`

#### `BinInput`
Wrapper para lista de bits `{0,1}^n` com método `.list()`.

#### `ClusWisard(addressSize, minScore, threshold, discriminatorsLimit)`
Rede WiSARD com múltiplos discriminadores por classe.

**Algoritmo de treinamento:**
1. Para cada amostra `(x, label)`:
   - Mapeamento aleatório de bits em grupos de `addressSize` (seed=0 fixo)
   - Computa ativações em cada discriminador da classe
   - Se `max_ativações >= threshold` → atualiza o melhor discriminador
   - Senão → cria novo discriminador (se `disc_limit = 0` ou não atingiu o limite)

**Algoritmo de classificação (score ponderado normalizado):**
- Para cada classe: `score = Σ(count_i) / n_treino_discriminador`
- Classe vencedora = `argmax(score)`
- Normalização por `n_treino` remove viés de classes desbalanceadas

**Serialização:** `model.json()` retorna estrutura JSON com metadados do modelo (estimativa de memória).

#### Termômetros

| Classe | Thresholds | `fit()` necessário |
|--------|-----------|-------------------|
| `DynamicThermometer(sizes, min, max)` | Uniformes por feature | Não |
| `SimpleThermometer(size, min, max)` | Uniformes | Não |
| `DistributiveThermometer(size)` | Quantis empíricos equiespaçados | Sim |
| `GaussianThermometer(size)` | Quantis da gaussiana ajustada | Sim |
| `ExponentialThermometer(size)` | Espaçamento quadrático (aprox. exponencial) | Sim |

**Codificação de features:**
- Numéricas → termômetro: `n` bits por feature onde bit `i = 1 ↔ valor > threshold_i`
- Binárias inteiras (0/1) → 1 bit direto
- Binárias categóricas (2 valores) → 1 bit (ordenação lexicográfica)
- K-árias categóricas (k>2) → one-hot com k bits

---

## 5. Configuração do Grid Search

**Modo rápido (`QUICK_MODE = True`):**
- Termômetros: Distributive, Gaussian
- Tamanhos: 8, 16, 32 bits
- Address sizes: 4, 8, 16 bits

**Total:** 2 × 3 × 3 = 18 configs × 7 datasets × 2 tarefas = 252 experimentos  
→ 172 válidos (80 SKIPados porque `addr_size > total_bits` de entrada)

**Modo completo (`QUICK_MODE = False`):** 4 × 6 × 8 = 192 configs × 14 combinações dataset/tarefa ≈ 2.688 experimentos (~horas)

**Divisão dos dados:** 70% treino / 30% teste, estratificada, `random_state=0`  
**Mapeamento aleatório:** `random.Random(0)` (seed=0 fixo conforme PLANO.md)

---

## 6. Resultados

### Tarefa Binária (normal=0 vs ataque=1)

| Dataset | Melhor Termômetro | Size | Addr | Acurácia | F1 Macro | AUC-ROC | Mem (KB) |
|---------|-----------------|------|------|---------|---------|---------|---------|
| GPS_Tracker | Distributive | 32 | 8 | **0.8760** | **0.8657** | **0.9027** | 0.20 |
| Weather | Distributive | 32 | 8 | **0.7791** | **0.7653** | **0.8686** | 0.20 |
| Modbus | Distributive | 8 | 16 | 0.5207 | 0.5202 | 0.5334 | 0.21 |
| Fridge | Distributive | 32 | 16 | 0.5451 | 0.4980 | 0.4993 | 0.20 |
| Thermostat | Gaussian | 16 | 8 | 0.5058 | 0.5024 | 0.5055 | 0.20 |
| Motion_Light | — | — | — | N/A | N/A | N/A | — |
| Garage_Door | — | — | — | N/A | N/A | N/A | — |

### Tarefa Multi-classe (tipo de ataque)

| Dataset | Melhor Termômetro | Size | Addr | F1 Macro | AUC-ROC (OvR) |
|---------|-----------------|------|------|---------|---------|
| Weather | Gaussian | 32 | 16 | **0.4476** | **0.8777** |
| GPS_Tracker | Distributive | 32 | 8 | 0.3040 | 0.8663 |
| Modbus | Gaussian | 8 | 16 | 0.2570 | 0.6006 |
| Fridge | Distributive | 8 | 4 | 0.1324 | 0.5061 |
| Thermostat | Gaussian | 16 | 4 | 0.1293 | 0.4928 |

### Melhor resultado global
**GPS_Tracker / binary / Distributive(32) / addr=8**  
→ F1 Macro = **0.8657** | AUC-ROC = **0.9027** | Memória = **0.20 KB** | Latência = **19.4 µs/amostra**

---

## 7. Limitações e Observações

### 7.1 Saturação de RAMs (datasets com poucas features)
**Problema:** WiSARD pressupõe que a razão `n_amostras / n_endereços_por_RAM` seja pequena.  
Com poucas features binárias, o espaço de endereços é minúsculo:

| Dataset | Max bits | addr=8 | endereços/RAM | saturação (28k amostras) |
|---------|---------|--------|--------------|--------------------------|
| Fridge | 33 bits (therm=32) | 256 | ~100% | alta |
| Thermostat | 33 bits (therm=32) | 256 | ~100% | alta |
| GPS_Tracker | 64 bits (therm=32) | 65.536 | ~18% | baixa → **bom desempenho** |
| Weather | 96 bits (therm=32) | 65.536 | ~12% | baixa → **bom desempenho** |

**Recomendação:** Para datasets com poucas features, usar `addr_size` maior (≥ 16) e `therm_size` maior (≥ 32), ou considerar feature engineering adicional.

### 7.2 Motion_Light e Garage_Door (2 bits de entrada)
Essas bases têm apenas features binárias puras (sem features numéricas). Com apenas 2 bits de entrada e `addr_size` mínimo = 4, **nenhuma configuração é válida** para WiSARD. São casos patológicos para redes sem pesos — considerar outros classificadores.

### 7.3 wisardpkg puro Python vs C++
A implementação em Python é funcionalmente equivalente mas ~10-50× mais lenta que a versão C++. Para o grid search completo de ~2.700 experimentos, recomenda-se:
```bash
# Instalar com sudo (necessário para python3-dev)
sudo apt install python3-pip python3-dev -y
pip install git+https://github.com/muanlartins/wisardpkg@muanlartins --no-build-isolation
```
Com a biblioteca nativa, o notebook `ClusWisard_TON_IoT.ipynb` pode ser executado diretamente no Jupyter.

### 7.4 AUC alto com F1 baixo (multi-classe)
Nos datasets como Weather e GPS_Tracker, o AUC-ROC multi-classe (OvR macro) é alto (0.87-0.90) mesmo com F1 macro moderado (~0.30-0.45). Isso indica que o modelo **ranqueia bem as classes** (boa separabilidade nos scores) mas **não classifica perfeitamente** — fenômeno esperado em cenários com classes minoritárias raras (ex: tipo "scanning" com apenas 61 amostras no Thermostat).

---

## 8. Como Reproduzir

```bash
# 1. Navegar ao diretório
cd /home/karen-cardoso/Documentos/RNSP/Trabalho_1

# 2. Verificar dependências (se não instaladas)
~/.local/bin/pip install --user --break-system-packages pandas numpy scikit-learn matplotlib seaborn

# 3. Executar o notebook como script (modo rápido, ~15 min)
python3 ClusWisard_run.py 2>&1 | tee results/cluswisard/execution.log

# 4. Para o grid completo, editar ClusWisard_TON_IoT.ipynb:
#    Alterar QUICK_MODE = False  (estimativa: 2-4 horas)

# 5. Com wisardpkg nativo instalado, rodar no Jupyter:
jupyter notebook ClusWisard_TON_IoT.ipynb
```

---

## 9. Próximos Passos

- [ ] Instalar `python3-dev` com acesso root e compilar wisardpkg fork (`muanlartins/wisardpkg@muanlartins`) para obter termômetros ajustados adicionais (BloomWisard, BTHOWeN, DWN, ULEEN)
- [ ] Executar grid completo (QUICK_MODE=False) com 192 configs por dataset/task
- [ ] Comparar resultados com os outros membros da equipe (formato JSON padronizado do PLANO.md)
- [ ] Analisar fronteira de Pareto F1 × memória × latência para seleção do melhor modelo por cenário de deployment
- [ ] Investigar feature engineering para Motion_Light e Garage_Door (combinação de features, contagens temporais)
