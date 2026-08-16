import argparse
import signal
import time

import yaml

from detectors.audio import YAMNetDetector
from detectors.source import AudioTail
from detectors.vocal import VocalSpike
from engine.clipper import cut
from engine.score import MomentEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="OBS live clipper — M2")
    parser.add_argument("-c", "--config", default="config.yaml")
    parser.add_argument("-f", "--file", help="override do caminho do MKV")
    parser.add_argument("--debug", action="store_true", help="mostra scores e top-5 classes")
    parser.add_argument("--no-model", action="store_true", help="não carrega YAMNet")
    parser.add_argument("--test-clip", action="store_true", help="força um clip em janela fixa")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.file:
        cfg["recording"]["file"] = args.file

    hop = cfg["detector"]["hop_seconds"]
    signals = {
        name: sig for name, sig in cfg["signals"].items()
        if name == "aplauso" or sig.get("enabled", True)
    }
    engine = MomentEngine(signals, cfg["clipper"])

    detector = None
    vocal = None
    if not args.no_model:
        detector = YAMNetDetector(cfg["signals"]["aplauso"]["classes"])
        if "pregador" in signals:
            vocal = VocalSpike.from_cfg(signals["pregador"], hop)

    src = AudioTail(
        cfg["recording"]["file"],
        audio_track=cfg["recording"]["audio_track"],
    )
    stop = {"flag": False}
    signal.signal(signal.SIGINT, lambda *_: stop.__setitem__("flag", True))
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__("flag", True))

    print(f"[clipper] ouvindo {cfg['recording']['file']} (track a:{cfg['recording']['audio_track']})")
    print(f"[clipper] sinais: {', '.join(signals)}")
    src.start()

    t = 0.0
    test_done = False
    while not stop["flag"]:
        chunk = src.read(hop)
        if chunk is None:
            if not src.alive:
                print("[clipper] fim do arquivo — encerrando")
                break
            time.sleep(hop)
            continue
        t += hop

        if args.test_clip and not test_done and t >= cfg["test"]["clip_at"]:
            test_done = True
            test = cfg["test"]
            clip = cut(
                cfg["recording"]["file"],
                cfg["clipper"]["output_dir"],
                test["start"],
                test["end"],
                "teste",
            )
            print(f"[teste] clip salvo: {clip}")
            continue

        if detector is None:
            continue

        scores = {"aplauso": detector.score(chunk)}
        speech = detector.speech_prob(chunk)
        if vocal is not None:
            scores["pregador"] = vocal.score(chunk, speech)

        if args.debug:
            parts = "  ".join(f"{k}={v:.2f}" for k, v in scores.items())
            print(f"t={t:7.1f}s  [{parts}]  | " + "  ".join(detector.top(chunk)))
            continue

        event = engine.feed(t, scores)
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
            bars = " ".join(f"{k}={v:.2f}" for k, v in scores.items())
            print(f"t={t:8.1f}s  {bars}")

    src.stop()
    print("[clipper] encerrado")


if __name__ == "__main__":
    main()