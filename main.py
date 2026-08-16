import argparse
import signal
import sys
import time

import yaml

from detectors.audio import YAMNetDetector
from detectors.source import AudioTail
from engine.clipper import cut
from engine.score import MomentEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="OBS live clipper — M1")
    parser.add_argument("-c", "--config", default="config.yaml")
    parser.add_argument("-f", "--file", help="override do caminho do MKV")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.file:
        cfg["recording"]["file"] = args.file

    src = AudioTail(
        cfg["recording"]["file"],
        audio_track=cfg["recording"]["audio_track"],
    )
    detector = YAMNetDetector(cfg["detector"]["classes"])
    engine = MomentEngine(cfg)

    stop = {"flag": False}
    signal.signal(signal.SIGINT, lambda *_: stop.__setitem__("flag", True))
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__("flag", True))

    hop = cfg["detector"]["hop_seconds"]
    print(f"[clipper] ouvindo {cfg['recording']['file']} (track a:{cfg['recording']['audio_track']})")
    src.start()

    t = 0.0
    while not stop["flag"]:
        chunk = src.read(hop)
        if chunk is None:
            if not src.alive:
                print("[clipper] fim do arquivo — encerrando")
                break
            time.sleep(hop)
            continue
        prob = detector.score(chunk)
        t += hop
        event = engine.feed(t, prob)
        if event:
            clip = cut(
                cfg["recording"]["file"],
                cfg["clipper"]["output_dir"],
                event["start"],
                event["end"],
                event["label"],
            )
            print(f"[clipper] clip salvo: {clip}")
        else:
            print(f"t={t:8.1f}s  aplauso={prob:.2f}")

    src.stop()
    print("[clipper] encerrado")


if __name__ == "__main__":
    main()