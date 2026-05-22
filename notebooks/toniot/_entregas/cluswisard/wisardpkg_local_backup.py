"""
wisardpkg — implementação pura Python (fallback sem C++)
Reimplementa: DataSet, BinInput, ClusWisard,
              DynamicThermometer, DistributiveThermometer,
              GaussianThermometer, ExponentialThermometer
API compatível com wisardpkg >= 1.6
"""

import json as _json
import random as _random
import numpy as _np

__version__ = "1.6.3-pure-python"


# ── Primitivas de entrada ──────────────────────────────────────────────────────

class BinInput:
    """Vetor binário de entrada para a rede WiSARD."""
    def __init__(self, bits):
        self._bits = list(bits)

    def list(self):
        return self._bits

    def __len__(self):
        return len(self._bits)

    def __getitem__(self, idx):
        return self._bits[idx]


class DataSet:
    """Coleção de BinInputs com rótulos opcionais."""

    def __init__(self, X=None, y=None):
        self._inputs = []
        self._labels = []
        if X is not None and y is not None:
            for x_i, y_i in zip(X, y):
                self.add(x_i, str(y_i))

    def add(self, bits, label=None):
        if isinstance(bits, BinInput):
            self._inputs.append(bits)
        else:
            self._inputs.append(BinInput(bits))
        self._labels.append(str(label) if label is not None else None)

    def __len__(self):
        return len(self._inputs)

    def __getitem__(self, idx):
        return self._inputs[idx]

    def getLabel(self, idx):
        return self._labels[idx]

    def getY(self, idx):
        try:
            return float(self._labels[idx])
        except Exception:
            return None

    def save(self, filename):
        pass  # stub


# ── Internos do WiSARD ─────────────────────────────────────────────────────────

class _RAM:
    """Neurônio RAM: dicionário endereço → contagem de ativações."""

    __slots__ = ("_data",)

    def __init__(self):
        self._data = {}

    def train(self, address):
        self._data[address] = self._data.get(address, 0) + 1

    def activate(self, address):
        return 1 if address in self._data else 0

    def activate_bleach(self, address, b):
        """Ativa somente se contagem >= b (BBleaching)."""
        return 1 if self._data.get(address, 0) >= b else 0

    def count(self, address):
        return self._data.get(address, 0)

    def approx_bytes(self):
        return len(self._data) * 24


class _Discriminator:
    """Conjunto de RAMs representando um cluster/classe."""

    def __init__(self, n_rams, mapping):
        self._n_rams      = n_rams
        self._mapping     = mapping      # list[list[int]] — índices de bits por RAM
        self._rams        = [_RAM() for _ in range(n_rams)]
        self._train_count = 0            # amostras usadas no treino deste discriminador

    # Endereço: concatenação dos bits selecionados pelo mapeamento
    def _addr(self, bits, ram_idx):
        addr = 0
        for pos in self._mapping[ram_idx]:
            addr = (addr << 1) | int(bits[pos])
        return addr

    def train(self, bits):
        for i, ram in enumerate(self._rams):
            ram.train(self._addr(bits, i))
        self._train_count += 1

    def activated(self, bits):
        """Número de RAMs que ativaram (b=1)."""
        return sum(ram.activate(self._addr(bits, i)) for i, ram in enumerate(self._rams))

    def score(self, bits):
        """Fração de RAMs ativadas ∈ [0, 1]."""
        if self._n_rams == 0:
            return 0.0
        return self.activated(bits) / self._n_rams

    def score_bleach(self, bits, b: int):
        """Fração de RAMs com contagem >= b (BBleaching)."""
        if self._n_rams == 0:
            return 0.0
        act = sum(
            ram.activate_bleach(self._addr(bits, i), b)
            for i, ram in enumerate(self._rams)
        )
        return act / self._n_rams

    def weighted_score(self, bits):
        """Soma das contagens normalizada pelo total de treino deste discriminador."""
        total = max(self._train_count, 1)
        return sum(
            ram.count(self._addr(bits, i))
            for i, ram in enumerate(self._rams)
        ) / total

    def approx_bytes(self):
        return sum(r.approx_bytes() for r in self._rams)


# ── ClusWisard ────────────────────────────────────────────────────────────────

class ClusWisard:
    """
    ClusWisard — WiSARD com múltiplos discriminadores por classe.

    Parâmetros
    ----------
    addressSize : int
        Número de bits por endereço de RAM.
    minScore : float
        Score mínimo para aceitar uma classificação (0 = sem mínimo).
    threshold : int
        Número mínimo de RAMs ativadas para fundir com cluster existente.
        0 → sempre cria novo cluster; n_rams → só funde se totalmente coberto.
    discriminatorsLimit : int
        Máximo de clusters por classe (0 = ilimitado).
    """

    def __init__(self, addressSize, minScore=0.0, threshold=1, discriminatorsLimit=0):
        self._addr_size      = int(addressSize)
        self._min_score      = float(minScore)
        self._threshold      = int(threshold)
        self._disc_limit     = int(discriminatorsLimit)
        self._clusters: dict[str, list[_Discriminator]] = {}
        self._mapping        = None
        self._n_rams         = 0
        self._input_len      = 0

    # ── configuração do mapeamento aleatório ──────────────────────────────────

    def _init_mapping(self, input_len: int):
        if self._mapping is not None:
            return
        self._input_len = input_len
        rng = _random.Random(0)          # semente fixa conforme PLANO.md

        indices = list(range(input_len))
        rng.shuffle(indices)

        n_complete = input_len // self._addr_size
        remainder  = input_len  % self._addr_size

        self._mapping = [
            indices[i * self._addr_size:(i + 1) * self._addr_size]
            for i in range(n_complete)
        ]
        if remainder > 0:
            # Completa o último grupo com bits repetidos
            last = indices[n_complete * self._addr_size:]
            while len(last) < self._addr_size:
                last.append(rng.randint(0, input_len - 1))
            self._mapping.append(last)

        self._n_rams = len(self._mapping)

    def _new_disc(self):
        return _Discriminator(self._n_rams, self._mapping)

    # ── treinamento ───────────────────────────────────────────────────────────

    def train(self, dataset: DataSet):
        for i in range(len(dataset)):
            bits  = dataset[i].list()
            label = dataset.getLabel(i)

            if self._mapping is None:
                self._init_mapping(len(bits))

            discs = self._clusters.setdefault(label, [])

            if not discs:
                d = self._new_disc()
                d.train(bits)
                discs.append(d)
                continue

            # Encontra discriminador com mais RAMs ativadas
            scores = [d.activated(bits) for d in discs]
            best_i = max(range(len(scores)), key=lambda k: scores[k])

            if scores[best_i] >= self._threshold:
                discs[best_i].train(bits)
            elif self._disc_limit == 0 or len(discs) < self._disc_limit:
                d = self._new_disc()
                d.train(bits)
                discs.append(d)
            else:
                discs[best_i].train(bits)

    def trainUnsupervised(self, dataset: DataSet):
        self.train(dataset)

    # ── classificação ─────────────────────────────────────────────────────────

    def _label_score_bleach(self, bits, label, b: int) -> float:
        """Score máximo (entre discriminadores) com bleaching level b."""
        discs = self._clusters.get(label, [])
        if not discs:
            return 0.0
        return max(d.score_bleach(bits, b) for d in discs)

    def _label_weighted_score(self, bits, label) -> float:
        """Score ponderado pelas contagens (usado para AUC/ranking)."""
        discs = self._clusters.get(label, [])
        if not discs:
            return 0.0
        return max(d.weighted_score(bits) for d in discs)

    def classify(self, dataset: DataSet):
        """
        Classificação com score ponderado normalizado por amostras de treino.
        Para cada amostra, a classe com maior score médio por discriminador vence.
        """
        labels = list(self._clusters.keys())
        results = []
        for i in range(len(dataset)):
            bits    = dataset[i].list()
            w_scores = {lbl: self._label_weighted_score(bits, lbl) for lbl in labels}
            if not w_scores or max(w_scores.values()) == 0:
                results.append(labels[0] if labels else "")
                continue
            best = max(w_scores, key=w_scores.get)
            results.append(best if w_scores[best] >= self._min_score else "")
        return results

    def classifyUnsupervised(self, dataset: DataSet):
        return self.classify(dataset)

    def getAllScores(self, dataset: DataSet):
        """Retorna scores ponderados por contagem (proxy de probabilidade)."""
        labels = list(self._clusters.keys())
        result = []
        for i in range(len(dataset)):
            bits = dataset[i].list()
            result.append({lbl: self._label_weighted_score(bits, lbl) for lbl in labels})
        return result

    def rank(self, dataset: DataSet):
        return self.getAllScores(dataset)

    # ── utilitários ───────────────────────────────────────────────────────────

    def setMinScore(self, score):
        self._min_score = float(score)

    def setThreshold(self, threshold):
        self._threshold = int(threshold)

    def setDiscriminatorsLimit(self, limit):
        self._disc_limit = int(limit)

    def json(self):
        """Serialização do modelo (estrutura do mapeamento + metadados)."""
        data = {
            "addressSize"          : self._addr_size,
            "minScore"             : self._min_score,
            "threshold"            : self._threshold,
            "discriminatorsLimit"  : self._disc_limit,
            "inputLen"             : self._input_len,
            "nRams"                : self._n_rams,
            "classes"              : list(self._clusters.keys()),
            "nDiscriminators"      : {k: len(v) for k, v in self._clusters.items()},
            "totalRamEntries"      : {
                k: sum(len(r._data) for d in v for r in d._rams)
                for k, v in self._clusters.items()
            },
        }
        return _json.dumps(data)

    def getsizeof(self):
        return sum(d.approx_bytes() for discs in self._clusters.values() for d in discs)

    def getMentalImage(self):
        return {}

    def getMentalImages(self):
        return {}


# ── Termômetros ───────────────────────────────────────────────────────────────

class _ThermResult:
    """Resultado de transformação de termômetro (compatível com BinInput)."""
    __slots__ = ("_bits",)

    def __init__(self, bits):
        self._bits = bits

    def list(self):
        return self._bits


def _therm_encode_with_thresholds(val, thresholds):
    """1 bit por threshold: 1 se val > threshold, 0 caso contrário."""
    fval = float(val)
    return [1 if fval > t else 0 for t in thresholds]


class DynamicThermometer:
    """
    Termômetro simples com min/max por feature (equivalente ao Simple do original).

    Parameters
    ----------
    thermometerSizes : list[int]
        Número de bits por feature.
    minimum : list[float]
        Valor mínimo por feature.
    maximum : list[float]
        Valor máximo por feature.
    """

    def __init__(self, thermometerSizes, minimum=None, maximum=None):
        self._sizes = list(thermometerSizes)
        n = len(self._sizes)
        self._mins = list(minimum) if minimum is not None else [0.0] * n
        self._maxs = list(maximum) if maximum is not None else [1.0] * n
        # Thresholds uniformes entre min e max
        self._thresholds = []
        for i, (mn, mx, sz) in enumerate(zip(self._mins, self._maxs, self._sizes)):
            if mx == mn:
                mx = mn + 1.0
            step = (mx - mn) / sz
            self._thresholds.append([mn + step * j for j in range(sz)])

    def transform(self, sample):
        bits = []
        for val, thresholds in zip(sample, self._thresholds):
            bits.extend(_therm_encode_with_thresholds(val, thresholds))
        return _ThermResult(bits)

    def getSize(self):
        return sum(self._sizes)


class SimpleThermometer:
    """Termômetro simples para uma única feature."""

    def __init__(self, thermometerSize=2, minimum=0.0, maximum=1.0):
        self._size = thermometerSize
        mn, mx = float(minimum), float(maximum)
        if mx == mn:
            mx = mn + 1.0
        step = (mx - mn) / thermometerSize
        self._thresholds = [mn + step * j for j in range(thermometerSize)]

    def transform(self, sample):
        bits = _therm_encode_with_thresholds(sample[0], self._thresholds)
        return _ThermResult(bits)

    def getSize(self):
        return self._size


class DistributiveThermometer:
    """
    Termômetro com thresholds nos quantis equiespaçados da distribuição empírica.
    Precisa de fit(data_matrix) antes de transform().
    """

    def __init__(self, thermometerSize=32):
        self._size       = thermometerSize
        self._thresholds = None

    def fit(self, data_matrix):
        data = _np.array(data_matrix, dtype=float)
        quantile_positions = _np.linspace(0, 100, self._size + 2)[1:-1]
        self._thresholds = [
            _np.percentile(data[:, j], quantile_positions).tolist()
            for j in range(data.shape[1])
        ]

    def transform(self, sample):
        bits = []
        for val, thresholds in zip(sample, self._thresholds):
            bits.extend(_therm_encode_with_thresholds(val, thresholds))
        return _ThermResult(bits)

    def getThresholds(self):
        return self._thresholds

    def setThresholds(self, thresholds):
        self._thresholds = thresholds

    def getSize(self):
        return self._size


class GaussianThermometer:
    """
    Termômetro com thresholds na distribuição gaussiana ajustada por feature.
    Precisa de fit(data_matrix) antes de transform().
    """

    def __init__(self, thermometerSize=32):
        self._size       = thermometerSize
        self._thresholds = None

    def fit(self, data_matrix):
        from scipy.stats import norm as _norm
        data = _np.array(data_matrix, dtype=float)
        probs = _np.linspace(0, 1, self._size + 2)[1:-1]  # (0,1) exclusivo
        self._thresholds = []
        for j in range(data.shape[1]):
            col = data[:, j]
            mu, sigma = col.mean(), col.std()
            if sigma == 0:
                sigma = 1.0
            self._thresholds.append(
                [float(mu + sigma * _norm.ppf(p)) for p in probs]
            )

    def transform(self, sample):
        bits = []
        for val, thresholds in zip(sample, self._thresholds):
            bits.extend(_therm_encode_with_thresholds(val, thresholds))
        return _ThermResult(bits)

    def getThresholds(self):
        return self._thresholds

    def setThresholds(self, thresholds):
        self._thresholds = thresholds

    def getSize(self):
        return self._size


class ExponentialThermometer:
    """
    Termômetro com thresholds com espaçamento exponencial entre min e max.
    Precisa de fit(data_matrix) antes de transform().
    """

    def __init__(self, thermometerSize=32):
        self._size       = thermometerSize
        self._thresholds = None

    def fit(self, data_matrix):
        data = _np.array(data_matrix, dtype=float)
        self._thresholds = []
        for j in range(data.shape[1]):
            col = data[:, j]
            mn, mx = float(col.min()), float(col.max())
            if mx == mn:
                mx = mn + 1.0
            # Espaçamento quadrático (simula distribuição exponencial discreta)
            self._thresholds.append([
                mn + (mx - mn) * (i / self._size) ** 0.5
                for i in range(1, self._size + 1)
            ])

    def transform(self, sample):
        bits = []
        for val, thresholds in zip(sample, self._thresholds):
            bits.extend(_therm_encode_with_thresholds(val, thresholds))
        return _ThermResult(bits)

    def getThresholds(self):
        return self._thresholds

    def setThresholds(self, thresholds):
        self._thresholds = thresholds

    def getSize(self):
        return self._size


class StochasticThermometer:
    """Termômetro estocástico (stub)."""

    def __init__(self, thermometerSize=32):
        self._size       = thermometerSize
        self._thresholds = None

    def fit(self, data_matrix):
        dt = DistributiveThermometer(self._size)
        dt.fit(data_matrix)
        self._thresholds = dt.getThresholds()

    def transform(self, sample):
        bits = []
        for val, thresholds in zip(sample, self._thresholds):
            bits.extend(_therm_encode_with_thresholds(val, thresholds))
        return _ThermResult(bits)

    def getSize(self):
        return self._size


dataset_sufix = ".dataset"
