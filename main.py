import argparse
import time

import yaml

from pipeline import Pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="OBS live clipper — CLI")
    parser.add_argument("-c", "--config", default="config.yaml")
    parser.add_argument("-f", "--file", help="override do caminho do MKV")
    parser.add_argument("--debug", action="store_true", help="mostra scores por segundo")
    parser.add_argument("--no-model", action="store_true", help="não carrega modelos de IA")
    parser.add_argument("--test-clip", action="store_true", help="força um clip em janela fixa")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.file:
        cfg["recording"]["file"] = args.file

    pipe = Pipeline(cfg, verbose=True, debug=args.debug,
                    no_model=args.no_model, test_clip=args.test_clip)
    pipe.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    pipe.stop()
    print(f"[clipper] encerrado — {pipe.clips_count} clips gerados")


if __name__ == "__main__":
    main()