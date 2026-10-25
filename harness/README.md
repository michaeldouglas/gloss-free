# Harness da dissertação

Este diretório coordena o desenvolvimento da dissertação. O código da
aplicação permanece em `../app/`; o harness contém governança, automações,
Spec Kit, relações estruturais e artefatos derivados.

## Fontes de verdade

| Assunto | Fonte |
| --- | --- |
| Regras e princípios | `.specify/memory/constitution.md` |
| Instruções dos agentes | `AGENTS.md` |
| Features, planos e tarefas | `specs/` |
| Relações estruturais | `graphify-out/` |
| Resultados técnicos e científicos | `../app/data/processed/` |
| Modelos e evidências arquiteturais | `artifacts/architecture/` |
| Reports e projeções derivadas | `artifacts/reports/` |
| Showroom publicado | `../docs/` |
| Apresentações e tema Slidev | `presentations/` |
| Snapshots públicos por versão | `artifacts/reports/publications/` |

`app/data/processed/` é a evidência produzida pela aplicação. Os arquivos em
`artifacts/reports/` e `docs/` são projeções para consulta humana e publicação;
eles não substituem os resultados técnicos.

## Runtime

Hooks e automações do harness usam Bun e TypeScript. A versão esperada está em
`.bun-version`. A aplicação Python deve ser executada a partir de `../app/`
com `uv run ...`.

```text
bun run check       # valida os entrypoints declarados em .codex/hooks.json
bun test            # executa os testes determinísticos do harness
bun run core/scripts/verify-harness.ts prepare
```

O Graphify canônico fica em `graphify-out/`; não crie uma segunda saída em
`app/graphify-out/`. Depois de mudanças relevantes no código, execute
`graphify update .` a partir desta pasta.

## Artefatos e publicação

Os modelos Archify versionáveis ficam em
`artifacts/architecture/source/`; seus HTML e recibos são derivados em
`artifacts/architecture/html/`. O script de refresh valida e renderiza modelos
existentes; ele não reconstrói automaticamente a arquitetura a partir do
código.

O showroom é gerado por `core/scripts/build-showroom.ts`, usando os reports do
harness e os resumos técnicos disponíveis em `../app/data/processed/`. A
publicação deve gerar e validar o showroom antes de enviar o conteúdo de
`../docs/` ao GitHub Pages.

## Apresentações científicas

As apresentações usam Slidev em um pacote próprio em `presentations/`, com
dependências e lockfile separados. O pacote não faz parte de `../app/` e não
executa análise científica. Os slides usam Markdown; componentes Vue ficam em
`presentations/components/`; estilos e layouts compartilhados pertencem ao
tema.

Cada versão publicada possui um snapshot derivado em
`artifacts/reports/publications/<id>.json`. O snapshot é preparado a partir dos
relatórios em `../app/data/processed/`, de `artifacts/reports/latest.json` e do
estado dos artefatos Spec Kit. Ele contém somente campos públicos permitidos,
origens relativas e hashes das fontes; caminhos absolutos e dados brutos não
são copiados. A evidência científica primária continua em
`../app/data/processed/`; o snapshot serve à reprodução do showroom e do deck
em um checkout limpo do CI.

Como `../app/data/processed/` é ignorado pelo Git, gere o snapshot na máquina
que possui os resultados e revise o arquivo antes de adicioná-lo:

```text
bun run core/scripts/prepare-presentation-release.ts --id 2026-11-15-reuniao-orientador --title "Progresso da pesquisa — 15 de novembro de 2026" --summary "Síntese curta do avanço e das evidências deste checkpoint."
```

Depois, crie `presentations/decks/<id>/release.json` e `slides.md`, cite as
fontes nas lâminas e mantenha versões anteriores imutáveis. O build processa
todas as versões do índice e atualiza `../docs/apresentacoes/latest.pptx` para
a versão mais recente:

```text
cd presentations
bun install --frozen-lockfile
bun run build
```

O catálogo em `../docs/apresentacoes/` oferece o PPTX mais recente como ação
principal e permite selecionar versões pelo checkpoint. O HTML e o PDF ficam
disponíveis como formatos complementares. O workflow do Pages gera showroom,
apresentações e exports antes do build Jekyll.

## Estrutura preservada

`.codex/`, `.agents/`, `.specify/`, `specs/`, `graphify-out/` e `artifacts/`
permanecem em suas localizações atuais. O código próprio do harness fica em
`core/hooks/`, `core/scripts/`, `core/lib/` e `core/assets/`.
