#!/usr/bin/env bash
# Para o servidor do painel
pkill -f "python server.py" 2>/dev/null && echo "servidor parado" || echo "nenhum servidor rodando"