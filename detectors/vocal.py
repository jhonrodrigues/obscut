import numpy as np

from typing import Dict


class VocalSpike:
    """Pico vocal: energia de fala acima do baseline recente.

    Score alto quando há Speech detectado (YAMNet) e a energia do trecho
    dispara muito acima da média móvel dos últimos segundos (pregador
    gritando, clímax da ministração).
    """

    def __init__(self, baseline_seconds: float, spike_factor: float,
                 speech_min: float, hop: float = 1.0):
        self.alpha = 1.0 / max(1.0, baseline_seconds / hop)
        self.baseline = 0.05
        self.spike_factor = spike_factor
        self.speech_min = speech_min
        self.hop = hop

    @classmethod
    def from_cfg(cls, cfg: Dict, hop: float) -> "VocalSpike":
        return cls(
            baseline_seconds=cfg["baseline_seconds"],
            spike_factor=cfg["spike_factor"],
            speech_min=cfg["speech_min"],
            hop=hop,
        )

    def score(self, chunk: np.ndarray, speech_prob: float) -> float:
        if speech_prob < self.speech_min:
            return 0.0
        energy = float(np.sqrt(np.mean(chunk ** 2)))
        ratio = energy / (self.baseline + 1e-9)
        self.baseline = self.alpha * energy + (1 - self.alpha) * self.baseline
        score = (ratio - 1.0) / (self.spike_factor - 1.0)
        return float(np.clip(score, 0.0, 1.0))