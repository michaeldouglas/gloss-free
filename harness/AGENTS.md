## Escopo do projeto

Este harness coordena o repositório da dissertação, cuja raiz é a pasta pai. O diretório `../old/` é legado local, permanece ignorado pelo Git e não deve ser incluído em revisões, commits ou Pull Requests.

## Arquitetura do aplicativo

O aplicativo em `../app/` segue deliberadamente uma **Flat Architecture híbrida**. A organização deve permanecer pragmática e orientada aos módulos do projeto, com separação pontual de responsabilidades quando isso ajudar a manter o código compreensível.

Essa arquitetura não deve ser reinterpretada ou reestruturada automaticamente como Clean Architecture, arquitetura hexagonal ou outra arquitetura em camadas rígida. A pasta `infrastructure/` pode isolar integrações externas, mas isso não transforma o projeto em uma arquitetura formal de portas e adaptadores.

## Runtime da infraestrutura

Hooks e automações do harness ficam em TypeScript e são executados com Bun. Os entrypoints do Codex estão em `core/hooks/`; módulos compartilhados ficam em `core/lib/`; scripts de infraestrutura e Spec Kit ficam em `core/scripts/`. Use `bun run ...`, `bun test` e `bun run check`. Não reintroduza wrappers PowerShell ou Node.js para lógica do harness. Módulos internos empacotados por ferramentas locais, como o Archify, podem manter o formato upstream, mas devem ser chamados pelo harness via Bun.

Python permanece no aplicativo para processamento de datasets e vídeo, EDA, estatística, ML, treinamento, inferência e avaliação. Execute comandos do aplicativo a partir de `../app/` usando `uv run ...`; não converta o código científico para TypeScript.

## Narrativa científica do showroom

Toda geração de `../docs/` deve preservar o contrato em `core/assets/showroom-report-contract.md`. A configuração `core/assets/showroom-project.json` mantém o foco científico, a finalidade da etapa atual e os limites de interpretação; os resultados da execução devem continuar vindo dos reports e resumos técnicos, sem números ou conclusões duplicados manualmente. O build do showroom valida a presença dessa narrativa e dos links para os detalhes e deve falhar se o contrato não for atendido.

Antes de alterar afirmações científicas, confira as fontes indicadas no contrato. Para novas interpretações de resultados ou mudanças de etapa, coordene com `.codex/agents/scientific-data-analysis-coordinator.md` e use somente as skills adequadas à etapa. Delegue ao especialista de vídeo apenas conclusões que dependam de inspeção audiovisual; envolva revisão de literatura somente quando houver afirmações baseadas em literatura externa. Não execute esses agentes como etapa automática para renderizar dados já validados.

## Design visual do showroom

Quando a tarefa alterar a aparência, hierarquia, navegação ou legibilidade de `docs/`, use as skills locais de forma complementar e na ordem adequada ao trabalho:

1. `ui-ux-pro-max` (`.agents/skills/ui-ux-pro-max/SKILL.md`) é a referência principal para escolher direção visual, tipografia, paleta, espaçamento e padrões de leitura. Trate o showroom como relatório científico/documentação, com foco em compreensão e leitura responsiva; detecte a stack real (HTML/CSS estático) e não introduza framework ou dependências por conveniência.
2. `impeccable` (`.agents/skills/impeccable/SKILL.md`) orienta crítica e refinamento da interface existente. Para um ajuste pontual, preserve identidade, conteúdo e comportamento existentes; siga o carregamento de contexto e leia `reference/craft-floor.md` imediatamente antes de editar UI. Use o modo `Read` para páginas de relatório/documentação.
3. `web-design-guidelines` (`.agents/skills/web-design-guidelines/SKILL.md`) faz a revisão final de acessibilidade, responsividade e qualidade técnica. Antes de cada auditoria, busque as regras atualizadas na fonte indicada pela própria skill e registre achados com arquivo e linha.
4. `emil-design-eng` (`.agents/skills/emil-design-eng/SKILL.md`) só entra quando a mudança realmente precisar de animação ou microinteração. Não adicione movimento decorativo ao relatório por padrão; qualquer movimento deve respeitar `prefers-reduced-motion`.

Não execute as quatro skills em toda regeneração: a atualização rotineira de dados continua usando `bun run core/scripts/build-showroom.ts`. Em trabalho visual, edite as fontes (`core/scripts/build-showroom.ts` e `core/assets/showroom.css`), regenere `../docs/` e confira o resultado renderizado; não edite manualmente as páginas geradas. Preserve integralmente o contrato científico e não altere o significado de métricas, decisões ou conclusões para obter efeito visual. Não mantenha sistemas de tokens concorrentes; se uma reformulação visual ampla exigir documentação persistente, escolha uma única fonte visual canônica e reconcilie nela as recomendações das skills.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

The canonical Graphify output is `harness/graphify-out/`. The sibling application in `../app/` is represented in this graph under repo `app`; do not keep a second `../app/graphify-out/`. When refreshing application code, merge its extracted graph into this canonical graph and leave the generated output here.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Apresentações científicas

Apresentações ficam em `presentations/`, como pacote Slidev separado do
runtime do harness e do código em `../app/`. Não leia dados brutos no Slidev:
use snapshots públicos versionados em `artifacts/reports/publications/`,
gerados com `core/scripts/prepare-presentation-release.ts`. Cada snapshot é
uma projeção com origens relativas; preserve as datas e limitações das
evidências e não substitua versões já publicadas. HTML, PDF e PPTX publicados
são saídas derivadas em `../docs/apresentacoes/`, construídas por
`core/scripts/build-presentations.ts` antes do Pages/Jekyll.

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

## Tradução de PDFs com preservação de layout

Para traduzir PDFs do corpus sem perder imagens, colunas, gráficos ou a camada
de texto selecionável, use a skill local
`.agents/skills/pdf-translation-layout/SKILL.md` e o subagente
`.codex/agents/pdf-translation-coordinator.md`. O script reutilizável fica em
`.agents/skills/pdf-translation-layout/scripts/translate_pdf_layout.py`.

O original deve permanecer intacto. Por padrão, leia `../materiais/en` e grave
as cópias em `../materiais/pt`. Valide páginas, imagens, extração de texto e
fragmentos truncados antes de concluir; blocos de matemática, CJK ou símbolos
que não possam ser representados com segurança devem ser preservados do
original, não substituídos por `?`.

## Processamento reprodutível de vídeos

Para tarefas de inspeção, validação ou pré-processamento audiovisual, delegue
ao subagente `.codex/agents/video-processing-specialist.md`. O escopo inclui
`ffprobe`, FFmpeg, codecs, FPS, resolução, duração, frames, amostragem temporal
e Docker usado para isolar o pipeline.

Use a skill local `.agents/skills/docker-patterns/SKILL.md` para decisões de
containerização. A referência upstream de FFmpeg é a skill `video-editing` do
ECC, disponível em:
`https://github.com/affaan-m/ECC/blob/main/skills/video-editing/SKILL.md`.
Ela não deve ser tratada como uma skill separada chamada `ffmpeg`, nem seu
escopo de edição criativa deve ser aplicado automaticamente a este projeto.

O subagente deve manter `../app/data/raw/` imutável, gravar derivados em área
separada, produzir JSON/CSV com parâmetros e logs, validar as saídas e
considerar a preservação de mãos, expressões faciais e contexto corporal em
vídeos de Libras. A aplicação permanece fora do escopo desta alteração; quando
for implementada, seus módulos e testes deverão ficar em `../app/` conforme a
arquitetura flat híbrida existente.

## Fluxo Git e subagente de pesquisa

O agente principal deve coordenar as alterações e delegar a execução das
revisões de literatura ao subagente definido em
`.codex/agents/literature-review-coordinator.md`.

Antes de alterar arquivos, pergunte ao usuário se deseja trabalhar em uma
branch de funcionalidade no formato `feature/<slug>`. Registre a branch, o
commit e o Pull Request correspondente no resumo final.

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
