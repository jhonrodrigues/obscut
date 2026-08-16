# Setup OBS para o clipper

## 1. Gravação

1. **Configurações → Saída → Gravação**
   - Formato: **MKV** (essential: arquivo crescente é lido pelo clipper em tempo real)
   - Caminho: pasta `./grava/` do repo
   - Nome: fixo, ex.: `culto.mkv`
2. **Configurações → Avançado**
   - Desmarque "Fechar arquivo ao iniciar/parar gravação" se aplicável
   - Se gravar tracks separadas (mic / música), confira o índice no
     `config.yaml` → `audio_track`
3. Use uma **cena** com as fontes do culto (câmera + captura + overlay).

## 2. Fluxo de uso

1. `python main.py` rodando
2. OBS: **iniciar gravação** (arquivo `culto.mkv` nasce e cresce)
3. Clipper consome o áudio do arquivo crescente e gera clips em `cultos/`
4. Ao fim: parar gravação e Ctrl+C no clipper

## 3. Dica: gravação longa

MKV aguenta horas. Se quiser dividir em arquivos (por culto), use a opção
"Separar arquivos por" no OBS e reinicie o clipper a cada novo MKV — ou
apenas mantenha um arquivo só e deixe o clipper cortar.

## 4. WebSocket (opcional, p/ M2+)

Para o clipper iniciar/parar gravação ou consultar status do OBS, ative
`Ferramentas → WebSocket Server Settings` e anote porta/senha. Não é
necessário no M1.