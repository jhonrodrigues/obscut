#!/usr/bin/env bash
# Gera um MKV de teste com "aplauso" sintético (rajadas de ruído branco,
# som de palma mais realista que tremolo) em janelas conhecidas.
#
# Janelas de aplauso: t=8..12s e t=22..27s.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p grava

ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "aevalsrc=expr='0.8*random(0)*lt(mod(n,3600),400)*if(between(t,8,12)+between(t,22,27),1,0.05)':s=44100:d=40" \
  -c:a aac -b:a 128k \
  grava/teste.mkv

echo "ok: grava/teste.mkv (aplausos em 8-12s e 22-27s)"