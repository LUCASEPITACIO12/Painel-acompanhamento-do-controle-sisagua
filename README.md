# Painel SISAGUA Alagoas: quem já alimentou o controle da qualidade da água

Painel para acompanhar se os responsáveis por sistemas (SAA) e soluções alternativas coletivas (SAC) de abastecimento de água em Alagoas estão enviando ao SISAGUA as análises de controle da qualidade da água exigidas pela Portaria GM/MS nº 888/2021, e qual mês ainda falta alimentar.

Este repositório guarda o código. Os dados são baixados do Portal de Dados Abertos do SUS cada vez que o script roda.

## O que o painel mostra

- Quantas formas de abastecimento, de cada 100, mandaram dados no último mês fechado.
- Quantos responsáveis devem pelo menos um mês e quantas formas estão em dia.
- Um "copo d'água" por mês, que enche conforme as formas mandam dados.
- A lista "quem está devendo qual mês", por responsável ou por município.
- Uma grade de meses por responsável, que abre para mostrar cada forma de abastecimento.
- Um mapa dos municípios pela parte dos meses fechados que tiveram dados.
- Busca por município e por responsável (nome ou CNPJ, com ou sem pontuação).

Cada mês de cada forma recebe uma situação:

| Situação | Quando |
|---|---|
| ✓ Enviado | chegaram pelo menos 90% das análises mínimas do plano de amostragem no mês |
| ½ Envio parcial | chegou algum dado, mas menos de 90% |
| ✕ Não enviado | nenhum dado no mês |
| … Ainda em digitação | mês depois do último mês fechado, ainda sem dado completo |
| – Não exigido | SAI (só vigilância, Art. 4º) ou parâmetro fora do plano |
| (vazio) | o mês ainda não terminou |

"Último mês fechado" é o mês mais recente em que enviaram pelo menos 80% das formas da mediana dos 12 meses anteriores. Os cortes de 90% e 80% são critérios deste painel, porque a Portaria não fixa prazo de envio.

## De onde vêm os dados

Portal de Dados Abertos do SUS (dadosabertos.saude.gov.br), conjunto SISAGUA, licença Creative Commons Atribuição (CC BY):

| Base | Uso |
|---|---|
| População abastecida (cadastro) | quais formas existem em cada ano, tipo, responsável, população |
| Tratamento de água (cadastro) | quem faz fluoretação (Anexo 13, nota 2) |
| Controle mensal – Plano de amostragem | quantas análises são exigidas por mês |
| Controle mensal – Parâmetros básicos | quantas análises foram enviadas e em que mês |
| Controle semestral | se houve envio no semestre |

Os limites municipais do mapa vêm do projeto [geodata-br](https://github.com/tbrugz/geodata-br), feito a partir da malha do IBGE. Confira a licença no repositório de origem antes de redistribuir.

Regras da Portaria GM/MS nº 888/2021 usadas: Art. 4º e 14 (quem envia), Art. 28, §3º (turbidez pós-filtração), Art. 42 e 44 (planos de amostragem) e Anexos 13, 14 e 15 (número mínimo de amostras e frequência). O exigido de cada mês é o plano registrado no SISAGUA (total anual ÷ 12, por ponto e parâmetro). Para SAA, o plano de coliformes no sistema de distribuição é conferido com o Anexo 14.

## Estrutura

```
atualizar.py        baixa os dados, filtra Alagoas e gera os arquivos do painel
painel/index.html   página do painel (roda dentro do painel de dados do Claude)
requirements.txt    dependências do Python
dados/              CSV de Alagoas baixados do portal (criada pelo script, fora do Git)
saida/              arquivos JSON para o painel (criada pelo script, fora do Git)
```

## Como instalar

Precisa de Python 3.9 ou mais novo. Testado com pandas 2.2 e 3.0.

```bash
pip install -r requirements.txt
```

## Como atualizar os dados

```bash
python atualizar.py
```

Busca de novo o ano corrente e os cadastros (cerca de 500 MB de download) e só baixa um ano anterior se ele ainda não estiver em `dados/`. Grava em `saida/`:

- `formas.json`: uma linha por forma de abastecimento, município e ano, com os meses em que houve envio.
- `cumprimento.json`: análises exigidas e enviadas por mês e parâmetro.
- `referencia.json`: data da busca, data de publicação no portal e último mês fechado.
- `municipios_al.json`: limites municipais (só na primeira vez).

O portal também corrige meses de anos anteriores. Para buscar tudo de novo (cerca de 1,7 GB; no teste levou uns 5 minutos):

```bash
python atualizar.py --tudo
```

Para só recalcular com os arquivos que já estão em `dados/`, sem baixar nada:

```bash
python atualizar.py --sem-baixar
```

## Como pôr os dados novos no painel

O painel fica no Claude, como um painel de dados. Depois de rodar o script:

1. Abra o painel e o painel de fontes (Sources).
2. Substitua os arquivos das fontes "Formas de abastecimento e envio", "Análises exigidas e enviadas" e "Data de referência dos dados" pelos novos `saida/formas.json`, `saida/cumprimento.json` e `saida/referencia.json`.

Ou peça ao Claude para fazer a troca.

## Sobre a página `painel/index.html`

A página usa o ambiente do painel de dados do Claude (`dash.data`, `dash.calc`, `dash.draw`) e lê os arquivos anexados a ele. Ela não abre sozinha num navegador nem no GitHub Pages. Uma versão estática para o GitHub Pages é possível, mas publicaria os arquivos de `saida/`, que trazem nomes de responsáveis (veja abaixo).

## O que fica fora do Git e por quê

- `dados/`: são cerca de 200 MB de CSV, baixados de novo pelo script a qualquer momento.
- `saida/`: trazem os nomes dos responsáveis como o Ministério da Saúde publica. Alguns são pessoas físicas (por exemplo, microempreendedores), e certos nomes de empresa incluem números que parecem CPF. Por isso não ficam num repositório que pode ser público. Gere de novo com o script.

## Automação opcional com GitHub Actions

Dá para o GitHub rodar o script todo mês e guardar os arquivos gerados como artefato da execução, por um tempo limitado. Para isso, crie o arquivo `.github/workflows/atualizar.yml` com:

```yaml
name: Atualizar dados do SISAGUA
on:
  schedule:
    - cron: "0 9 20 * *"   # todo dia 20, 9h UTC (6h em Alagoas)
  workflow_dispatch:        # permite rodar na mão pela aba Actions
jobs:
  atualizar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python atualizar.py
      - uses: actions/upload-artifact@v4
        with:
          name: saida-painel
          path: saida/
```

Cuidados:

- O GitHub não troca os arquivos dentro do painel do Claude. Baixe o artefato da execução e substitua as fontes, ou peça ao Claude.
- Como o runner começa vazio, cada execução baixa todos os anos (cerca de 1,7 GB).
- Num repositório público, os artefatos ficam acessíveis a outras pessoas. Use um repositório privado.
- Em repositório privado, os minutos de GitHub Actions dependem do seu plano.

## Limitações

- Uma forma que abastece mais de um município conta em cada um, como no cadastro do SISAGUA.
- O controle semestral só confere se houve envio, não se vieram todos os parâmetros.
- Análises lançadas num ponto de monitoramento fora do plano contam como envio no mês, mas não completam o plano.
- O plano de amostragem de 2022 usa outro formato de campos, por isso o painel começa em 2023.
