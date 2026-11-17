# Como subir este projeto no GitHub

Há dois jeitos. O primeiro é só pelo site, sem instalar nada. O segundo usa o programa `git` no computador e facilita mandar atualizações depois.

Antes de começar, descompacte o arquivo `painel-sisagua-al.zip`. Vai aparecer a pasta `painel-sisagua-al` com estes arquivos:

```
.gitignore
COMO_SUBIR_NO_GITHUB.md
README.md
atualizar.py
requirements.txt
painel/index.html
```

O `.gitignore` começa com ponto e fica escondido em alguns computadores. No Mac, aperte Cmd + Shift + . (ponto) no Finder para ver arquivos escondidos. No Windows, no Explorador de Arquivos, marque Exibir > Itens ocultos.

## Jeito 1: pelo site

1. Entre em github.com com sua conta. Se não tiver, clique em Sign up e crie uma.
2. No canto superior direito, clique no **+** e depois em **New repository**.
3. Em **Repository name**, escreva um nome, por exemplo `painel-sisagua-al`.
4. Escolha **Private** (só você e quem você convidar veem) ou **Public** (qualquer pessoa vê). Na dúvida, escolha Private: dá para mudar depois.
5. Deixe desmarcadas as opções de adicionar README, .gitignore e licença, porque esses arquivos já estão na pasta.
6. Clique em **Create repository**.
7. Na página do repositório vazio, clique no link **uploading an existing file**.
8. Abra a pasta `painel-sisagua-al` no seu computador, selecione **tudo o que está dentro dela** (inclusive a pasta `painel` e o `.gitignore`) e arraste para a área da página.
9. Confira se a lista mostra `painel/index.html`, e não só `index.html`. Se a pasta não veio junto, use um navegador como Chrome ou Edge e arraste de novo.
10. Embaixo, em **Commit changes**, escreva uma frase como `Primeira versão do painel` e clique em **Commit changes**.

Pronto. Para atualizar um arquivo depois, abra-o no GitHub, clique no lápis (Edit) ou use **Add file > Upload files** de novo.

## Jeito 2: pela linha de comando com git

### Uma vez só, no seu computador

1. Instale o Git em git-scm.com/downloads. No Windows, aceite as opções padrão do instalador.
2. Abra o terminal. No Windows, use o **Git Bash**, que vem com o Git. No Mac, use o app **Terminal**.
3. Diga ao Git seu nome e e-mail (aparecem no histórico do repositório):

```bash
git config --global user.name "Seu Nome"
```

```bash
git config --global user.email "seu-email@exemplo.com"
```

### Criar o repositório no GitHub

Faça os passos 1 a 6 do Jeito 1. Ao final, o GitHub mostra um endereço parecido com `https://github.com/SEU-USUARIO/painel-sisagua-al.git`. Copie esse endereço.

### Enviar os arquivos

1. No terminal, entre na pasta descompactada. Se ela estiver em Downloads:

```bash
cd ~/Downloads/painel-sisagua-al
```

2. Transforme a pasta num repositório Git:

```bash
git init -b main
```

3. Marque todos os arquivos para entrar no primeiro envio:

```bash
git add .
```

4. Confira o que vai entrar. Devem aparecer só os seis arquivos da lista acima, e nunca as pastas `dados/` ou `saida/`:

```bash
git status
```

5. Grave essa versão:

```bash
git commit -m "Primeira versão do painel"
```

6. Ligue a pasta ao repositório do GitHub, colando o endereço que você copiou:

```bash
git remote add origin https://github.com/SEU-USUARIO/painel-sisagua-al.git
```

7. Envie:

```bash
git push -u origin main
```

Na primeira vez, o Git pede login. No Windows, abre uma janela do navegador para entrar no GitHub. No Mac e no Linux, se pedir senha, a senha da conta não funciona: crie um token em GitHub > Settings > Developer settings > Personal access tokens e cole o token no lugar da senha.

### Para mandar mudanças depois

Depois de editar arquivos, rode estes três comandos, na pasta do projeto:

```bash
git add .
```

```bash
git commit -m "Descreva o que mudou"
```

```bash
git push
```

## Antes de deixar o repositório público

- Rodar `python atualizar.py` cria as pastas `dados/` e `saida/`. O `.gitignore` já as deixa de fora, porque `saida/` traz nomes de responsáveis, alguns de pessoas físicas.
- Se você mesmo copiar arquivos de `saida/` para dentro do repositório, eles passam a ser públicos junto com ele.
