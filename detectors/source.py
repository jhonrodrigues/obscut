import subprocess
from typing import Optional

import numpy as np


class AudioTail:
    """Lê áudio do MKV crescente (gravação contínua do OBS) via ffmpeg."""

    def __init__(self, file_path: str, audio_track: int = 0, sample_rate: int = 16000):
        self.file_path = file_path
        self.audio_track = audio_track
        self.sample_rate = sample_rate
        self._proc: Optional[subprocess.Popen] = None

    def start(self) -> None:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-i", self.file_path,
            "-map", f"0:a:{self.audio_track}",
            "-ac", "1", "-ar", str(self.sample_rate),
            "-f", "s16le", "pipe:1",
        ]
        self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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