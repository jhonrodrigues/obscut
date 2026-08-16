# Setup OBS para o clipper

## 1. Gravação

**Configurações → Saída → Modo de Saída: Avançado → aba Gravação:**

- Tipo: **Padrão**
- Caminho da gravação: `/Users/jonathan/obscut/grava` (a pasta `grava/` do repo)
- Formato de gravação: **MKV (Matroska)** — essential: arquivo crescente é
  lido pelo clipper em tempo real
- Formatação de nome de arquivo: `culto` — só o nome, **sem macros**
  (`%Y%m%d` etc.) pra sempre gravar em `culto.mkv`
- Se o arquivo existir: **Sobrescrever** (garante MKV novo a cada gravação)
- Video encoder: Apple VT H264/H265 · Audio encoder: AAC

**Configurações → Avançado:**

- Se gravar tracks separadas (mic / música), confira o índice no
  `config.yaml` → `audio_track`

Use uma **cena** com as fontes do culto (câmera + captura + overlay).
Antes de cada gravação: `rm -f grava/culto.mkv` (garante arquivo zerado).

## 2. Fluxo de uso

1. `python main.py` rodando (CLI) — ou painel visual, seção 5
2. OBS: **iniciar gravação** (arquivo `culto.mkv` nasce e cresce)
3. Clipper consome o áudio do arquivo crescente e gera clips em `cultos/`
4. Ao fim: parar gravação e Ctrl+C no clipper

## 3. Dica: gravação longa

MKV aguenta horas. Se quiser dividir em arquivos (por culto), use a opção
"Separar arquivos por" no OBS e reinicie o clipper a cada novo MKV — ou
apenas mantenha um arquivo só e deixe o clipper cortar.

## 4. WebSocket (opcional)

Para o clipper iniciar/parar gravação ou consultar status do OBS, ative
`Ferramentas → WebSocket Server Settings` e anote porta/senha. Não é
necessário pro uso normal.

## 5. Painel visual (Browser Dock)

1. Terminal: `python server.py` (API em `http://127.0.0.1:8765`)
2. OBS: menu **Dock → Custom Browser Docks** → **Add Dock**
   - Nome: `obscut`
   - URL: `http://127.0.0.1:8765`
   - Largura: `320`, Salvar
3. O painel aparece como janela acoplável no OBS com:
   - **▶ Iniciar / ■ Parar** o pipeline
   - **Scores ao vivo** dos sinais (aplauso/pregador/keywords) + toggle
   - **Lista de clips** recentes e **abrir pasta**
   - Log em tempo real
4. Primeiro "Iniciar" carrega os modelos (YAMNet + whisper) — o badge
   mostra "carregando modelos…" até ficar pronto.

> Para painel ficar aberto sempre: Dock → Custom Browser Docks → bloqueie
> o dock (cadeado) pra não fechar junto com o painel de cenas.