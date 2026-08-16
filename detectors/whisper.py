import unicodedata
from typing import Dict, List, Optional

import numpy as np

_WINDOW = 15600


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


class KeywordDetector:
    """Transcreve lotes de áudio com faster-whisper e pontua keywords.

    Score = soma dos pesos das keywords encontradas / divisor, clipado em
    [0,1]. Keyword forte (peso == divisor) dispara sozinha; keyword fraca
    ("amém") sozinha fica abaixo do limiar.
    """

    def __init__(self, model_size: str, language: str, batch_seconds: float,
                 words: Dict[str, float], score_divisor: float):
        from faster_whisper import WhisperModel  # import pesado, lazy

        self.batch_seconds = batch_seconds
        self.language = language
        self.words = {_norm(k): v for k, v in words.items()}
        self.divisor = max(1.0, score_divisor)
        self._buf = np.zeros(0, dtype=np.float32)
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def push(self, chunk: np.ndarray) -> None:
        self._buf = np.concatenate([self._buf, chunk])
        maxlen = int(self.batch_seconds * 16000)
        if len(self._buf) > maxlen:
            self._buf = self._buf[-maxlen:]

    def score(self) -> float:
        audio = self._buf
        if len(audio) < 16000:  # menos de 1s: nada a transcrever
            return 0.0
        segments, _ = self.model.transcribe(
            audio, language=self.language, beam_size=1
        )
        text = _norm(" ".join(s.text for s in segments))
        total = sum(w for word, w in self.words.items() if word in text)
        return float(min(1.0, total / self.divisor))