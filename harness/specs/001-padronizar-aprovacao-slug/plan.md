# Implementation Plan: Padronizar Aprovação de Slug

**Branch**: `feature/padronizar-aprovacao-slug` | **Date**: 2026-09-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-padronizar-aprovacao-slug/spec.md`

## Summary

Esta feature torna obrigatória a sugestão e a aprovação explícita do slug da
branch antes de o subagente coordenador de revisão de literatura criar ou
selecionar uma branch e alterar arquivos. A implementação consiste em
atualizar as instruções operacionais do subagente, mantendo as regras de
proteção de `main` e `develop`, e validar o fluxo por inspeção documental e
cenários reproduzíveis.

## Technical Context

**Language/Version**: Markdown e JSON; sem linguagem de execução

**Primary Dependencies**: Spec Kit CLI 1.0.1 e instruções do agente Codex; sem dependências de aplicação

**Storage**: Arquivos versionados no repositório; sem armazenamento em runtime

**Testing**: Revisão dos cenários, busca por placeholders, `git diff --check` e verificação dos arquivos gerenciados pelo Spec Kit

**Target Platform**: Ambiente Windows com Codex e Spec Kit

**Project Type**: Configuração e governança documental de agentes

**Performance Goals**: O fluxo deve exigir no máximo uma confirmação explícita antes do prosseguimento normal

**Constraints**: `main` e `develop` permanecem protegidas; nenhuma alteração ocorre sem slug aprovado; a instalação do Spec Kit e seus arquivos gerenciados devem ser preservados

**Scale/Scope**: Um subagente coordenador, uma regra de aprovação, uma branch de feature e os artefatos documentais desta feature

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

A constituição atual ainda contém apenas placeholders e não define princípios
ratificados ou gates executáveis. Não há uma violação identificável para esta
feature. A alteração é limitada às instruções do subagente e aos artefatos do
Spec Kit, sem código de aplicação, dependências novas ou mudança nas regras de
proteção de branches.

**Gate inicial**: PASS — nenhuma restrição ratificada aplicável foi encontrada.

**Gate pós-design**: PASS — o design permanece documental, reversível e dentro
do escopo da especificação.

## Project Structure

### Documentation (this feature)

```text
specs/001-padronizar-aprovacao-slug/
├── plan.md              # Plano de implementação
├── research.md          # Decisões e alternativas da Fase 0
├── data-model.md        # Modelo do estado conversacional
├── quickstart.md        # Guia de validação
├── contracts/           # Não aplicável: não há interface externa
└── tasks.md             # Será criado pela etapa speckit-tasks
```

### Source Code (repository root)

```text
.codex/
└── agents/
    └── literature-review-coordinator.md  # Regra operacional do subagente

.agents/
└── skills/                               # Skills instaladas do Spec Kit

.specify/
├── feature.json                          # Ponteiro da feature ativa
└── ...                                    # Templates, scripts e manifests

specs/001-padronizar-aprovacao-slug/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
└── quickstart.md
```

**Structure Decision**: A mudança será mantida nos arquivos de instrução do
subagente e nos artefatos documentais da feature. Não há diretório de código
fonte nem suíte de testes de aplicação envolvidos; a validação será executada
contra os próprios documentos e o estado do repositório.

## Complexity Tracking

Não aplicável: não há violações da constituição ratificada a justificar.
