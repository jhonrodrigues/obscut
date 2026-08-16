from typing import Dict, Optional


class MomentEngine:
    """Máquina de estados: detecta aplauso sustentado e agenda clip."""

    def __init__(self, cfg: Dict):
        det = cfg["detector"]
        clip = cfg["clipper"]
        self.threshold = det["threshold"]
        self.min_sustain = det["min_sustain_seconds"]
        self.pre = clip["pre_seconds"]
        self.post = clip["post_seconds"]
        self.min_duration = clip["min_duration_seconds"]
        self.cooldown = clip["cooldown_seconds"]
        self.label = clip.get("label", "momento")
        self._active = False
        self._start: Optional[float] = None
        self._cooldown_until = 0.0

    def feed(self, t: float, prob: float) -> Optional[Dict]:
        if t < self._cooldown_until:
            return None
        if prob >= self.threshold:
            if not self._active:
                self._active = True
                self._start = t
            return None

        if self._active:
            self._active = False
            dur = t - self._start
            if dur >= self.min_duration:
                self._cooldown_until = t + self.cooldown
                return {
                    "start": max(0.0, self._start - self.pre),
                    "end": t + self.post,
                    "label": self.label,
                }
        return None