import argparse
import signal
import time

import yaml

from detectors.audio import YAMNetDetector
from detectors.source import MKVTail, StreamSource
from detectors.vocal import VocalSpike
from detectors.whisper import KeywordDetector
from engine.clipper import cut
from engine.score import MomentEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="OBS live clipper — M4")
    parser.add_argument("-c", "--config", default="config.yaml")
    parser.add_argument("-f", "--file", help="override do caminho do MKV")
    parser.add_argument("--debug", action="store_true", help="mostra scores e top-5 classes")
    parser.add_argument("--no-model", action="store_true", help="não carrega modelos de IA")
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
    kws = None
    if not args.no_model:
        detector = YAMNetDetector(cfg["signals"]["aplauso"]["classes"])
        if "pregador" in signals:
            vocal = VocalSpike.from_cfg(signals["pregador"], hop)
        if "keywords" in signals:
            kws_cfg = signals["keywords"]
            kws = KeywordDetector(
                model_size=kws_cfg["model_size"],
                language=kws_cfg["language"],
                batch_seconds=kws_cfg["batch_seconds"],
                words=kws_cfg["words"],
                score_divisor=kws_cfg["score_divisor"],
            )

    if cfg["recording"]["type"] == "stream":
        src = StreamSource(cfg["recording"]["stream_args"])
        src_label = "stream: " + " ".join(cfg["recording"]["stream_args"])
    else:
        src = MKVTail(
            cfg["recording"]["file"],
            audio_track=cfg["recording"]["audio_track"],
        )
        src_label = cfg["recording"]["file"]

    stop = {"flag": False}
    signal.signal(signal.SIGINT, lambda *_: stop.__setitem__("flag", True))
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__("flag", True))

    print(f"[clipper] ouvindo {src_label}")
    print(f"[clipper] sinais: {', '.join(signals)}")
    src.start()

    clips = 0
    t = 0.0
    kw_score = 0.0
    last_kw_t = 0.0
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
        if kws is not None:
            kws.push(chunk)
            if t - last_kw_t >= kws.batch_seconds:
                kw_score = kws.score()
                last_kw_t = t
            scores["keywords"] = kw_score

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
            clips += 1
            print(f"[clipper] clip salvo: {clip}")
        else:
            bars = " ".join(f"{k}={v:.2f}" for k, v in scores.items())
            print(f"t={t:8.1f}s  {bars}")

    src.stop()
    print(f"[clipper] encerrado — {clips} clips gerados")


if __name__ == "__main__":
    main()