# Research: Padronizar Aprovação de Slug

## Escopo da pesquisa

Não foi necessária pesquisa externa. A feature altera somente instruções
locais do subagente e artefatos de governança do repositório; não há biblioteca,
serviço externo, formato de API ou decisão tecnológica desconhecida.

## Decisões

### Decisão: usar uma confirmação explícita do slug antes de qualquer mutação

- **Rationale**: preserva o controle do usuário sobre a nomenclatura e impede
  que branch ou arquivo seja criado com uma intenção presumida.
- **Alternativas consideradas**: aprovar somente a branch; rejeitada porque a
  branch é derivada do slug e a aprovação precisa ser inequívoca.

### Decisão: normalizar slugs inválidos e pedir aprovação da versão normalizada

- **Rationale**: mantém um padrão previsível (`feature/<slug>` em minúsculas e
  com hífens) sem substituir silenciosamente a decisão do usuário.
- **Alternativas consideradas**: normalizar e prosseguir automaticamente;
  rejeitada porque viola o gate de aprovação explícita.

### Decisão: implementar a regra nas instruções do subagente

- **Rationale**: o comportamento é processual e já é governado pelo arquivo do
  coordenador de revisão de literatura; não exige código executável.
- **Alternativas consideradas**: criar um validador ou estado persistente;
  rejeitada por adicionar complexidade sem necessidade para a primeira versão.

### Decisão: manter a política de branches existente

- **Rationale**: `main` e `develop` continuam protegidas e toda alteração parte
  de uma branch `feature/*` criada a partir de `develop`.
- **Alternativas consideradas**: permitir alterações diretas quando o usuário
  recusasse uma branch; rejeitada por conflitar com a governança do projeto.
