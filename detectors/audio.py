from pathlib import Path
from typing import List

import numpy as np
import tensorflow as tf  # noqa: F401  (registra ops antes do hub.load)
import tensorflow_hub as hub

_WINDOW = 15600  # YAMNet espera 0.975s de áudio = 15600 amostras @ 16kHz


def _load_class_indices(class_map_path: str, wanted: List[str]) -> List[int]:
    indices = []
    for row in Path(class_map_path).read_text(encoding="utf-8").splitlines()[1:]:
        parts = row.split(",")
        if len(parts) < 3:
            continue
        index, name = parts[0], parts[2]  # formato: index,mid,display_name
        if name in wanted:
            indices.append(int(index))
    return indices


class YAMNetDetector:
    """Pontua classes alvo do AudioSet (ex.: Applause) por janela de ~1s."""

    def __init__(self, classes: List[str]):
        self.model = hub.load("https://tfhub.dev/google/yamnet/1")
        class_map = self.model.class_map_path().numpy().decode("utf-8")
        self.target_indices = _load_class_indices(class_map, classes)
        if not self.target_indices:
            raise ValueError(f"nenhuma classe YAMNet encontrada para: {classes}")

    def score(self, chunk: np.ndarray) -> float:
        if chunk.shape[0] < _WINDOW:
            return 0.0
        wav = chunk[:_WINDOW][np.newaxis, :]
        scores = self.model(wav)[0].numpy()  # (1, 521) -> (521,)
        return float(scores[self.target_indices].max())