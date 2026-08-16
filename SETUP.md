# Setup do zero (máquina nova)

Passos pra qualquer Mac novo que for rodar o clipper. Não esquece: `git
pull` traz só o código — deps, ffmpeg e modelos baixam separado.

## 1. Pré-requisitos

```bash
# Homebrew (só se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# ffmpeg + Python 3.12
brew install ffmpeg python@3.12
```

Feche e abra o Terminal depois de instalar o Homebrew (pra entrar no PATH).

## 2. Clone e venv

```bash
git clone https://github.com/jhonrodrigues/obscut.git && cd obscut
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
```

## 3. Dependências

```bash
# necessário pro tensorflow-hub (pkg_resources removido do setuptools novo)
pip install "setuptools<81"
pip install -r requirements.txt    # pesado: TF (~600MB) + faster-whisper
```

## 4. Primeira execução

Modelos baixam sozinhos na primeira vez (precisa internet):
- YAMNet (~20MB, tfhub.dev)
- whisper small (~460MB, HuggingFace)

Teste rápido do pipeline inteiro (corta um clip sem IA):

```bash
python main.py -f grava/teste.mkv --no-model --test-clip
```

## 5. Teste com áudio real

```bash
# grava 30s do mic enquanto você bate palma (~8-12s) e fala alto (~20-24s)
ffmpeg -f avfoundation -i ":0" -t 30 -c:a aac grava/teste2.mkv

# processa com todos os sinais
python main.py -f grava/teste2.mkv
```

Se `:0` não for o mic, lista os dispositivos:
`ffmpeg -f avfoundation -list_devices true -i ""`

## 6. Live de verdade (OBS)

1. `obs-config/README-obs-setup.md` — OBS gravando **MKV** em
   `./grava/culto.mkv`
2. `python main.py` rodando antes de iniciar a gravação
3. OBS inicia gravação, live rola, clips nascem em `cultos/`

## Config

Tudo em `config.yaml`: caminho/entrada do áudio, limiares, janelas,
keywords e pesos. Ver tabela de tuning no `README.md`.