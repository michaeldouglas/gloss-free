# Instruções do projeto Dissertacao

Este repositório contém o projeto completo da dissertação. A pasta `old/` é
legado local e permanece ignorada pelo Git; não a inclua em commits ou
revisões.

## Delegação de revisão de literatura

O agente principal deve coordenar e delegar tarefas de revisão de literatura a
um subagente. Para as regras detalhadas, consulte
`harness/.codex/agents/literature-review-coordinator.md` e
`harness/AGENTS.md`.

Escolha a skill conforme o escopo:

- PDFs e documentos locais: `literature-review-closed-evidence`;
- RSL formal e auditável: `research-systematic-literature-review`;
- survey de ML/estatística: `literature-review-ml`;
- orientação inicial: `litreview`.

## Branches e Pull Requests

- `main` e `develop` são protegidas; nunca faça commit direto nelas.
- Trabalhe somente em `feature/<slug>` criada a partir de `develop`.
- Para `develop`, o Pull Request deve vir de `feature/<slug>` e ter o título
  `develop <- feature/<slug>`.
- Para `main`, o Pull Request deve vir de `develop` e ter o título
  `main <- develop`.
- Antes de alterar arquivos, o subagente deve perguntar se o usuário deseja
  usar uma feature branch e registrar branch, commit e PR no resumo.
