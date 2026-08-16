import subprocess
import time
from pathlib import Path


def cut(source: str, output_dir: str, start: float, end: float, label: str) -> Path:
    """Extrai [start, end] do MKV crescente. -c copy = fast cut em keyframe."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = out_dir / f"{ts}_t{int(start)}s_{label}.mp4"
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-ss", f"{start:.2f}", "-to", f"{end:.2f}",
        "-i", source,
        "-c", "copy", "-avoid_negative_ts", "make_zero",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out