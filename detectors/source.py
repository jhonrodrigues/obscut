import subprocess
from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np


class AudioSource(ABC):
    """Fonte de áudio: lê PCM 16k mono em janelas de `seconds` segundos."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._proc: Optional[subprocess.Popen] = None

    @abstractmethod
    def _cmd(self) -> List[str]:
        ...

    def start(self) -> None:
        self._proc = subprocess.Popen(
            self._cmd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def read(self, seconds: float) -> Optional[np.ndarray]:
        n_bytes = int(self.sample_rate * seconds * 2)
        data = self._proc.stdout.read(n_bytes)
        if not data or len(data) < n_bytes:
            return None
        raw = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        return raw

    def stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def stderr_tail(self) -> str:
        if self._proc and self._proc.stderr:
            try:
                return self._proc.stderr.read().decode("utf-8", "replace")[-500:]
            except Exception:
                return ""
        return ""


class MKVTail(AudioSource):
    """Lê áudio do MKV crescente (gravação contínua do OBS)."""

    def __init__(self, file_path: str, audio_track: int = 0, sample_rate: int = 16000):
        super().__init__(sample_rate)
        self.file_path = file_path
        self.audio_track = audio_track

    def _cmd(self) -> List[str]:
        return [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-i", self.file_path,
            "-map", f"0:a:{self.audio_track}",
            "-ac", "1", "-ar", str(self.sample_rate),
            "-f", "s16le", "pipe:1",
        ]


class StreamSource(AudioSource):
    """Lê áudio de qualquer entrada do ffmpeg (URL, dispositivo, NDI se
    o ffmpeg tiver libndi_newtek, lavfi pra testes...)."""

    def __init__(self, input_args: List[str], sample_rate: int = 16000):
        super().__init__(sample_rate)
        self.input_args = input_args

    def _cmd(self) -> List[str]:
        return [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            *self.input_args,
            "-ac", "1", "-ar", str(self.sample_rate),
            "-f", "s16le", "pipe:1",
        ]