# Tasks: Estruturar Projeto App

**Status**: Complete
**Feature**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)

Este arquivo registra retrospectivamente as tarefas executadas e verificadas
para fechar a feature. Todas as tarefas estão concluídas; uma nova necessidade
deve iniciar uma nova especificação e um novo conjunto de tarefas.

## Phase 1: Setup

- [x] T001 [P] Confirmar a raiz da aplicação em `../app/` e a separação dos artefatos em `specs/` e `../app/README.md`.
- [x] T002 [P] Registrar o projeto Python e a entrada CLI em `../app/pyproject.toml`.

## Phase 2: Foundational

- [x] T003 Implementar configuração de caminhos, datasets e leitura segura de `HF_TOKEN` em `../app/dataset/src/libras_translation/config.py`.
- [x] T004 Implementar o adaptador oficial do Hugging Face em `../app/dataset/src/libras_translation/infrastructure/huggingface_client.py`.
- [x] T005 Implementar resolução de revisão, aquisição concorrente, retomada e gravação atômica de manifestos em `../app/dataset/src/libras_translation/acquisition.py`.

## Phase 3: User Story 1 — Executar a base do aplicativo

- [x] T006 [US1] Implementar os comandos `data list` e `data download` em `../app/dataset/src/libras_translation/cli.py`.
- [x] T007 [US1] Cobrir configuração, listagem, limites, downloads, retomada, caminhos Unicode e manifestos em `../app/dataset/tests/test_acquisition.py`.
- [x] T008 [US1] Cobrir ajuda, validação de argumentos, opções e resumos da CLI em `../app/dataset/tests/test_cli.py`.
- [x] T009 [US1] Verificar a suíte determinística com `uv run python -m unittest discover -s dataset/tests -v`, sem rede real ou credenciais.

## Phase 4: User Story 2 — Identificar os limites do projeto

- [x] T010 [US2] Documentar instalação, comandos, dados, manifestos, credenciais e limites em `../app/README.md`.
- [x] T011 [US2] Registrar o modelo de aplicação, manifestos e relacionamentos em `data-model.md`.
- [x] T012 [US2] Registrar o procedimento executável e os critérios de validação em `quickstart.md`.

## Phase 5: Polish and Closure

- [x] T013 Atualizar `spec.md`, `plan.md`, `research.md` e `checklists/requirements.md` para o estado implementado.
- [x] T014 Preencher a constituição do projeto em `.specify/memory/constitution.md`.
- [x] T015 Confirmar `uv run libras --help` e registrar a evidência de fechamento em `plan.md`.

## Dependencies

```text
T001 -> T002 -> T003 -> T004 -> T005
T005 -> T006 -> T007 -> T008 -> T009
T001 -> T010 -> T011 -> T012
T009 + T010 + T011 + T012 -> T013 -> T014 -> T015
```

## Parallel Opportunities

- T001 e T002 podem ser verificados em paralelo.
- T003 e T004 podem ser desenvolvidos em paralelo antes de T005.
- T007 e T008 podem ser executados em paralelo depois da implementação da CLI.
- T010, T011 e T012 podem ser atualizados em paralelo após a definição da estrutura.

## Independent Test Criteria

- **US1**: a CLI exibe ajuda e a suíte executa 11 testes com sucesso sem rede real.
- **US2**: README, quickstart e estrutura de diretórios apontam para `../app/` e
  distinguem o harness dos arquivos de aplicação.

## Closure

Não há tarefas abertas, tarefas de convergência ou trabalho de implementação
restante no escopo desta feature. A próxima mudança deve começar por uma nova
feature `specify`, sem reabrir esta lista.
