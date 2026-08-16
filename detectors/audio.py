import csv
from pathlib import Path
from typing import List

import numpy as np
import tensorflow as tf  # noqa: F401  (registra ops antes do hub.load)
import tensorflow_hub as hub

_WINDOW = 15600  # YAMNet espera 0.975s de áudio = 15600 amostras @ 16kHz


def _load_names(class_map_path: str) -> List[str]:
    names = []
    with open(class_map_path, encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            names.append(row[2])  # formato: index,mid,display_name
    return names


class YAMNetDetector:
    """Pontua classes alvo do AudioSet (ex.: Applause) por janela de ~1s."""

    def __init__(self, classes: List[str]):
        self.model = hub.load("https://tfhub.dev/google/yamnet/1")
        class_map = self.model.class_map_path().numpy().decode("utf-8")
        self.class_names = _load_names(class_map)
        self.target_indices = [
            i for i, name in enumerate(self.class_names) if name in classes
        ]
        if not self.target_indices:
            raise ValueError(f"nenhuma classe YAMNet encontrada para: {classes}")

    def scores(self, chunk: np.ndarray) -> np.ndarray:
        if chunk.shape[0] < _WINDOW:
            return np.zeros(len(self.class_names))
        wav = chunk[:_WINDOW]  # 1-D; YAMNet faz o framing internamente
        return self.model(wav)[0].numpy()[0]  # (1, 521) -> (521,)

    def score(self, chunk: np.ndarray) -> float:
        return float(self.scores(chunk)[self.target_indices].max())

    def top(self, chunk: np.ndarray, k: int = 5) -> List[str]:
        s = self.scores(chunk)
        idx = np.argsort(s)[::-1][:k]
        return [f"{self.class_names[i]}={s[i]:.2f}" for i in idx]