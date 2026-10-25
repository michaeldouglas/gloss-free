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

## Estrutura preservada

`.codex/`, `.agents/`, `.specify/`, `specs/`, `graphify-out/` e `artifacts/`
permanecem em suas localizações atuais. O código próprio do harness fica em
`core/hooks/`, `core/scripts/`, `core/lib/` e `core/assets/`.
