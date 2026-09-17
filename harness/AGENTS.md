## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Skills locais de revisão de literatura

As skills importadas ficam em `.agents/skills/`. Quando mais de uma puder
ser usada, selecione conforme a finalidade:

O agente principal deve atuar como coordenador: para tarefas de revisão de
literatura, delegue a execução a um subagente e entregue a ele a skill
correspondente. O agente principal pode organizar o pedido, fornecer contexto,
revisar o resultado e integrar os artefatos, mas não deve executar diretamente
o fluxo completo da revisão quando um subagente puder fazê-lo.

- `literature-review-closed-evidence`: priorize quando a revisão deve usar os
  PDFs e documentos fornecidos no próprio projeto, com triagem, extração,
  matrizes e auditoria de citações.
- `research-systematic-literature-review`: priorize para uma RSL formal, com
  protocolo, busca de alta recuperação, auditoria de recall, congelamento do
  corpus, PRISMA e avaliação de confiança.
- `literature-review-ml`: priorize para surveys de aprendizado de máquina ou
  estatística que exijam metadados de datasets, benchmarks, código e
  reprodutibilidade.
- `litreview`: use para orientação inicial e reconhecimento do campo, antes
  de uma revisão completa.

Não trate uma orientação inicial, uma revisão baseada apenas no corpus local
ou uma RSL abrangente como o mesmo tipo de entrega. Registre claramente o
escopo, as fontes utilizadas e as limitações da revisão.

## Fluxo Git e subagente de pesquisa

O agente principal deve coordenar as alterações e delegar a execução das
revisões de literatura ao subagente definido em
`.codex/agents/literature-review-coordinator.md`.

Antes de qualquer alteração em arquivos, o subagente deve perguntar se o
usuário deseja trabalhar em uma branch de funcionalidade no formato
`feature/<slug-da-alteracao>`. Como `main` e `develop` são protegidas, a
resposta negativa não autoriza alterações nessas branches: nesse caso, use
uma branch `feature/*` existente ou aguarde a decisão do usuário.

Regras obrigatórias:

- Nunca faça commit diretamente em `main` ou `develop`.
- Toda alteração deve partir de uma branch `feature/<slug>`.
- O primeiro Pull Request deve ser da feature para `develop` e usar o título
  exato `develop <- feature/<slug>`.
- A promoção para `main` deve ocorrer somente por Pull Request de `develop`
  para `main`, com o título `main <- develop`.
- O subagente deve informar no resumo o que foi alterado, a branch utilizada,
  o commit e o Pull Request correspondente.

## Preservação de trabalho ao iniciar uma nova feature

- Antes de trocar de branch ou iniciar uma nova feature, verifique o estado do
  worktree, incluindo arquivos staged, unstaged e não rastreados.
- Se houver trabalho em andamento, crie um snapshot recuperável e nomeado com
  `git stash push --include-untracked` antes da troca de branch. Nunca use
  `git stash pop` como primeira restauração: aplique o snapshot mantendo-o
  disponível até a confirmação de que o conteúdo foi preservado.
- Crie a nova branch a partir de `develop` e restaure o snapshot nela quando o
  objetivo for continuar o trabalho anterior. Confirme no status e por
  inspeção dos arquivos que o WIP reapareceu.
- Se a restauração produzir conflito, pare e informe os arquivos afetados;
  nunca descarte o snapshot nem resolva o conflito destrutivamente sem
  autorização.
- Trabalho já commitado continua preservado na branch anterior; não exclua a
  branch anterior enquanto a nova ainda não tiver sido validada.
- Arquivos ignorados (por exemplo, segredos locais) devem ser identificados e
  relatados sem serem enviados para o remoto ou adicionados ao commit.
