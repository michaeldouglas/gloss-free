# Quickstart de Validação: Padronizar Aprovação de Slug

## Pré-requisitos

- Estar na branch `feature/padronizar-aprovacao-slug`.
- Ter o Spec Kit instalado e `specify check` aprovado.
- Ter o arquivo `.codex/agents/literature-review-coordinator.md` disponível.

## Cenário 1 — sugestão antes da alteração

1. Abra `.codex/agents/literature-review-coordinator.md`.
2. Confirme que a seção de aprovação obriga o subagente a:
   - analisar a alteração;
   - sugerir `feature/<slug>`;
   - pedir aprovação explícita;
   - aguardar a resposta antes de criar a branch ou alterar arquivos.
3. Resultado esperado: todos os quatro comportamentos estão descritos de
   forma operacional.

## Cenário 2 — rejeição e nova proposta

1. Simule uma solicitação de alteração sem aprovar o slug sugerido.
2. Responda com uma rejeição ou com um slug alternativo.
3. Verifique que as instruções exigem uma nova proposta/confirmação e proíbem
   alterações enquanto não houver aprovação.
4. Resultado esperado: somente o slug explicitamente aprovado pode ser usado.

## Cenário 3 — integridade dos artefatos

Execute na raiz do repositório:

```powershell
specify check
specify integration status
git diff --check
Get-Content .specify/feature.json
```

Resultados esperados:

- `specify check` indica que a CLI está pronta.
- A integração Codex permanece `OK`, sem arquivos gerenciados ausentes ou
  modificados.
- `git diff --check` não reporta erros de whitespace.
- `feature.json` aponta para `specs/001-padronizar-aprovacao-slug`.

## Critério de conclusão

A feature está pronta para a etapa de tarefas quando os três cenários acima
passarem e a revisão confirmar que nenhuma regra permite mutação antes da
aprovação explícita do slug.
