# Implementation Plan: Validar Metadados Técnicos de Vídeo

**Branch**: `feature/validar-metadados-video` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

## Summary

Implementar uma validação reproduzível que relacione as declarações de
`annotations.csv` e `error.csv` aos vídeos físicos do dataset, extraia as
propriedades reais de cada arquivo, teste as duas interpretações plausíveis da
coluna `fps` e entregue tabelas estruturadas para o notebook de inventário.
Os vídeos em `data/raw/` serão somente leitura; os resultados ficarão em
`data/processed/metadata-validation/<dataset>/`.

A etapa de qualidade posterior à convenção de nomes reutiliza o JSON técnico e
grava evidências em `data/processed/metadata-validation/reports/` e manifests
derivados em `data/processed/metadata-validation/manifests/`.

## Technical Context

**Language/Version**: Python >=3.10, executado localmente com Python 3.13.7 e
`uv`.

**Primary Dependencies**: Biblioteca padrão Python para leitura, comparação,
JSON, CSV e subprocessos; Typer/Rich já usados pela CLI; pandas já usado pelo
notebook; `pyarrow` para escrita e leitura determinística dos manifests
Parquet. Não será adicionada dependência específica de vídeo.

**Storage**: Vídeos e CSVs originais em `../app/data/raw/`; resultados
derivados em `../app/data/processed/metadata-validation/`; manifestos de
aquisição permanecem em `../app/data/manifests/` e não terão seu contrato
alterado.

**Testing**: `uv run python -m unittest discover -s dataset/tests -v`, com
fixtures temporários e `subprocess.run` controlado; nenhum teste padrão usará
rede, credenciais, Docker ou o corpus bruto.

**Target Platform**: Windows local com PowerShell, `uv` e Docker Desktop; o
mesmo código deve manter invocação sem shell e caminhos explícitos.

**Project Type**: CLI Python com notebook exploratório de dataset.

**Performance Goals**: Processar um lote sem interromper o restante por causa
de uma falha individual e evitar mais de uma inspeção complementar por vídeo
quando `nb_frames` estiver ausente.

**Constraints**: `data/raw/` imutável; entrada do contêiner somente leitura;
saída e temporários separados; nenhum segredo ou rede no contêiner; valores
ausentes, zero, erros e resultados inconclusivos devem permanecer distintos.

**Scale/Scope**: Primeiro dataset V-Librasil, com extensão para os datasets já
configurados pela CLI; uma linha por vídeo e resumos agregados por execução.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Reproducible data acquisition: PASS — a validação preserva a revisão e os
  caminhos já registrados no manifesto e grava a execução da ferramenta.
- Explicit application boundaries: PASS — implementação e testes ficam em
  `../app/`; Spec Kit e governança ficam em `harness/`.
- Testable and safe changes: PASS — testes usam fixtures e substitutos
  determinísticos; o corpus bruto não é alterado.
- Traceability and preservation: PASS — CSV, vídeo, comando, versões,
  parâmetros, status e erros são relacionados nos resultados.
- Maintainable simplicity: PASS — a extração, a comparação, a CLI e o notebook
  terão responsabilidades separadas dentro da arquitetura Flat híbrida.

## Phase 0: Research Decisions

1. Preservar `avg_frame_rate` e `r_frame_rate`; usar a taxa média válida como
   `actual_fps` principal e registrar a origem escolhida.
2. Usar `nb_frames` quando disponível e executar uma segunda consulta com
   `-count_frames` apenas quando necessário; ausência continuará distinta de
   zero e de uma estimativa.
3. Executar o código de vídeo no contêiner existente, com `data/raw` montado
   como somente leitura e `data/processed` como destino gravável.
4. Manter a coluna CSV `fps` intacta e produzir estados independentes para a
   hipótese de taxa de quadros e para a hipótese de quantidade de frames.
5. Registrar tolerância numérica de FPS, versões efetivas de FFmpeg/ffprobe,
   digest da imagem quando disponível, comandos e falhas por arquivo.

## Phase 1: Design & Implementation Structure

### Documentation

```text
specs/003-validar-metadados-video/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── validate-metadata.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Application

```text
../app/
├── dataset/src/libras_translation/
│   ├── video_metadata.py
│   ├── metadata_validation.py
│   ├── dataset_quality_validation.py
│   ├── config.py
│   └── cli.py
├── dataset/tests/
│   ├── test_video_metadata.py
│   ├── test_metadata_validation.py
│   └── test_cli.py
├── notebooks/dataset/01_preparacao_inventario_validacao_datasets.ipynb
├── data/raw/                         # somente leitura
├── data/processed/metadata-validation/
│   ├── reports/                       # evidências e decisão GO/NO-GO
│   └── manifests/                     # manifests Parquet derivados
└── docker/video-processing/           # imagem existente reutilizada
```

### Structure Decision

A implementação permanece na Flat Architecture híbrida atual. `video_metadata`
será responsável por invocar e interpretar a ferramenta externa;
`metadata_validation` será responsável por carregar CSVs, unir registros
físicos e comparar valores; `cli.py` exporá o comando; o notebook apenas
orquestrará a execução e exibirá os arquivos de resultado. Não será criada uma
camada formal de domínio, adaptadores ou Clean Architecture.

## Phase 2: Implementation Outline

1. Criar os tipos e funções de extração, parsing racional de FPS, fallback de
   contagem e registro de erros.
2. Criar a comparação CSV × vídeo, os estados por campo, a classificação das
   hipóteses de `fps`, os CSVs de detalhe e o JSON fonte da execução.
3. Expor `libras video validate-metadata` com seleção de dataset, CSVs,
   diretório de saída e executável da ferramenta.
4. Adicionar testes unitários e de CLI com fixtures temporários e comandos
   falsos controlados.
5. Inserir no notebook a chamada ao comando no Docker e as tabelas antes da
   seção de convenção do nome do arquivo.
6. Documentar execução, interpretação e limitações.
7. Após a convenção de nomes, reconciliar `error.csv` com `annotations.csv` e
   `videos/`, classificar issues, gerar a decisão e materializar os manifests
   Parquet sem tocar nos arquivos brutos.

## Re-evaluation After Design

- `pyarrow` is the only added dependency; the existing Python, pandas, Typer
  and Docker setup remains sufficient for the rest of the workflow.
- The output directory is new and derived, so acquisition manifests remain
  backward compatible.
- The FPS ambiguity is represented explicitly rather than resolved by naming or
  coercion.
- The JSON result is the source of truth; CSVs are tabular projections for the
  notebook and manual inspection.

## Complexity Tracking

No constitution violation or unjustified complexity is introduced.
