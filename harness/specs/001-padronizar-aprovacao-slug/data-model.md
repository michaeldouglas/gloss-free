# Modelo de Dados: Padronizar Aprovação de Slug

Esta feature não cria entidades persistentes de aplicação. O modelo abaixo
representa o estado conversacional necessário para implementar e validar a
regra do subagente.

## Entidades

### SlugProposal

Representa a sugestão de nome feita pelo subagente para a alteração solicitada.

| Campo | Descrição | Regra |
|---|---|---|
| `requested_change` | Resumo da alteração que será realizada | Deve estar presente antes da sugestão |
| `suggested_slug` | Slug proposto sem o prefixo de branch | Minúsculo, descritivo e separado por hífens |
| `branch_name` | Nome completo da branch proposta | Deve seguir `feature/<slug>` |
| `status` | Estado da proposta | `proposed`, `approved`, `rejected` ou `revised` |
| `user_response` | Resposta que confirma ou recusa a proposta | Necessária para transição de estado |

### BranchDecision

Representa a decisão sobre criar ou usar uma branch depois da aprovação do
slug.

| Campo | Descrição | Regra |
|---|---|---|
| `branch_name` | Branch aprovada ou existente | Deve ser uma `feature/*` |
| `base_branch` | Branch de origem | Nova branch deve partir de `develop` |
| `action` | Ação autorizada | `create` ou `use-existing` |
| `slug_approved` | Evidência da aprovação | Deve ser verdadeiro antes da ação |

## Transições

```text
proposed ── aprovação explícita ──> approved ──> create/use-existing branch
    │
    ├── rejeição ──> rejected ──> revised ──> proposed
    └── resposta ambígua ──> proposed (aguardar confirmação)
```

Nenhuma transição para criação de branch ou alteração de arquivo é permitida
a partir de `rejected` ou de uma proposta sem confirmação explícita.
