#!/usr/bin/env python3
"""Gera um único arquivo HTML com o painel, os dados e a biblioteca de gráficos dentro.
Abre com dois cliques, sem internet, sem Python e sem servidor.

Uso:  python montar_offline.py [arquivo.html]    (padrão: painel-offline.html; usa os dados de saida/)
"""
import json
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
D3 = "https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"
FONTES = {"formas": "formas.json", "cumprimento": "cumprimento.json", "referencia": "referencia.json",
          "municipios_geo": "municipios_al.json"}
destino = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "painel-offline.html"


def script(js):
    return "<script>" + js.replace("</script", "<\\/script") + "</script>"  # não fecha a tag antes da hora


with urllib.request.urlopen(D3, timeout=60) as r:
    d3 = r.read().decode("utf-8")
dados = {id_: json.loads((AQUI / "saida" / arq).read_text(encoding="utf-8")) for id_, arq in FONTES.items()}
# "<" escapado dentro do JSON: nenhum texto dos dados consegue abrir ou fechar uma tag
dados_js = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

html = (AQUI / "pages" / "casca.html").read_text(encoding="utf-8")
trocas = [
    (f'<script src="{D3}"></script>', script(d3)),
    ('<script src="dash.js"></script>', script((AQUI / "pages" / "dash.js").read_text(encoding="utf-8"))),
    ("{formas: 'dados/formas.json', cumprimento: 'dados/cumprimento.json', referencia: 'dados/referencia.json', "
     "municipios_geo: 'dados/municipios_al.json'}", "DADOS_PAINEL"),
    ("<body>", "<body>\n<script>window.DADOS_PAINEL = " + dados_js + ";</script>"),
    ("<!-- PAINEL -->", "<!-- PAINEL -->\n" + (AQUI / "painel" / "index.html").read_text(encoding="utf-8")),
]
for velho, novo in trocas:
    assert html.count(velho) == 1, f"não achei uma vez só em pages/casca.html: {velho[:70]}"
    html = html.replace(velho, novo)
destino.write_text(html, encoding="utf-8")
print(f"{destino}: {destino.stat().st_size / 1e6:.1f} MB")
