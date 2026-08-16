import os
import threading
import time
from collections import deque
from typing import Dict, Optional

from detectors.audio import YAMNetDetector
from detectors.source import MKVTail, StreamSource
from detectors.vocal import VocalSpike
from detectors.whisper import KeywordDetector
from engine.clipper import cut
from engine.score import MomentEngine


class Pipeline:
    """Pipeline completo de detecção, rodando em thread própria."""

    def __init__(self, cfg: Dict, verbose: bool = True, debug: bool = False,
                 no_model: bool = False, test_clip: bool = False):
        self.cfg = cfg
        self.verbose = verbose
        self.debug = debug
        self.no_model = no_model
        self.test_clip = test_clip
        self.hop = cfg["detector"]["hop_seconds"]
        self._recompute_signals()
        self.detector: Optional[YAMNetDetector] = None
        self.vocal: Optional[VocalSpike] = None
        self.kws: Optional[KeywordDetector] = None

        self.running = False
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.t = 0.0
        self.scores: Dict[str, float] = {}
        self.last_clip: Optional[str] = None
        self.clips_count = 0
        self.logs: deque = deque(maxlen=300)
        self.kw_score = 0.0
        self._last_kw_t = 0.0
        self._test_done = False

    def _log(self, msg: str) -> None:
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        self.logs.append(line)
        if self.verbose:
            print(line)

    def _recompute_signals(self) -> None:
        self.signals_cfg = {
            name: sig for name, sig in self.cfg["signals"].items()
            if name == "aplauso" or sig.get("enabled", True)
        }
        self.engine = MomentEngine(self.signals_cfg, self.cfg["clipper"])

    def _load_models(self) -> None:
        self._log("carregando modelos de IA (primeira vez demora)...")
        self.detector = YAMNetDetector(self.cfg["signals"]["aplauso"]["classes"])
        if "pregador" in self.cfg["signals"]:
            self.vocal = VocalSpike.from_cfg(self.cfg["signals"]["pregador"], self.hop)
        if "keywords" in self.cfg["signals"]:
            kws_cfg = self.cfg["signals"]["keywords"]
            self.kws = KeywordDetector(
                model_size=kws_cfg["model_size"],
                language=kws_cfg["language"],
                batch_seconds=kws_cfg["batch_seconds"],
                words=kws_cfg["words"],
                score_divisor=kws_cfg["score_divisor"],
            )
        self._log("modelos prontos")

    def set_signal(self, name: str, enabled: bool) -> None:
        if name not in self.cfg["signals"]:
            return
        self.cfg["signals"][name]["enabled"] = enabled
        self._recompute_signals()

    def start(self) -> bool:
        if self.running:
            return False
        self._stop.clear()
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def status(self) -> Dict:
        return {
            "running": self.running,
            "t": self.t,
            "scores": dict(self.scores),
            "signals": {
                name: (name == "aplauso" or sig.get("enabled", True))
                for name, sig in self.cfg["signals"].items()
            },
            "clips_count": self.clips_count,
            "last_clip": self.last_clip,
            "models": self.detector is not None,
        }

    def _run(self) -> None:
        rec = self.cfg["recording"]
        src = StreamSource(rec["stream_args"]) if rec["type"] == "stream" \
            else MKVTail(rec["file"], audio_track=rec["audio_track"])
        try:
            if not self.no_model:
                self._load_models()

            started = False
            read_some = False
            retries = 0
            while not self._stop.is_set():
                if not started:
                    if rec["type"] == "file" and not os.path.exists(rec["file"]):
                        self._log("aguardando arquivo nascer...")
                        time.sleep(2)
                        continue
                    src.start()
                    started = True
                    read_some = False
                    src_label = " ".join(rec["stream_args"]) if rec["type"] == "stream" else rec["file"]
                    self._log(f"ouvindo {src_label} — sinais: {', '.join(self.signals_cfg)}")

                chunk = src.read(self.hop)
                if chunk is None:
                    if not src.alive:
                        err = src.stderr_tail()
                        if read_some:
                            self._log("fim do arquivo — encerrando")
                            break
                        retries += 1
                        if retries > 10:
                            self._log(f"ffmpeg falhou sem dados: {err}")
                            break
                        self._log(f"ffmpeg saiu sem ler nada ({err.strip() or 'sem erro'}) — tentando de novo")
                        started = False
                        time.sleep(2)
                        continue
                    time.sleep(self.hop)
                    continue
                read_some = True
                self.t += self.hop

                if self.test_clip and not self._test_done and self.t >= self.cfg["test"]["clip_at"]:
                    self._test_done = True
                    test = self.cfg["test"]
                    clip = cut(rec["file"], self.cfg["clipper"]["output_dir"],
                               test["start"], test["end"], "teste")
                    self.clips_count += 1
                    self.last_clip = str(clip)
                    self._log(f"[teste] clip salvo: {clip}")
                    continue

                if self.detector is None:
                    continue

                scores = {"aplauso": self.detector.score(chunk)}
                speech = self.detector.speech_prob(chunk)
                if "pregador" in self.signals_cfg and self.vocal is not None:
                    scores["pregador"] = self.vocal.score(chunk, speech)
                if "keywords" in self.signals_cfg and self.kws is not None:
                    self.kws.push(chunk)
                    if self.t - self._last_kw_t >= self.kws.batch_seconds:
                        self.kw_score = self.kws.score()
                        self._last_kw_t = self.t
                    scores["keywords"] = self.kw_score
                self.scores = scores

                if self.debug:
                    self._log(f"t={self.t:7.1f}s " + " ".join(f"{k}={v:.2f}" for k, v in scores.items()))
                    continue

                event = self.engine.feed(self.t, scores)
                if event:
                    if rec["type"] == "stream":
                        self._log(f"momento {event['label']} detectado (clip não suportado em modo stream)")
                        continue
                    clip = cut(rec["file"], self.cfg["clipper"]["output_dir"],
                               event["start"], event["end"], event["label"])
                    self.clips_count += 1
                    self.last_clip = str(clip)
                    self._log(f"clip salvo: {clip}")
                elif self.verbose:
                    bars = " ".join(f"{k}={v:.2f}" for k, v in scores.items())
                    self._log(f"t={self.t:8.1f}s  {bars}")
        finally:
            src.stop()
            self.running = False
            self._log("pipeline encerrado")