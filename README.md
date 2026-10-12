# Aprendizado profundo de representações visuais para tradução de Libras para português escrito sem glosas

Projeto de pesquisa para tradução de Libras para português escrito sem glosas,
com foco em aprendizado profundo, aquisição e análise de vídeos e pipelines
reproduzíveis para Machine Learning.

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

## Próximos passos

O próximo passo imediato é consolidar o container de processamento de vídeos
com FFmpeg e `ffprobe`. A implementação da análise será feita depois dentro da
aplicação, sem misturar código de execução com os artefatos de governança.
