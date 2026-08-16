# Clipper de culto ao vivo (OBS + IA)

Detecta momentos de aplauso, pico vocal do pregador e keywords de culto
na live enquanto rola e salva cortes automaticamente. IA na mesma máquina
do OBS.

```
OBS grava MKV contínuo (ou entrada NDI/URL via ffmpeg)
→ YAMNet pontua aplauso + fala
→ pico vocal (energia acima do baseline) + faster-whisper por keywords
→ engine multi-sinal sustenta o melhor momento e agenda clip
→ ffmpeg extrai trecho → cultos/<data>_t<seg>_<sinal>.mp4
```

## Stack

- OBS gravando em **MKV** (arquivo crescente, cortável em tempo real)
- Python 3.10+ / TensorFlow CPU / **YAMNet** (aplauso, fala)
- **faster-whisper** (keywords de culto, CPU int8)
- ffmpeg para leitura do áudio e corte dos clips (`-c copy` = fast cut)

## Setup

Setup completo pra máquina nova (Mac, Homebrew, deps, primeira execução):
ver **[SETUP.md](SETUP.md)**.

```bash
# resumo Linux
sudo apt install ffmpeg
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # pesado: TF (~600MB) + whisper model
```

OBS: ver `obs-config/README-obs-setup.md` (gravar MKV em `./grava/culto.mkv`).
Primeira execução baixa modelos YAMNet (~20MB) e whisper small (~460MB).

## Rodar

```bash
source .venv/bin/activate
python main.py            # CLI: com o MKV do OBS rolando
python server.py          # painel visual no OBS (Browser Dock, seção abaixo)
python main.py --debug    # mostra scores por segundo
python main.py --no-model --test-clip  # valida o corte sem IA (smoke test)
```

## Painel visual no OBS (Browser Dock)

`python server.py` sobe API local (`http://127.0.0.1:8765`) com um dock
HTML. No OBS: **Dock → Custom Browser Docks** → Add Dock → URL
`http://127.0.0.1:8765`. Painel com botões iniciar/parar, scores ao vivo,
toggle de sinais, lista de clips e log. Detalhes em
`obs-config/README-obs-setup.md` seção 5.

## Sinais

| Sinal | Detecta | Como |
|---|---|---|
| `aplauso` | palmas/congregação | YAMNet `Applause`/`Clapping` |
| `pregador` | clímax de fala | Speech + energia acima do baseline |
| `keywords` | frases de culto | faster-whisper + pesos |

Keyword score = soma dos pesos / `score_divisor`. Keyword forte
(`glória a deus`=8) dispara sozinha; fraca (`amém`=1) só soma.

## Entradas (`recording.type`)

- `file` — MKV crescente do OBS (padrão)
- `stream` — qualquer entrada ffmpeg: NDI (ffmpeg com `libndi_newtek`),
  URL, dispositivo. Ex. no `config.yaml`:
  - NDI: `["-f", "libndi_newtek", "-i", "NomeCanal"]`
  - teste: `["-f", "lavfi", "-i", "sine=frequency=440:duration=30"]`

## Tuning rápido

| Parâmetro | O que faz |
|---|---|
| `signals.*.threshold` | limiar do sinal (0.5 padrão; baixe pra sensível) |
| `signals.*.min_sustain` | mínimo contínuo pra não disparar falso positivo |
| `signals.*.pre/post_seconds` | contexto antes/depois no clip (por sinal) |
| `signals.pregador.spike_factor` | quanto acima do baseline a fala precisa estar |
| `signals.keywords.batch_seconds` | janela de transcrição do whisper |
| `signals.keywords.words` | keywords + pesos |
| `clipper.cooldown_seconds` | gap entre clips (compartilhado) |

## Notas

- Corte em keyframe pode começar/terminar alguns frames antes/depois do
  ponto exato. Corte milimétrico: troque `-c copy` por re-encode
  (`-c:v libx264 -crf 20`).
- `audio_track`: se OBS gravar em tracks separadas (mic/música), aponte o
  índice certo.