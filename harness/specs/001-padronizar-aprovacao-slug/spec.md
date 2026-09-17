# Feature Specification: Padronizar Aprovação de Slug

**Feature Branch**: `feature/padronizar-aprovacao-slug`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Sempre sugerir um nome de slug para a feature e aguardar a aprovação do usuário; se essa regra estiver faltando, ajustar o subagente."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Aprovar o slug antes da alteração (Priority: P1)

Como usuário do projeto, quero receber uma sugestão clara de slug antes de
qualquer criação de branch ou alteração de arquivo, para controlar o nome e o
escopo identificável da feature.

**Why this priority**: A aprovação prévia evita branches e artefatos criados
com nomes inesperados e estabelece o ponto de controle antes de mudanças no
repositório.

**Independent Test**: Solicitar uma alteração ao subagente e verificar que ele
apresenta um slug e aguarda uma resposta explícita antes de criar a branch ou
alterar arquivos.

**Acceptance Scenarios**:

1. **Given** uma solicitação de alteração sem slug aprovado, **When** o
   subagente inicia o atendimento, **Then** ele sugere um slug no formato
   `feature/<slug>` e informa a branch proposta.
2. **Given** uma sugestão de slug apresentada, **When** o usuário ainda não a
   aprova, **Then** o subagente não cria branch nem altera arquivos.
3. **Given** uma sugestão de slug apresentada, **When** o usuário aprova o
   slug, **Then** o subagente pode prosseguir com a branch e as alterações
   autorizadas.

### User Story 2 - Substituir uma sugestão rejeitada (Priority: P2)

Como usuário do projeto, quero rejeitar ou substituir o slug sugerido, para
que a nomenclatura final reflita melhor a intenção da alteração.

**Why this priority**: Permite corrigir nomes ambíguos sem interromper o
fluxo de trabalho e mantém a decisão de nomenclatura com o usuário.

**Independent Test**: Rejeitar uma sugestão, fornecer outro slug e verificar
que somente a opção aprovada é usada no fluxo seguinte.

**Acceptance Scenarios**:

1. **Given** um slug sugerido e não aprovado, **When** o usuário fornece uma
   alternativa, **Then** o subagente confirma a alternativa e aguarda a
   aprovação explícita correspondente.
2. **Given** um slug rejeitado, **When** o usuário não fornece alternativa,
   **Then** o subagente permanece aguardando e não inicia alterações.

### Edge Cases

- Se a solicitação já contiver um slug, o subagente deve apresentá-lo como
  proposta para aprovação, sem tratá-lo como aprovado automaticamente.
- Se o slug contiver espaços, letras maiúsculas ou caracteres incompatíveis,
  o subagente deve propor uma versão normalizada e pedir aprovação dessa
  versão.
- Se o usuário aprovar a branch, mas não deixar claro que aprovou o slug, o
  subagente deve pedir confirmação explícita antes de prosseguir.
- Se já existir uma branch com o slug aprovado, o subagente deve informar o
  conflito e aguardar a escolha entre usar a branch existente ou propor outro
  slug.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O subagente MUST gerar uma sugestão de slug curta, descritiva,
  em minúsculas e com palavras separadas por hífens para cada alteração que
  possa criar ou modificar arquivos.
- **FR-002**: O subagente MUST apresentar o slug no formato
  `feature/<slug>` antes de criar ou selecionar uma branch e antes de alterar
  qualquer arquivo.
- **FR-003**: O subagente MUST aguardar aprovação explícita do usuário para o
  slug antes de prosseguir com a branch ou com alterações no repositório.
- **FR-004**: O subagente MUST propor uma nova opção ou aceitar um slug
  fornecido pelo usuário quando a sugestão for rejeitada.
- **FR-005**: O subagente MUST manter a proteção de `main` e `develop`, usando
  uma branch `feature/*` criada a partir de `develop` ou uma branch de feature
  existente autorizada pelo usuário.
- **FR-006**: As instruções do subagente MUST registrar a regra de sugestão,
  aprovação e bloqueio de alterações de forma inequívoca e operacional.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das revisões de solicitações que alterem arquivos, o
  subagente apresenta um slug antes de qualquer alteração no repositório.
- **SC-002**: Em 100% dos casos sem aprovação explícita, nenhuma branch nova é
  criada e nenhum arquivo é alterado pelo subagente.
- **SC-003**: Em 100% dos casos de rejeição, o subagente oferece uma nova
  proposta ou usa a alternativa fornecida pelo usuário antes de prosseguir.
- **SC-004**: Uma revisão das instruções do subagente identifica uma única
  regra consistente de aprovação do slug, sem conflito com as regras de
  proteção de branches do projeto.

## Assumptions

- A aprovação explícita pode ser uma resposta afirmativa ao slug proposto ou
  a indicação clara de um slug alternativo.
- O slug da branch e o nome do diretório da especificação podem ser
  diferentes; esta feature controla a aprovação do slug da branch.
- A proteção de `main` e `develop` continua válida e não é flexibilizada.
- A primeira versão desta feature altera as instruções do subagente e seus
  artefatos de especificação; não altera o código da aplicação.
