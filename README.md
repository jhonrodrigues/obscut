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
| `signals.aplauso.threshold` | prob. YAMNet pra contar como aplauso (0.3 = sensível, 0.7 = forte) |
| `signals.aplauso.min_sustain` | mínimo contínuo p/ não disparar com palminha única |
| `signals.pregador.threshold` | pico vocal do pregador (energia de fala acima do baseline) |
| `signals.pregador.spike_factor` | quanto acima da média a fala precisa estar (2.5 = 2.5x) |
| `signals.pregador.speech_min` | prob. mínima de Speech pra considerar fala |
| `pre/post_seconds` | contexto antes/depois do momento no clip (por sinal) |
| `clipper.cooldown_seconds` | gap entre clips (evita flood; compartilhado entre sinais) |
| `signals.aplauso.classes` | classes AudioSet alvo (Applause, Clapping) |

## Roadmap

- **M1** ✅ — aplauso → clip (pipeline completo validado)
- **M2** (este) — pico vocal do pregador + score multi-sinal
- **M3** — faster-whisper com keywords de culto + peso combinado
- **M4** — NDI como fonte de áudio alternativa + polimento

## Notas

- Corte em keyframe pode começar/terminar alguns frames antes/depois do
  ponto exato. Se precisar de corte milimétrico, troque `-c copy` por
  re-encode (`-c:v libx264 -crf 20`).
- `audio_track`: se OBS gravar em tracks separadas (mic/música), aponte o
  índice certo em `config.yaml`.