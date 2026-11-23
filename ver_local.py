#!/usr/bin/env python3
"""Monta o painel na pasta site/ (como o GitHub faz) e abre no navegador do seu computador.

Uso:  python ver_local.py https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/
          usa os dados já publicados no seu GitHub Pages (rápido, não baixa nada do portal)
      python ver_local.py
          usa os dados da pasta saida/ (rode antes: python atualizar.py)
Para parar, aperte Ctrl+C no terminal.
"""
import functools
import http.server
import shutil
import sys
import urllib.request
import webbrowser
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SITE = AQUI / "site"
ARQUIVOS = ["formas.json", "cumprimento.json", "referencia.json", "municipios_al.json"]

(SITE / "dados").mkdir(parents=True, exist_ok=True)
if len(sys.argv) > 1:
    base = sys.argv[1].rstrip("/") + "/dados/"
    for nome in ARQUIVOS:
        print(f"baixando {base}{nome}")
        urllib.request.urlretrieve(base + nome, SITE / "dados" / nome)
else:
    faltam = [nome for nome in ARQUIVOS if not (AQUI / "saida" / nome).exists()]
    if faltam:
        sys.exit(f"Faltam arquivos em saida/: {', '.join(faltam)}.\n"
                 "Rode antes 'python atualizar.py' ou passe o endereço do seu GitHub Pages.")
    for nome in ARQUIVOS:
        shutil.copy(AQUI / "saida" / nome, SITE / "dados" / nome)

# mesma montagem do .github/workflows/publicar.yml: moldura + página do painel + funções do painel
casca = (AQUI / "pages" / "casca.html").read_text(encoding="utf-8")
assert "<!-- PAINEL -->" in casca, "pages/casca.html sem o marcador <!-- PAINEL -->"
painel = (AQUI / "painel" / "index.html").read_text(encoding="utf-8")
(SITE / "index.html").write_text(casca.replace("<!-- PAINEL -->", "<!-- PAINEL -->\n" + painel, 1), encoding="utf-8")
shutil.copy(AQUI / "pages" / "dash.js", SITE / "dash.js")

# o navegador não deixa a página ler os dados direto do disco, então serve a pasta num endereço local
Servidor = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
try:
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 8000), Servidor)
except OSError:  # porta 8000 ocupada: usa uma livre
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Servidor)
url = f"http://localhost:{servidor.server_address[1]}/"
print(f"\nPainel em {url}  (Ctrl+C para parar)")
webbrowser.open(url)
try:
    servidor.serve_forever()
except KeyboardInterrupt:
    print("Parado.")
