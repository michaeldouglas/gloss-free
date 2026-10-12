# Data Model: Estruturar Projeto App

Esta feature mantém os artefatos de governança e registra as entidades de
execução já implementadas para a aquisição reproduzível.

## Entidades

### Dataset Catalog

- **Fonte**: `DATASETS` em `../app/dataset/src/libras_translation/config.py`.
- **Conteúdo**: nome local e identificador do repositório Hugging Face.
- **Regra**: datasets desconhecidos são rejeitados pela aplicação.

### Remote File

- **Fonte**: `RemoteFile` em `infrastructure/huggingface_client.py`.
- **Conteúdo**: caminho remoto e tamanho esperado, quando disponível.
- **Regra**: caminhos absolutos ou com `..` não podem ser gravados no destino.

### Dataset Manifest

- **Localização**: `../app/data/manifests/<dataset>.json`.
- **Conteúdo**: repositório, commit resolvido, data de aquisição, arquivos,
  caminhos locais, tamanhos esperados, estado e erro.
- **Estados**: `pending`, `downloaded`, `skipped_existing` e `failed`.
- **Regra**: atualizações são gravadas atomicamente e podem ser retomadas.

### Acquisition Result

- **Fonte**: retorno de `DatasetAcquisition.run`.
- **Conteúdo**: dataset, commit, quantidades listadas, baixadas, reutilizadas,
  auxiliares e falhas.
- **Regra**: falhas individuais são reportadas sem ocultar o resumo da operação.

## Artefatos de Governança

- `../app/`: aplicação, dados, configuração e testes.
- `harness/`: `.specify/`, `specs/` e instruções de coordenação.
- `specs/002-estruturar-projeto-app/tasks.md`: registro das tarefas concluídas.

## Relacionamentos

`Dataset Catalog` identifica o repositório; `Remote File` descreve cada item;
`Dataset Manifest` registra o estado local de cada item; `Acquisition Result`
resume a operação apresentada pela CLI.
