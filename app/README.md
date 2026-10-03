# Libras Translation — aquisição de datasets

Nesta etapa, tudo que implementa e testa o download dos datasets está em `dataset/`. A raiz mantém a configuração do projeto; `data/` mantém os vídeos e manifestos. Modelos e treinamento ficam fora do escopo atual.

## Ambiente no Windows (PowerShell)

A raiz continua sendo `app/`. O arquivo `.python-version` fixa Python 3.13.7 para `pyenv-win` e `uv`.

```powershell
Set-Location C:\Users\mdbaa\development\Dissertacao\app
pyenv install 3.13.7 # somente se ainda não estiver instalado
pyenv local 3.13.7
uv sync
```

Se a instalação falhar por certificado da rede, tente `uv sync --native-tls`.

Configure o token na raiz do projeto. Se `.env` já existir, preserve-o e edite-o; se não existir, crie-o a partir do exemplo:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Defina `HF_TOKEN` no `.env` com um token Hugging Face de leitura. O arquivo `.env` é ignorado pelo Git. Uma variável `$env:HF_TOKEN` já definida no PowerShell tem precedência. O programa não registra nem exibe o token.

## Aquisição de vídeos

O código e os testes de aquisição ficam em `dataset/`; os dados e manifestos ficam em `data/` na raiz do projeto. A CLI é composta por Typer e Rich e não abre menus nem solicita respostas: cada operação recebe suas opções pela linha de comando, permitindo execução em scripts e terminais não interativos. O destino mantém a raiz de cada repositório em `data/raw/<dataset>/`: vídeos em `videos/` e arquivos auxiliares, como anotações, na raiz. A integração usa a biblioteca oficial `huggingface_hub` (a mesma infraestrutura do comando `hf download`), fixa um commit e mantém manifesto rastreável. Os comandos podem ser executados de qualquer diretório após `uv sync`.

```powershell
# Ver comandos e opções
uv run libras --help
uv run libras data --help

# Listar metadados/tamanhos, sem baixar (pode selecionar um ou todos)
uv run libras data list --dataset all
uv run libras data list --dataset minds-libras-raw --show-files

# Testar download limitado; exige seleção explícita do dataset
uv run libras data download --dataset minds-libras-raw --limit 2 --workers 2

# Download completo de um dataset (use --dataset all para ambos)
uv run libras data download --dataset v-librasil-raw
uv run libras data download --dataset all

# Retomar uma aquisição interrompida: repetir o mesmo comando
uv run libras data download --dataset all

# Selecionar dataset, destino e concorrência
uv run libras data download --dataset v-librasil-raw --destination E:\dados\libras --workers 4
```

Os comandos retornam `0` quando a operação termina sem falhas, `1` quando ocorre falha de rede/acesso ou de arquivos e `2` quando há opções inválidas ou obrigatórias ausentes. Para apenas ver a ajuda, use `uv run libras --help` ou `uv run libras data download --help`; invocar sem argumentos mostra a ajuda e não inicia downloads.

Cada manifesto em `data/manifests/` registra o repositório, o commit fixado, a data da aquisição, os caminhos remotos e locais, os tamanhos disponíveis e o estado dos vídeos e arquivos auxiliares. A opção `--limit` limita apenas os vídeos para testes; os arquivos auxiliares de metadados do dataset ainda são baixados. Arquivos completos são reutilizados ao retomar.

No MINDS-Libras, isso preserva, quando presentes no commit escolhido, `annotations.csv` e `annotations.py` ao lado de `videos/`. No V-Librasil, preserva `annotations.csv`, `error.csv` e `videos/`. Os nomes e caminhos remotos são mantidos; os scripts de anotação são apenas baixados, nunca executados. O Dataset Viewer indisponível não impede o download dos arquivos originais do repositório.

Os datasets só poderão ser considerados adequados à tradução Gloss-Free depois de examinar suas anotações, pares vídeo-texto e condições de uso. Nenhuma tradução ou rótulo é inferido pelo nome de um arquivo.

## Estrutura atual

```text
app/
├── dataset/                 único componente de aquisição nesta etapa
│   ├── src/libras_translation/
│   │   ├── cli.py           interface de linha de comando
│   │   ├── config.py        raiz, caminhos e token
│   │   ├── acquisition.py   coordenação e manifesto
│   │   └── infrastructure/ cliente do Hugging Face Hub
│   └── tests/               testes do componente sem downloads reais
├── data/                    dados fora do código
│   ├── raw/                 vídeos originais; ignorados pelo Git
│   └── manifests/           registros versionáveis da aquisição
├── .env.example            modelo do token, sem credenciais
├── pyproject.toml          dependências, build e comando `libras`
└── uv.lock                 versões resolvidas das dependências
```

O grafo de conhecimento do projeto é centralizado em `../harness/graphify-out/`; não mantenha um `graphify-out/` separado nesta pasta.

Quando uma etapa de preparação for implementada, seus resultados intermediários e preparados serão adicionados sob `data/`, com uma decisão explícita sobre formatos, rastreabilidade e licenças.
