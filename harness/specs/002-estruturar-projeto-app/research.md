# Research: Estruturar Projeto App

**Feature**: [spec.md](spec.md)

**Data**: 2026-09-16

## Decision: Manter `app/` separado do harness

**Decision**: O código executável, a configuração do projeto e a documentação
de execução ficam em `app/`; o Spec Kit, suas especificações e scripts ficam
em `harness/`.

**Rationale**: O usuário definiu `app/` como o local do projeto. A separação
preserva o harness como ferramenta de governança e reduz o risco de misturar
arquivos de aplicação com artefatos de planejamento.

**Alternatives considered**:

- Colocar o código diretamente em `harness/`: rejeitado porque mistura a
  aplicação com os artefatos do Spec Kit.
- Mover o Spec Kit para `app/`: rejeitado porque altera a estrutura operacional
  existente e torna o próprio projeto responsável por hospedar sua ferramenta
  de planejamento.

## Decision: Preservar a configuração Python existente nesta feature

**Decision**: O plano usa a declaração atual de `app/pyproject.toml` como
fonte de verdade e não altera ainda o requisito `Python >=3.14`.

**Rationale**: A solicitação atual é estruturar e planejar o projeto. Alterar a
versão sem uma decisão explícita sobre compatibilidade poderia mascarar uma
escolha de ambiente. A inspeção registrou que a máquina atual possui Python
3.13.7, portanto o quickstart deve falhar de forma clara até que Python 3.14+
esteja disponível ou o requisito seja deliberadamente revisado em uma feature
própria.

**Alternatives considered**:

- Reduzir o requisito para Python 3.13: rejeitado por não estar autorizado e
  por poder divergir da intenção já registrada no projeto.
- Adicionar dependências ou um framework agora: rejeitado porque não há
  requisito de negócio que justifique essa complexidade no bootstrap.

## Decision: Usar uma verificação de fumaça mínima

**Decision**: A primeira validação deve executar a entrada atual da aplicação e
confirmar a saída esperada, depois de validar o requisito de Python.

**Rationale**: A base atual não possui dependências nem uma suíte de testes
dedicada. Uma verificação de fumaça é suficiente para provar que a estrutura
está localizada e executável antes de adicionar funcionalidades.

**Alternatives considered**:

- Introduzir pytest nesta feature: rejeitado por adicionar uma dependência sem
  necessidade funcional.
- Criar testes de integração completos: rejeitado porque ainda não há fluxo de
  negócio ou contrato externo para testar.
