# Painel SISAGUA Alagoas: quem já alimentou o controle da qualidade da água

Painel para acompanhar se os responsáveis por sistemas (SAA) e soluções alternativas coletivas (SAC) de abastecimento de água em Alagoas estão enviando ao SISAGUA as análises de controle da qualidade da água exigidas pela Portaria GM/MS nº 888/2021, e qual mês ainda falta alimentar.

Este repositório guarda o código. Os dados são baixados do Portal de Dados Abertos do SUS cada vez que o script roda. O painel é publicado no GitHub Pages e se atualiza sozinho toda semana (veja "Painel no GitHub Pages").

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

Regras da Portaria GM/MS nº 888/2021 usadas: Art. 4º e 14 (quem envia), Art. 28, §3º (turbidez pós-filtração), Art. 42 e 44 (planos de amostragem) e Anexos 13, 14 e 15 (número mínimo de amostras e frequência). O exigido de cada mês é o plano registrado no SISAGUA (total anual ÷ 12, por ponto e parâmetro). Para SAA, o plano de coliformes no sistema de distribuição é conferido com o Anexo 14; diferenças que vêm só do arredondamento de “1 para cada N habitantes” não são marcadas.

## Estrutura

```
atualizar.py                     baixa os dados, filtra Alagoas e gera os arquivos do painel
ver_local.py                     monta o painel e abre no navegador do seu computador
painel/index.html                página do painel (a mesma no Claude e no GitHub Pages)
pages/casca.html                 moldura da página para o GitHub Pages
pages/dash.js                    funções do painel de dados do Claude que a página usa, para rodar fora dele
.github/workflows/publicar.yml   roda o script e publica o painel no GitHub Pages
requirements.txt                 dependências do Python
dados/                           CSV de Alagoas baixados do portal (criada pelo script, fora do Git)
saida/                           arquivos JSON para o painel (criada pelo script, fora do Git)
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
- `cumprimento.json`: análises exigidas e enviadas por mês, ponto de coleta e parâmetro.
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

## Como pôr os dados novos no painel do Claude

O painel fica no Claude, como um painel de dados. Depois de rodar o script:

1. Abra o painel e o painel de fontes (Sources).
2. Substitua os arquivos das fontes "Formas de abastecimento e envio", "Análises exigidas e enviadas" e "Data de referência dos dados" pelos novos `saida/formas.json`, `saida/cumprimento.json` e `saida/referencia.json`.

Ou peça ao Claude para fazer a troca.

## Painel no GitHub Pages

O arquivo `.github/workflows/publicar.yml` faz o GitHub, a cada execução:

1. rodar `python atualizar.py`, que busca os dados no portal (cerca de 1,7 GB, uns 5 a 10 minutos);
2. montar a pasta `site/` com a página (`pages/casca.html` + `painel/index.html` + `pages/dash.js`) e os quatro arquivos de `saida/`;
3. publicar essa pasta no GitHub Pages.

Ele roda toda segunda-feira às 6h17 (horário de Alagoas), quando alguém altera a página, o script ou o próprio fluxo, e quando você aperta **Run workflow** na aba **Actions**.

Para ligar, uma vez só:

1. Em **Settings > Pages**, em **Build and deployment > Source**, escolha **GitHub Actions**.
2. Na conta gratuita do GitHub, o Pages só funciona com repositório público. Se o seu estiver privado, mude em **Settings > General > Danger Zone > Change visibility**.
3. Na aba **Actions**, abra **Publicar painel no GitHub Pages** e clique em **Run workflow**.

O endereço aparece no fim da execução e em **Settings > Pages**. Ele segue o formato `https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/`.

Se uma execução falhar (por exemplo, com o portal fora do ar), o site continua com a versão anterior, e o GitHub avisa conforme as suas configurações de notificação.

## Ver no seu computador

Para só ver o painel, abra o endereço do GitHub Pages no navegador. Para rodar no seu computador, por exemplo para testar uma mudança antes de subir:

1. Instale o Python 3.9 ou mais novo (python.org). No Windows, marque **Add python.exe to PATH** na instalação.
2. Baixe o repositório: no GitHub, **Code > Download ZIP**, e descompacte.
3. Abra um terminal na pasta descompactada. No Windows, abra a pasta, clique na barra de endereço, digite `cmd` e aperte Enter.
4. Rode o comando abaixo, trocando pelo endereço do seu site. Se o Windows disser que não conhece `python`, use `py`.

```bash
python ver_local.py https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/
```

O script baixa os dados já publicados no site, monta a página na pasta `site/` e abre o navegador em `http://localhost:8000/`. Para parar, aperte Ctrl+C no terminal.

Para calcular tudo no seu computador, sem usar os dados do site (baixa cerca de 1,7 GB do portal na primeira vez):

```bash
pip install -r requirements.txt
```

```bash
python atualizar.py
```

```bash
python ver_local.py
```

Abrir o `index.html` com dois cliques não funciona, porque o navegador não deixa a página ler os arquivos de dados direto do disco. O `ver_local.py` resolve isso servindo a pasta num endereço local. A página carrega a biblioteca d3 pela internet, então precisa de conexão.

## O que fica fora do Git e por quê

- `dados/`: são cerca de 200 MB de CSV, baixados de novo pelo script a qualquer momento.
- `saida/` e `site/`: são gerados a cada execução. O GitHub monta tudo na hora de publicar, sem guardar os dados no repositório.

O site publicado é público e mostra os nomes dos responsáveis como o Ministério da Saúde publica nos dados abertos (licença CC BY), inclusive de pessoas físicas, como microempreendedores. O script tira dos nomes os números com formato de CPF que aparecem em alguns cadastros de MEI.

## Limitações

- Uma forma que abastece mais de um município conta em cada um, como no cadastro do SISAGUA.
- O controle semestral só confere se houve envio, não se vieram todos os parâmetros.
- Análises lançadas num ponto de monitoramento fora do plano contam como envio no mês, mas não completam o plano.
- O plano de amostragem de 2022 usa outro formato de campos, por isso o painel começa em 2023.
