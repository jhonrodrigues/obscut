#!/usr/bin/env bash
# Sobe o servidor do painel em background. Log em server.log
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
nohup python server.py > server.log 2>&1 &
echo "servidor iniciado (pid $!) — http://127.0.0.1:$(grep -A2 'server:' config.yaml | grep port | grep -o '[0-9]*')"
echo "log: server.log"