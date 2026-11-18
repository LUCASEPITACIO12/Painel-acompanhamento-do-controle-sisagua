#!/usr/bin/env python3
"""Atualiza os dados do painel "Controle SISAGUA Alagoas".

1. Baixa do Portal de Dados Abertos do SUS os arquivos nacionais do SISAGUA e guarda só as linhas de AL (pasta dados/).
2. Cruza, por forma de abastecimento, o plano de amostragem exigido com as análises enviadas (Portaria GM/MS 888/2021).
3. Grava saida/formas.json, saida/cumprimento.json, saida/referencia.json (e saida/municipios_al.json na 1ª vez).

Uso:  python3 atualizar.py               busca de novo o ano corrente e os cadastros; anos anteriores só se faltarem
      python3 atualizar.py --tudo        busca de novo também os anos anteriores (o portal ainda corrige meses antigos)
      python3 atualizar.py --sem-baixar  só recalcula com os CSV que já estão em dados/
Requer Python 3.9+ e pandas.
"""
import csv
import datetime as dt
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

UF = "AL"
ANO_INICIAL = 2023  # o plano de amostragem de 2022 usa outro layout de campos
BASE = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SISAGUA/"
GEO = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-27-mun.json"
AQUI = Path(__file__).resolve().parent
DADOS, SAIDA = AQUI / "dados", AQUI / "saida"
BUSCAS = DADOS / "buscas.json"  # quando cada arquivo foi buscado e quando o portal o publicou
HOJE = dt.date.today()
ANOS = range(ANO_INICIAL, HOJE.year + 1)
PARAM = {  # nome no controle mensal -> nome no plano de amostragem
    "Cloro Residual Livre (mg/L)": "Residual de Desinfetante",
    "Cloro Residual Combinado (mg/L)": "Residual de Desinfetante",
    "Dióxido de Cloro (mg/L)": "Residual de Desinfetante",
}


def arquivos():
    yield "cadastro_populacao_abastecida"
    yield "cadastro_tratamento_de_agua"
    for ano in ANOS:
        yield f"controle_mensal_plano_amostragem_{ano}"
        yield f"controle_mensal_parametros_basicos_{ano}"
        yield f"controle_semestral_{ano}"


def baixar(nome):
    """Baixa <nome>_csv.zip e grava dados/<nome>.csv só com as linhas da UF (UTF-8, ';')."""
    with tempfile.TemporaryFile() as tmp:
        try:
            with urllib.request.urlopen(BASE + nome + "_csv.zip", timeout=600) as r:
                shutil.copyfileobj(r, tmp)
                publicado = r.headers.get("Last-Modified")
        except urllib.error.HTTPError as e:
            if str(HOJE.year) in nome:  # arquivo do ano corrente pode ainda não ter sido publicado
                print(f"aviso: {nome} indisponível ({e.code}), mantido o que havia")
                return
            raise
        with zipfile.ZipFile(tmp) as z, z.open(next(n for n in z.namelist() if n.lower().endswith(".csv"))) as fh:
            header = next(csv.reader([fh.readline().decode("latin-1")], delimiter=";"))
            col = next(i for i, h in enumerate(header) if h in ("UF", "SG_UF"))
            kept = bad = 0
            with open(DADOS / f"{nome}.csv", "w", newline="", encoding="utf-8") as out:
                w = csv.writer(out, delimiter=";")
                w.writerow(header)
                for line in fh:
                    parts = line.split(b";", col + 1)
                    if len(parts) > col and parts[col].strip(b'"') == UF.encode():  # filtro rápido em bytes
                        row = next(csv.reader([line.decode("latin-1")], delimiter=";"))
                        if len(row) != len(header):
                            bad += 1
                            continue
                        w.writerow(row)
                        kept += 1
    print(f"{nome}: {kept} linhas de {UF}")
    assert bad <= kept * 0.001, f"{nome}: {bad} registros quebrados; trocar o filtro rápido pelo csv.reader completo"
    buscas = json.loads(BUSCAS.read_text()) if BUSCAS.exists() else {}
    buscas[nome] = {"buscado_em": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "publicado_em": publicado and dt.datetime.strptime(publicado, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%dT%H:%M:%SZ")}
    BUSCAS.write_text(json.dumps(buscas, indent=1))


def ler(prefixo):
    anos = {f: int(f.stem[-4:]) if f.stem[-4:].isdigit() else 0 for f in sorted(DADOS.glob(f"{prefixo}*.csv"))}
    partes = [pd.read_csv(f, sep=";", dtype=str).assign(arquivo_ano=a) for f, a in anos.items() if a == 0 or a in ANOS]
    assert partes, f"faltam arquivos {prefixo}*.csv em {DADOS}"
    return pd.concat(partes, ignore_index=True)


def cnpj(s):
    return s.fillna("").str.replace(r"\.0$", "", regex=True).str.zfill(14).replace("0" * 14, "SEM CNPJ")


def num(s):
    return pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")


def anexo14(pop):
    """Nº mínimo mensal de amostras bacteriológicas no sistema de distribuição de SAA (Anexo 14, retificado).
    "1 para cada N habitantes" arredondado para cima."""
    if pop < 5_000:
        return 5
    for teto, base, por in [(10_000, 10, 0), (50_000, 0, 1_000), (80_000, 25, 2_000), (130_000, 1, 1_250),
                            (250_000, 40, 2_000), (340_000, 115, 5_000), (400_000, 47, 2_500),
                            (600_000, 127, 5_000), (1_140_000, 187, 10_000)]:
        if pop <= teto:
            return base + (-(-pop // por) if por else 0)
    return min(244 + -(-pop // 20_000), 400)


def montar():
    chave = ["ano", "forma", "cod_ibge"]

    # Universo: formas cadastradas por ano (cadastro de população abastecida)
    cad = ler("cadastro_populacao_abastecida")
    cad = cad[cad.NU_ANO.astype(int).isin(ANOS)].sort_values("DT_INCLUSAO_REGISTRO")
    formas = pd.DataFrame({
        "ano": cad.NU_ANO.astype(int), "forma": cad.NU_SOLUCAO_ABASTECIMENTO, "cod_ibge": cad.CO_MUNICIPIO_IBGE.str[:6],
        "nome": cad.NO_SOLUCAO_ABASTECIMENTO, "tipo": cad.TP_ABASTECIMENTO, "municipio": cad.NO_MUNICIPIO,
        "responsavel": cad.NO_EMPRESA, "cnpj": cnpj(cad.NU_CNPJ), "populacao": num(cad.NU_VALOR_POPULACAO_ESTIMADA),
    }).drop_duplicates(chave, keep="last").assign(cadastrada=True)

    # Exigido: plano de amostragem do SISAGUA (total anual de análises por ponto e parâmetro)
    pl = ler("controle_mensal_plano_amostragem").rename(columns={"NU_SOLUCAO_ABASTECIMENTO": "forma"})
    pl["ano"], pl["cod_ibge"] = pl.arquivo_ano, pl.CO_MUNICIPIO_IBGE.str[:6]
    trat = ler("cadastro_tratamento_de_agua")
    fluor = trat[(trat.ST_FLUORETACAO == "S") | (trat.ST_DESFLUORETACAO == "S")]
    fluor = set(zip(fluor.NU_ANO.astype(int), fluor.NU_SOLUCAO_ABASTECIMENTO))
    # Anexo 13, nota 2: fluoreto mensal só para quem faz fluoretação/desfluoretação; os demais entram no semestral
    pl = pl[(pl.PARAMETRO != "Fluoreto (mg/L)") | pd.Series(list(zip(pl.ano, pl.forma)), index=pl.index).isin(fluor)]
    tot = pl[pl.CAMPO == "Total Anual de Análises"].assign(eta=pl.NO_ETA.fillna(""), v=num(pl.VALOR))
    # o arquivo repete linhas idênticas; uma por ETA/ponto/parâmetro e soma-se entre ETAs
    exig = (tot.groupby(chave + ["eta", "PT_MONITORAMENTO", "PARAMETRO"]).v.max()
            .groupby(level=chave + ["PT_MONITORAMENTO", "PARAMETRO"]).sum() / 12).rename("exig")

    # Conferência do plano com o Anexo 14 (SAA, coliformes totais no sistema de distribuição)
    a14 = pl[(pl.TP_ABASTECIMENTO == "SAA") & (pl.PT_MONITORAMENTO == "SISTEMA DE DISTRIBUIÇÃO")
             & (pl.PARAMETRO == "Coliformes totais") & (pl.CAMPO == "Número de Análises")]
    a14 = a14.assign(n=num(a14.VALOR), pop=num(a14.POP_ABASTECIDA_ESTIMADA)).dropna(subset=["n", "pop"])
    a14 = a14.groupby(chave).agg(n=("n", "max"), pop=("pop", "max"))
    a14["minimo_anexo14"] = a14["pop"].astype(int).map(anexo14)
    abaixo = (a14.n < a14.minimo_anexo14).rename("plano_abaixo_anexo14")

    # Enviado: controle mensal de parâmetros básicos
    bs = ler("controle_mensal_parametros_basicos")
    bs = bs.rename(columns={"Código Forma de abastecimento": "forma", "Ponto de Monitoramento": "PT_MONITORAMENTO"})
    bs["ano"], bs["mes"] = bs["Ano de referência"].astype(int), bs["Mês de referência"].astype(int)
    bs["cod_ibge"] = bs["Código IBGE"].str[:6]
    bs = bs[bs.ano.isin(ANOS)]
    envio = bs.groupby(chave).mes.agg(lambda m: "".join("1" if i in set(m) else "0" for i in range(1, 13))).rename("envio")
    am = bs[bs.Campo == "Número de amostras analisadas"]
    am = am.assign(PARAMETRO=am["Parâmetro"].replace(PARAM), v=num(am.Valor))
    real = am.groupby(chave + ["PT_MONITORAMENTO", "PARAMETRO", "mes"]).v.sum().unstack("mes").reindex(columns=range(1, 13))

    # Cumprimento: análises enviadas até o mínimo exigido (o excedente de um mês não cobre outro)
    cmp = real.reindex(exig.index).fillna(0).clip(upper=exig, axis=0)
    cmp["exig"] = exig
    cmp = cmp.groupby(level=chave + ["PARAMETRO"]).sum().round(2).reset_index()
    cmp.columns = chave + ["parametro"] + [f"m{m:02d}" for m in range(1, 13)] + ["exigido_mes"]
    cmp = cmp[chave + ["parametro", "exigido_mes"] + [f"m{m:02d}" for m in range(1, 13)]]

    # Controle semestral: houve envio no 1º/2º semestre?
    se = ler("controle_semestral").rename(columns={"NU_SOLUCAO_ABASTECIMENTO": "forma"})
    se = se.assign(ano=se.NU_ANO.astype(int), cod_ibge=se.CO_MUNICIPIO_IBGE.str[:6])
    semestral = se.groupby(chave).NU_SEMESTRE.agg(lambda s: ("1" if "1" in set(s) else "0") + ("1" if "2" in set(s) else "0"))

    # Formas que aparecem no plano ou no controle sem estar no cadastro do ano entram com os dados que trazem
    extra = pd.concat([
        pl.rename(columns={"NO_SOLUCAO_ABASTECIMENTO": "nome", "TP_ABASTECIMENTO": "tipo", "NO_MUNICIPIO": "municipio",
                           "NO_INSTITUICAO": "responsavel"}).assign(cnpj=cnpj(pl.NU_CNPJ_INSTITUICAO)),
        bs.rename(columns={"Nome da Forma de Abastecimento": "nome", "Tipo da Forma de Abastecimento": "tipo",
                           "Município": "municipio", "Nome da Instituição": "responsavel"}).assign(cnpj=cnpj(bs["CNPJ da Instituição"])),
    ])[chave + ["nome", "tipo", "municipio", "responsavel", "cnpj"]].drop_duplicates(chave)
    formas = pd.concat([formas, extra.assign(cadastrada=False)]).drop_duplicates(chave)
    formas["responsavel"] = formas.responsavel.fillna("Responsável não informado no cadastro")
    # alguns nomes de MEI trazem o CPF do titular; o painel é público, então esse número sai
    for col in ("responsavel", "nome"):
        formas[col] = formas[col].str.replace(r"\s*\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "", regex=True).str.strip()
    formas = (formas.set_index(chave)
              .join(pd.Series(True, index=exig.index.droplevel([3, 4]).unique(), name="tem_plano"))
              .join(abaixo).join(envio).join(semestral.rename("semestral")).reset_index())
    formas["tem_plano"] = formas.tem_plano.eq(True)
    formas["envio"] = formas.envio.fillna("0" * 12)
    formas["semestral"] = formas.semestral.fillna("00")
    formas["plano_abaixo_anexo14"] = formas.plano_abaixo_anexo14.astype("boolean")
    formas = formas.sort_values(chave)

    # Último mês completo: o mais recente em que enviaram ao menos 80% das formas da mediana dos 12 meses anteriores
    mensal = bs.groupby(["ano", "mes"])[["forma", "cod_ibge"]].apply(lambda d: len(d.drop_duplicates())).sort_index()
    ultimo = None
    for i in range(len(mensal) - 1, 11, -1):
        if mensal.iloc[i] >= 0.8 * mensal.iloc[i - 12:i].median():
            ultimo = mensal.index[i]
            break
    assert ultimo, "série mensal curta demais para achar o último mês completo"

    # Autoverificação
    assert not formas.duplicated(chave).any() and not cmp.duplicated(chave + ["parametro"]).any()
    assert not formas.responsavel.str.contains(r"\b\d{11}\b", na=False).any(), "sobrou número com cara de CPF"
    assert (cmp[[f"m{m:02d}" for m in range(1, 13)]].max(axis=1) <= cmp.exigido_mes + 0.01).all()
    assert anexo14(2775) == 5 and anexo14(12679) == 13 and anexo14(63199) == 57 and anexo14(2_000_000) == 344

    SAIDA.mkdir(exist_ok=True)
    codigo = Path(__file__).read_text(encoding="utf-8")
    entradas = "\n".join(BASE + n + "_csv.zip" for n in arquivos())
    meta = [{"label": "atualizar.py", "value": codigo, "type": "code", "lang": "python"},
            {"label": "Entradas", "value": entradas},
            {"label": "Gerado em", "value": dt.datetime.now().strftime("%Y-%m-%d %H:%M")}]

    def gravar(nome, df):
        d = json.loads(df.to_json(orient="split", index=False))
        rows = [[int(v) if isinstance(v, float) and v.is_integer() else v for v in r] for r in d["data"]]
        with open(SAIDA / nome, "w", encoding="utf-8") as f:
            json.dump({"columns": d["columns"], "rows": rows, "meta": meta}, f, ensure_ascii=False, separators=(",", ":"))
        print(f"{nome}: {len(df)} linhas, {(SAIDA / nome).stat().st_size / 1e6:.1f} MB")

    gravar("formas.json", formas)
    gravar("cumprimento.json", cmp)
    busca = (json.loads(BUSCAS.read_text()) if BUSCAS.exists() else {}).get(f"controle_mensal_parametros_basicos_{HOJE.year}", {})
    gravar("referencia.json", pd.DataFrame([{
        "extraido_em": HOJE.isoformat(), "ano_inicial": ANO_INICIAL, "ultimo_mes_completo": f"{ultimo[0]}-{ultimo[1]:02d}",
        "ultimo_mes_com_dados": f"{mensal.index[-1][0]}-{mensal.index[-1][1]:02d}",
        "buscado_em": busca.get("buscado_em"), "publicado_em": busca.get("publicado_em")}]))

    if not (SAIDA / "municipios_al.json").exists():
        with urllib.request.urlopen(GEO, timeout=120) as r:
            geo = json.load(r)
        for f in geo["features"]:  # coordenadas com 3 casas (~100 m) bastam para o mapa
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            g["coordinates"] = [[[[round(x, 3), round(y, 3)] for x, y in anel] for anel in p] for p in polys]
            g["type"] = "MultiPolygon"
            f["properties"] = {"cod_ibge": f["properties"]["id"][:6], "nome": f["properties"]["name"]}
        with open(SAIDA / "municipios_al.json", "w", encoding="utf-8") as f:
            json.dump(geo, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    DADOS.mkdir(exist_ok=True)
    if "--sem-baixar" not in sys.argv:
        for nome in arquivos():
            ano_antigo = nome[-4:].isdigit() and int(nome[-4:]) < HOJE.year
            if "--tudo" in sys.argv or not ano_antigo or not (DADOS / f"{nome}.csv").exists():
                baixar(nome)
    montar()
