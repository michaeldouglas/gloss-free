# Implementation Plan: Estruturar Projeto App

**Branch**: `feature/estruturar-projeto-app` | **Date**: 2026-09-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-estruturar-projeto-app/spec.md`

## Summary

Estabelecer `app/` como a raiz da aplicação e fornecer uma base mínima,
executável e documentada para as próximas features. O plano mantém os
artefatos do Spec Kit em `harness/`, documenta o pré-requisito de Python
declarado no projeto e cria uma validação de fumaça reproduzível a partir de
`app/`.

## Technical Context

**Language/Version**: Python >=3.14, conforme `app/pyproject.toml`; o ambiente local verificado possui Python 3.13.7 e não atende ao requisito ainda

**Primary Dependencies**: Nenhuma dependência de runtime declarada; `uv` 0.9.12 está disponível para gerenciamento local

**Storage**: N/A nesta feature de bootstrap

**Testing**: Verificação de fumaça da entrada principal; suíte dedicada será definida quando a primeira funcionalidade de negócio for especificada

**Target Platform**: Ambiente local Windows de desenvolvimento, com execução independente do diretório `harness/`

**Project Type**: Aplicação Python mínima executável localmente

**Performance Goals**: A verificação inicial deve concluir em até 10 segundos após os pré-requisitos estarem disponíveis

**Constraints**: `app/` contém o código da aplicação; `harness/` contém governança e artefatos Spec Kit; `old/` permanece legado ignorado; nenhuma dependência externa é necessária para a base

**Scale/Scope**: Uma base executável, documentação de entrada e uma verificação mínima; sem funcionalidades de negócio nesta feature

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

O arquivo de constituição ainda contém somente placeholders e não define
princípios ratificados ou gates executáveis. A feature é limitada à
organização e validação da base do projeto, sem dependências novas nem
alteração das regras de branches.

**Gate inicial**: PASS — não há restrição ratificada aplicável.

**Gate pós-design**: PASS — o desenho permanece pequeno, reversível e separado
do harness.

## Project Structure

### Documentation (this feature)

```text
specs/002-estruturar-projeto-app/
├── plan.md              # This file ($speckit-plan command output)
├── research.md          # Phase 0 output ($speckit-plan command)
├── data-model.md        # Phase 1 output ($speckit-plan command)
├── quickstart.md        # Phase 1 output ($speckit-plan command)
├── contracts/           # Phase 1 output ($speckit-plan command)
└── tasks.md             # Phase 2 output ($speckit-tasks command - NOT created by $speckit-plan)
```

### Source Code (repository root)
```text
app/
├── README.md                  # Entrada, pré-requisitos e validação
├── pyproject.toml             # Metadados e requisito de Python
├── main.py                    # Entrada mínima atual
└── tests/                     # Verificações da aplicação, quando criadas

harness/
├── .specify/                  # Scripts, templates e configuração do Spec Kit
└── specs/                     # Especificações e planos das features
```

**Structure Decision**: Manter um projeto Python simples em `app/` e uma área
de governança separada em `harness/`. A documentação de execução pertence a
`app/README.md`; o planejamento e os contratos de feature pertencem a
`harness/specs/`. Não criar `src/`, frontend, backend ou contratos externos
antes de existir uma necessidade funcional correspondente.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Nenhuma | Não há violação da constituição ratificada. | A estrutura simples atende ao bootstrap. |
