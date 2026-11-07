# Quickstart — Etapa 2 EDA

Este quickstart descreve a execução autorizada da caracterização e da EDA sem
ler `app/data/raw/` e sem executar `ffprobe` novamente.

## Pré-condições

- A Etapa 1 está fechada com `global_stage1_decision = GO` e
  `stage1_status = completed`.
- Os manifests canônicos validados existem nos caminhos definidos em
  `contracts/analysis-contract.md`.
- O ambiente Python do aplicativo está disponível em `app/.venv` e os comandos
  são executados com `uv run` a partir de `app/`.

## Testes

```powershell
cd app
uv run python -m unittest discover -s dataset/tests -v
```

Os testes não baixam datasets, não usam credenciais e não alteram os manifests.

## Execução controlada

O notebook `app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb`
chama `run_stage2_eda`, que publica as Partes 1–7 em um único run. A execução
cria um diretório privado em `app/data/processed/eda/archive/<run_id>`, valida
tabelas, figuras, hashes e denominadores e só depois promove a publicação
corrente por meio de `provenance/CURRENT.json`. A publicação anterior permanece
no archive.

Flags exploratórias não viram filtros automáticos.

## Verificações mínimas

Depois da execução, confira:

- `provenance/CURRENT.json` e `archive/<run_id>/provenance/execution.json`;
- hashes e schema dos dois manifests em `inputs`;
- `validation.all_passed = true`;
- datasets separados e denominadores explícitos nas tabelas;
- ausência de imputação, remoção, split, balanceamento e `ffprobe`;
- outputs derivados somente sob `app/data/processed/eda/`.
