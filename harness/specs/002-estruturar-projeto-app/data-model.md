# Data Model: Estruturar Projeto App

Esta feature não introduz entidades de domínio nem armazenamento persistente.
O modelo abaixo descreve somente os artefatos e estados necessários para
validar a separação do projeto.

## Artefatos

### Aplicação

- **Localização**: `app/`
- **Conteúdo**: código executável, metadados do projeto, documentação e
  verificações da aplicação.
- **Regra**: não deve conter os artefatos de governança do Spec Kit.

### Harness

- **Localização**: `harness/`
- **Conteúdo**: `.specify/`, `specs/`, instruções e scripts de planejamento.
- **Regra**: coordena o desenvolvimento, mas não é a raiz de execução da
  aplicação.

### Procedimento de validação

- **Entradas**: diretório atual, versão de Python e arquivos do projeto.
- **Estados**:
  - `não verificado`: os pré-requisitos ainda não foram conferidos;
  - `bloqueado`: algum pré-requisito está ausente ou incompatível;
  - `aprovado`: a entrada da aplicação executou e produziu a saída esperada.
- **Transições**:
  - `não verificado` → `bloqueado` quando Python 3.14+ não está disponível;
  - `não verificado` → `aprovado` quando a execução mínima termina com sucesso;
  - `bloqueado` → `aprovado` após corrigir o pré-requisito e repetir a validação.

## Relacionamentos

`harness/specs/<feature>/spec.md` descreve a necessidade; o plano define a
validação; `app/` recebe a implementação quando as tarefas forem executadas.
Nenhuma entidade de negócio é criada nesta feature.
