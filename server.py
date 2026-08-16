import os
import platform
import subprocess
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pipeline import Pipeline

CONFIG = Path(__file__).parent / "config.yaml"
DOCK = Path(__file__).parent / "dock.html"

app = FastAPI(title="obscut clipper")
cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
pipeline = Pipeline(cfg, verbose=False)


@app.get("/", response_class=HTMLResponse)
def dock():
    return DOCK.read_text(encoding="utf-8")


@app.get("/api/status")
def status():
    return pipeline.status()


@app.post("/api/start")
def start():
    return {"ok": pipeline.start()}


@app.post("/api/stop")
def stop():
    pipeline.stop()
    return {"ok": True}


@app.post("/api/signals/{name}")
async def toggle_signal(name: str, request: Request):
    body = await request.json()
    pipeline.set_signal(name, bool(body.get("enabled", True)))
    return {"ok": True}


@app.get("/api/clips")
def clips():
    out = Path(cfg["clipper"]["output_dir"])
    if not out.exists():
        return []
    files = sorted(out.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {"name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime}
        for p in files[:50]
    ]


@app.get("/api/logs")
def logs():
    return list(pipeline.logs)


@app.post("/api/open")
def open_folder():
    out = Path(cfg["clipper"]["output_dir"]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    cmd = {
        "Darwin": ["open", str(out)],
        "Linux": ["xdg-open", str(out)],
        "Windows": ["explorer", str(out)],
    }[system]
    subprocess.Popen(cmd)
    return {"ok": True}


@app.post("/api/quit")
def quit():
    pipeline.stop()
    os._exit(0)


if __name__ == "__main__":
    srv = cfg["server"]
    uvicorn.run(app, host=srv["host"], port=srv["port"], log_level="warning")