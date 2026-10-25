# Contrato científico do showroom

Este contrato se aplica sempre que `core/scripts/build-showroom.ts` gerar páginas em `../docs/`. O showroom é uma apresentação derivada: não cria uma fonte científica concorrente nem substitui os relatórios técnicos.

## Fontes de verdade

- O tema e o foco geral da dissertação devem seguir o `README.md` da raiz do repositório e os artefatos vigentes em `specs/`.
- O propósito e o escopo da etapa de validação devem seguir a especificação ativa em `specs/003-validar-metadados-video/spec.md`.
- Os resultados da execução atual vêm de `artifacts/reports/latest.json` e `artifacts/reports/latest.md`.
- Os resultados técnicos por dataset vêm de `../app/data/processed/metadata-validation/<dataset>/reports/metadata_summary.json`.
- A página pública é gerada em `../docs/`; seus textos e números não são fonte autoritativa.

## Conteúdo obrigatório

- A página inicial relaciona a pesquisa de tradução de Libras para português escrito sem glosas à etapa que está sendo executada.
- A página inicial aponta para as evidências por dataset e para o relatório detalhado mais recente.
- O relatório detalhado identifica o dataset e a decisão da execução, apresenta os resultados e mantém acesso ao texto original e às auditorias.
- A interpretação esclarece que `GO` e `NO-GO` desta etapa tratam de integridade e proveniência dos dados. Esses estados não medem qualidade linguística, qualidade de tradução nem desempenho de modelos.
- Cada achado específico, contagem, decisão e data é renderizado a partir do report ou resumo técnico correspondente; não se mantém uma cópia manual desses valores no texto da página.

## Revisão de afirmações

Não acrescente métodos, métricas, resultados experimentais ou conclusões que não estejam sustentados por uma fonte vigente do projeto. Diferencie trabalho realizado de objetivo futuro. Quando uma nova interpretação científica for necessária, coordene a análise usando `.codex/agents/scientific-data-analysis-coordinator.md` e a skill correspondente à etapa. Use o especialista de vídeo apenas para conclusões que dependam de evidência audiovisual e o coordenador de literatura apenas para afirmações que dependam de literatura. A renderização rotineira de resultados existentes não exige executar esses agentes.

O build verifica automaticamente os campos narrativos obrigatórios, os resultados da execução e os caminhos para as evidências. Os testes do harness protegem o contrato contra regressões.

## Apresentação visual

O showroom é uma superfície de leitura científica. Melhorias visuais podem reorganizar hierarquia, tipografia, espaçamento, contraste e navegação para facilitar a compreensão, mantendo as afirmações, métricas, decisões e relações entre evidências intactas. As regras de seleção e revisão das skills de interface estão em `AGENTS.md`; elas se aplicam a mudanças visuais, não à regeneração rotineira dos dados. Altere os templates e estilos em `core/` e gere novamente `../docs/`, que permanece saída derivada.
