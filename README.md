# Aprendizado profundo de representações visuais para tradução de Libras para português escrito sem glosas

Projeto de pesquisa para tradução de Libras para português escrito sem glosas,
com foco em aprendizado profundo, aquisição e análise de vídeos e pipelines
reproduzíveis.

[![CI](https://github.com/michaeldouglas/gloss-free/actions/workflows/ci.yml/badge.svg)](https://github.com/michaeldouglas/gloss-free/actions/workflows/ci.yml)

<p align="center">
  <img
    src="materiais/img/livi.png"
    alt="Livi, mascote do projeto de tradução de Libras para português escrito"
    width="280"
  />
</p>

### Livi

Livi é a mascote oficial do projeto. Ela representa a conexão entre Libras, visão computacional,
aprendizado profundo e acessibilidade, valores centrais desta pesquisa.

## Como o projeto está organizado

```text
Dissertacao/
├── app/        aplicação, dados, notebooks e Docker
├── harness/    especificações, agentes, skills e governança
├── materiais/  materiais de pesquisa
└── old/        legado local; não faz parte do desenvolvimento
```

### `app/`

É onde fica o projeto da aplicação.

```text
app/
├── dataset/                 código e testes da aquisição atual
├── data/
│   ├── raw/                 vídeos originais
│   └── manifests/           registros da aquisição
├── docker/video-processing/ ambiente para FFmpeg e ffprobe
├── notebooks/               inventários e análises exploratórias
├── pyproject.toml           dependências e comandos do projeto
└── README.md                instruções específicas da aplicação
```

Os arquivos em `data/raw/` são originais e não devem ser sobrescritos. Dados
processados e resultados devem ser gravados em locais separados.

Para começar:

```powershell
cd app
uv sync
uv run libras --help
uv run python -m unittest discover -s dataset/tests -v
```

Para verificar o ambiente de vídeos:

```powershell
cd app
docker compose -f docker/video-processing/compose.yaml config --quiet
docker compose -f docker/video-processing/compose.yaml build
```

O Docker Desktop precisa estar em execução para construir ou executar o
container.

### `harness/`

É a área de coordenação do projeto. Ela não contém o código principal da
aplicação.

```text
harness/
├── specs/          especificações, planos e tarefas
├── .codex/         agentes e hooks do Codex
├── .agents/skills/ skills usadas pelo projeto
└── graphify-out/   grafo de conhecimento canônico
```

Use o `harness` para planejar e validar mudanças. A aplicação continua em
`app/`, e não deve ser criado um grafo separado dentro dela.

## Regras rápidas

- Trabalhe em uma branch `feature/*`.
- Não faça commits diretamente em `main` ou `develop`.
- Não envie credenciais, arquivos `.env` ou vídeos brutos para o Git.
- Preserve os arquivos originais e registre como os resultados foram gerados.
- Antes de mudanças maiores, atualize a especificação correspondente em
  `harness/specs/`.

## Desenvolvimento e validação

Os testes da aplicação e a construção do ambiente Docker são executados
automaticamente pelo workflow de integração contínua em
`.github/workflows/ci.yml`. O workflow de branches em
`.github/workflows/branch-policy.yml` continua separado e cuida apenas da
governança de branches e Pull Requests.

Para executar as mesmas validações localmente:

```powershell
cd app
uv sync --locked
uv run python -m unittest discover -s dataset/tests -v
docker compose -f docker/video-processing/compose.yaml config --quiet
docker compose -f docker/video-processing/compose.yaml build
```

## Contribuição e citação

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) antes de propor alterações. O
código-fonte deste projeto está sob a licença [MIT](LICENSE). Vídeos, datasets,
artigos e outros materiais mantêm as licenças e condições de uso de suas
fontes originais.

Para citar o software, use o arquivo [CITATION.cff](CITATION.cff).

## Próximos passos

Os próximos passos são ampliar o processamento de vídeos e documentar os
experimentos de aprendizado profundo. A implementação da análise permanece em
`app/`, sem misturar código de execução com os artefatos de governança do
`harness`.
