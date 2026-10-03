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

O código e os testes de aquisição ficam em `dataset/`; os dados e manifestos ficam em `data/` na raiz do projeto. O destino padrão é `data/raw/<dataset>/videos/`. Os comandos usam o módulo da aplicação e podem ser executados de qualquer diretório após `uv sync`.

```powershell
# Listar os vídeos e tamanhos disponíveis, sem baixá-los
uv run python -m libras_translation --dataset all --list-only

# Testar com até 2 vídeos por dataset
uv run python -m libras_translation --dataset all --limit 2 --workers 2

# Download completo dos dois datasets
uv run python -m libras_translation --dataset all

# Retomar uma aquisição interrompida: repetir o mesmo comando
uv run python -m libras_translation --dataset all

# Selecionar dataset, destino e concorrência
uv run python -m libras_translation --dataset v-librasil-raw --destination E:\dados\libras --workers 4
```

Cada manifesto em `data/manifests/` registra o repositório, o commit fixado, a data da aquisição, os caminhos remotos e locais, os tamanhos disponíveis e o estado de cada arquivo. Arquivos completos são reutilizados ao retomar.

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
├── pyproject.toml          dependências, build e comando Python
└── uv.lock                 versões resolvidas das dependências
```

O grafo de conhecimento do projeto é centralizado em `../harness/graphify-out/`; não mantenha um `graphify-out/` separado nesta pasta.

Quando uma etapa de preparação for implementada, seus resultados intermediários e preparados serão adicionados sob `data/`, com uma decisão explícita sobre formatos, rastreabilidade e licenças.
