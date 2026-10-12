# Implementation Plan: Estruturar Projeto App

**Branch**: `feature/estruturar-projeto-app`
**Date**: 2026-10-11
**Spec**: [spec.md](spec.md)
**Status**: Complete

## Summary

Estabelecer `../app/` como a raiz da aplicação e registrar a base executável
que foi implementada para aquisição reproduzível de datasets de Libras. O
harness permanece responsável pela governança e pelos artefatos do Spec Kit.

## Technical Context

**Language/Version**: Python >=3.10, conforme `../app/pyproject.toml`
**Primary Dependencies**: `huggingface_hub`, `typer`, `rich`, `python-dotenv`
e dependências de análise declaradas no projeto
**Storage**: Arquivos originais em `../app/data/raw/` e manifestos JSON em
`../app/data/manifests/`
**Testing**: 11 testes determinísticos com `unittest`; nenhum teste padrão
realiza download ou exige credenciais
**Target Platform**: Windows local com PowerShell e `uv`
**Project Type**: CLI Python para aquisição de datasets
**Constraints**: `../app/` contém a aplicação; `harness/` contém governança;
`../old/` permanece fora do escopo; credenciais não podem ser registradas
**Scale/Scope**: Dois datasets configurados, aquisição retomável, listagem,
download limitado e download concorrente de arquivos auxiliares

## Constitution Check

*GATE: verified against the ratified constitution before closure.*

- Reproducible acquisition: PASS — commits, caminhos e estados são registrados
  nos manifestos.
- Explicit boundaries: PASS — aplicação e harness permanecem separados.
- Testable and safe changes: PASS — 11 testes passam sem rede real.
- Traceability and preservation: PASS — revisão remota, caminhos e tamanhos
  esperados são mantidos; gravações de manifestos são atômicas.
- Maintainable simplicity: PASS — CLI, coordenação, configuração e cliente
  externo permanecem em módulos separados.

## Implemented Structure

```text
../app/
├── README.md
├── pyproject.toml
├── data/
│   ├── manifests/
│   └── raw/
└── dataset/
    ├── src/libras_translation/
    │   ├── cli.py
    │   ├── config.py
    │   ├── acquisition.py
    │   └── infrastructure/huggingface_client.py
    └── tests/

harness/
├── .specify/
└── specs/002-estruturar-projeto-app/
```

## Completed Phases

### Phase 0: Boundary and project setup

- Confirmed `../app/` as the application root.
- Kept Spec Kit artifacts in `harness/`.
- Preserved the legacy `../old/` exclusion.

### Phase 1: Acquisition foundation

- Added project metadata and the `libras` CLI entry point.
- Added configuration for project paths, datasets, and `HF_TOKEN`.
- Added the Hugging Face adapter with explicit dataset revision resolution.

### Phase 2: Acquisition behavior

- Implemented listing without download.
- Implemented bounded and concurrent downloads.
- Implemented atomic, resumable JSON manifests.
- Preserved auxiliary dataset files and Unicode remote paths.
- Added user-facing error handling and Rich summaries.

### Phase 3: Verification and documentation

- Added acquisition and CLI tests using fakes and temporary directories.
- Documented setup, commands, data layout, credential handling, and scope.
- Verified 11 tests and the CLI help output.

## Completion Validation

```text
uv run python -m unittest discover -s dataset/tests -v
Ran 11 tests ... OK

uv run libras --help
Exit code: 0
```

No implementation task remains for this feature. Further behavior must be
defined as a new feature specification rather than appended to this bootstrap.

## Complexity Tracking

No unresolved constitution violation or unjustified complexity remains in the
scope of this feature.
