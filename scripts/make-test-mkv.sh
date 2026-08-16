#!/usr/bin/env bash
# Gera um MKV de teste com "aplauso" sintético (ruído marrom com tremolo)
# em janelas conhecidas, pra testar o pipeline sem OBS.
#
# Janelas de aplauso: t=8..12s e t=22..27s.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p grava

ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "anoisesrc=color=brown:duration=40:amplitude=0.5" \
  -af "tremolo=f=5:d=1,volume=enable='between(t,8,12)+between(t,22,27)':volume=2,volume=enable='not(between(t,8,12)+between(t,22,27))':volume=0.08" \
  -c:a aac -b:a 128k \
  grava/teste.mkv

echo "ok: grava/teste.mkv (aplausos em 8-12s e 22-27s)"