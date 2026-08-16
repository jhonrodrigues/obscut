from typing import Dict, List, Optional


class MomentEngine:
    """Máquina de estados multi-sinal.

    Sustenta o melhor sinal acima do limiar; quando cai, agenda clip se
    durou o mínimo. Cooldown compartilhado entre sinais (evita duplicar
    o mesmo momento como aplauso e pregador).
    """

    def __init__(self, signals: Dict, clipper: Dict):
        self.sigs = signals
        self.cooldown = clipper["cooldown_seconds"]
        self._active: Optional[str] = None
        self._start: Optional[float] = None
        self._cooldown_until = 0.0

    def feed(self, t: float, scores: Dict[str, float]) -> Optional[Dict]:
        if t < self._cooldown_until:
            return None

        above = {
            name: val for name, val in scores.items()
            if val >= self.sigs[name]["threshold"]
        }
        if above:
            best = max(above, key=above.get)
            if self._active is None:
                self._active = best
                self._start = t
            return None

        if self._active is not None:
            name = self._active
            self._active = None
            sig = self.sigs[name]
            dur = t - self._start
            if dur >= sig["min_sustain"]:
                self._cooldown_until = t + self.cooldown
                return {
                    "start": max(0.0, self._start - sig["pre_seconds"]),
                    "end": t + sig["post_seconds"],
                    "label": name,
                }
        return None