# Clipper de culto ao vivo (OBS + IA)

Detecta momentos de aplauso/canto na live enquanto rola e salva cortes
automaticamente. IA na mesma máquina do OBS.

```
OBS grava MKV contínuo → ffmpeg lê áudio do arquivo crescente
→ YAMNet pontua aplauso → estado de aplauso sustentado
→ ffmpeg extrai trecho → cultos/<data>_t<seg>_aplauso.mp4
```

## Stack (M1)

- OBS gravando em **MKV** (arquivo crescente, cortável em tempo real)
- Python 3.10+ / TensorFlow CPU / YAMNet (hub) para classificação de áudio
- ffmpeg para leitura do áudio e corte dos clips (`-c copy` = fast cut em keyframe)

## Setup

```bash
# 1. ffmpeg
sudo apt install ffmpeg

# 2. Python + deps (pesado: ~600MB TensorFlow CPU)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. OBS: ver obs-config/README-obs-setup.md (gravar MKV em ./grava/culto.mkv)
# 4. config.yaml: ajuste caminho do MKV, threshold, janelas
```

## Rodar

```bash
source .venv/bin/activate
python main.py
```

Log por segundo: `t=..s  aplauso=0.xx`. Clip salvo ao fim de aplauso
sustentado ≥ `min_duration_seconds`.

## Tuning rápido

| Parâmetro | O que faz |
|---|---|
| `threshold` | prob. YAMNet pra contar como aplauso (0.3 = sensível, 0.7 = só aplauso forte) |
| `min_sustain_seconds` | mínimo contínuo p/ não disparar com palminha única |
| `pre/post_seconds` | contexto antes/depois do momento no clip |
| `cooldown_seconds` | gap entre clips (evita flood de aplauso contínuo) |
| `classes` | troque por `["Singing"]`, `["Music"]` etc. do AudioSet |

## Roadmap

- **M1** (este) — aplauso → clip
- **M2** — score combinado (cooldown/dedup + pico vocal do pregador)
- **M3** — faster-whisper com keywords de culto + peso combinado
- **M4** — NDI como fonte de áudio alternativa + polimento

## Notas

- Corte em keyframe pode começar/terminar alguns frames antes/depois do
  ponto exato. Se precisar de corte milimétrico, troque `-c copy` por
  re-encode (`-c:v libx264 -crf 20`).
- `audio_track`: se OBS gravar em tracks separadas (mic/música), aponte o
  índice certo em `config.yaml`.