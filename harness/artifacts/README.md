# Artefatos do projeto

Esta pasta reúne artefatos derivados para consulta e apresentação.

```text
artifacts/
├── architecture/
│   ├── source/   # candidatos Archify versionáveis
│   └── html/     # diagramas Archify publicados
└── reports/
    ├── executions/ # relatórios gerados pelo notebook
    └── latest.*     # atalho para a execução mais recente
```

O showroom público é uma camada derivada em `../docs/`. O gerador
`scripts/build_showroom.py` lê estes artefatos e os resumos de validação em
`../app/data/processed/metadata-validation/`; ele não copia nem publica
`../app/data/raw/`.

Os dados originais continuam em `../app/data/raw/` e não são copiados nem
alterados por este fluxo. Os relatórios técnicos completos de validação
continuam em `../app/data/processed/metadata-validation/`; os relatórios em
`artifacts/reports/executions/` resumem a execução para consulta humana.

O hook de arquitetura só publica um diagrama quando encontra um candidato
`architecture/source/*.architecture.json`. Sem esse candidato, ele apenas
registra que a atualização está pendente.

O notebook pode reconstruir o showroom com `RUN_SHOWROOM_BUILD = True`. A
configuração inicial do GitHub Pages deve usar a branch `main` e a pasta
`/docs`; depois, as alterações geradas em `docs/` precisam ser versionadas e
enviadas junto com os artefatos que as originaram.
