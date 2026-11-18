# Etapa 2 — saneamento documental e proveniência

**Tipo:** `documentation/provenance closeout`
**Run analítico canônico:** `20261107T190651Z-bacdbe5`
**Decisão técnica publicada:** `COMPLETE WITH NOTES`
**stage2_status:** `completed`
**stage2_decision:** `COMPLETE WITH NOTES`
**canonical_run_id:** `20261107T190651Z-bacdbe5`
**Data do closeout:** `2026-11-17`
**human_review_status:** `approved`

Este fechamento reconcilia documentação e proveniência dos resultados já
publicados. Não recalcula estatísticas, não executa EDA, notebook, testes ou
`ffprobe`, não gera gráficos e não altera manifests nem `data/raw/`. O run
analítico continua sendo `20261107T190651Z-bacdbe5`.

Os relatórios e o mapa de evidências anteriores foram preservados, com hashes,
em `app/data/processed/eda/archive/20261107T190651Z-bacdbe5/provenance/documentation-closeout-2026-11-17/originals/`.
Os arquivos sob `app/data/processed/eda/` são projeções locais ignoradas pelo
Git. Este documento rastreado é a referência versionada do saneamento e contém
os achados e limites necessários à revisão.

## Estado das partes após saneamento

| Parte | Estado anterior à auditoria documental | Estado após saneamento | Evidência principal |
|---|---|---|---|
| 1 | COMPLETE WITH NOTES | COMPLETE WITH NOTES | overview, cobertura, fechamento histórico Stage 1 e síntese |
| 2 | COMPLETE WITH NOTES | COMPLETE WITH NOTES | tabelas temporais, figuras e relatório corrigido |
| 3 | PARTIAL | COMPLETE WITH NOTES | tabelas de classes/sinalizadores, cobertura e heatmap |
| 4 | PARTIAL | COMPLETE WITH NOTES | tabelas técnicas e seção de limites de aquisição |
| 5 | PARTIAL | COMPLETE WITH NOTES | comparação numérica/classes e estrutura de sinalizadores |
| 6 | COMPLETE WITH NOTES | COMPLETE WITH NOTES | flags, candidatos e regra sem remoção |
| 7 | PARTIAL | COMPLETE WITH NOTES | síntese e evidence map para sete partes; revisão humana aprovada |

## Parte 1 — Caracterização geral

O overview e o relatório canônicos registram 4.086 vídeos e 1.364 classes
observadas no V-LIBRASIL, e 800 vídeos no MINDS-Libras. O dataset card do
V-LIBRASIL declara 1.366 classes; a diferença declarada × observada é 2. Esse
valor declarado é preservado como referência do card, não recalculado nesta
tarefa. A cópia local do card consultada é
`app/data/raw/v-librasil-raw/README.md` (SHA-256
`a95509e1e709353d1c8fcd18bcecda1df9afba99074770278e3c923e1400583f`).

As tabelas `class_coverage.csv` e `class_signer_counts.csv` registram seis
classes com dois sinalizadores e seis combinações `class × user_id` ausentes:

| Classe × sinalizador ausente | Evidência histórica / classificação |
|---|---|
| `Congelar × Articulador3` | Entrada documentada em `error.csv`; fora do manifest válido. |
| `Criança × Articulador3` | Entrada documentada em `error.csv`; fora do manifest válido. |
| `Poesia × Articulador2` | Entrada documentada em `error.csv`; fora do manifest válido. |
| `Através × Articulador2` | Característica de cobertura; sem causa documentada. |
| `Solicitar × Articulador2` | Característica de cobertura; sem causa documentada. |
| `Terça-feira × Articulador2` | Característica de cobertura; sem causa documentada. |

Para as três últimas combinações, a classificação histórica disponível não
aponta evidência de erro de validação, perda de arquivo, colisão ou falha de
reconciliação. Isso descreve o estado da evidência consultada e não atribui uma
causa. O relatório arquivado da Etapa 1 documenta as três entradas de
`error.csv` fora do corpus válido (SHA-256: `87434173f604ed97f4ea56e3d9e148594cd055f209c3a0a1c03346c59da9d0d7`) e registra zero ausências, extras e duplicatas na reconciliação CSV × filesystem.

No MINDS-Libras, a cobertura é completa: `20 × 8 × 5 = 800`, com 160
combinações `class × user_id` observadas.

**Estado:** `COMPLETE WITH NOTES`. A nota restante é a distinção entre o card
declarado e o corpus observado, preservada acima e sem alteração da população.

## Parte 2 — Distribuições temporais

As tabelas `temporal_distribution_statistics.csv`, `temporal_percentiles.csv`
e `temporal_extreme_candidates.csv`, os metadados e as figuras publicadas
cobrem `actual_frame_count`, `actual_duration` e `actual_fps` para cada
dataset. Incluem centro, dispersão, MAD, assimetria descritiva quando
calculável, percentis, candidatos IQR, histogramas, boxplots e ECDF. As
observações e os valores originais foram preservados; nenhuma exclusão ou
imputação foi aplicada.

**Decisão da Parte 2:** `COMPLETE WITH NOTES`. A interpretação de flags
continua exploratória e não é diagnóstico de erro.

## Parte 3 — Classes e sinalizadores

`class_counts.csv`, `signer_counts.csv`, `class_signer_counts.csv`,
`class_coverage.csv` e `signer_coverage.csv`, acompanhados pelas figuras de
frequência de classes, cobertura de sinalizadores e heatmap `class × user_id`,
documentam a estrutura dos datasets separadamente. O V-LIBRASIL tem 1.364
classes observadas; seis têm cobertura de dois dos três sinalizadores, com as
ausências discriminadas na Parte 1. O MINDS-Libras tem 20 classes, oito
sinalizadores e cinco vídeos em cada uma das 160 combinações, totalizando 800.

As tabelas preservam os denominadores próprios. A cobertura não é interpretada
como um alvo de balanceamento, nem como critério de exclusão.

**Estado:** `COMPLETE WITH NOTES`.

## Parte 4 — Propriedades técnicas

`technical_distribution_statistics.csv` e `technical_frequency_tables.csv`
documentam dimensões, resolução, proporção de aspecto, `actual_fps` e codec.
As tabelas e figuras técnicas mantêm resultados separados por dataset. Os
artefatos mostram três resoluções e seis valores distintos de `actual_fps` no
V-LIBRASIL, versus uma resolução e 172 valores distintos de `actual_fps` no
MINDS-Libras; ambos registram codec H.264 em suas tabelas de frequência.

### Diferenças de aquisição

Os perfis observados diferem em resolução e na distribuição dos valores de
`actual_fps`, enquanto as tabelas de codec registram H.264 nos dois datasets.
Isso permite descrever heterogeneidade técnica entre os corpora. Os artefatos
não identificam equipamento, local, configuração de gravação ou causa dessas
diferenças; nenhuma dessas causas é inferida neste fechamento.

**Estado:** `COMPLETE WITH NOTES`.

## Parte 5 — Comparação entre datasets

`comparison_numeric.csv` e `comparison_classes.csv` sustentam comparações
descritivas de tamanho, variáveis temporais/técnicas e classes compartilhadas
ou exclusivas. `dataset` e denominadores são preservados; os datasets não são
tratados como uma população única.

As tabelas existentes de participação registram:

| Dataset | `user_id` distintos | Cobertura por `user_id` já publicada |
|---|---:|---|
| V-LIBRASIL | 3 | Articulador1: 1.364 vídeos/1.364 classes; Articulador2: 1.360/1.360; Articulador3: 1.362/1.362. |
| MINDS-Libras | 8 | Cada sinalizador: 100 vídeos/20 classes; cada combinação classe × sinalizador contém cinco vídeos. |

Essa comparação descreve desenho e repetição: o V-LIBRASIL tem um vídeo por
combinação observada e seis combinações ausentes; o MINDS-Libras tem cinco
vídeos em cada combinação completa. `Articulador*` e `Sinalizador*` são
identificadores internos a datasets distintos e não são equiparados como as
mesmas pessoas.

**Estado:** `COMPLETE WITH NOTES`.

## Parte 6 — Observações atípicas

`outlier_flags.csv` e `temporal_extreme_candidates.csv` registram variável,
valor, critério, flag e ação recomendada para inspeção. A síntese e o relatório
temporal limitam a interpretação: extremo estatístico não significa erro de
dado. Os registros foram preservados; não houve remoção, winsorização ou
imputação automática.

**Estado:** `COMPLETE WITH NOTES`; inspeção humana audiovisual/de dados não é
declarada como concluída por esta EDA.

## Parte 7 — Síntese científica

O relatório `app/data/processed/eda/reports/stage2_synthesis.md` agora reúne
achados e evidências das Partes 1–6, limitações de documentação e cobertura,
riscos e implicações para etapas futuras. O mapa de evidências cobre as sete
partes. A síntese não inicia modelagem e não emite decisão global de
encerramento.

**Estado documental:** `COMPLETE WITH NOTES`. **human_review_status:** `approved`.
A revisão humana foi aprovada em 2026-11-17.

## Limitações e implicações

- A contagem declarada no card e a contagem observada no manifest descrevem
  bases distintas; não se deve substituir uma pela outra.
- As seis lacunas do V-LIBRASIL têm classificações históricas distintas. Para
  três delas há registro em `error.csv`; para as demais não há causa
  documentada.
- Os datasets diferem em cobertura, número de sinalizadores e perfil técnico.
  Dependência entre vídeos do mesmo sinalizador deve ser considerada em
  qualquer etapa futura.
- As tabelas são descritivas. Não sustentam inferência causal, qualidade
  linguística, desempenho de modelos, prontidão para treinamento ou
  equivalência entre corpora.
- Etapas futuras podem definir requisitos de modelagem e avaliação com revisão
  metodológica própria. Esta síntese não prescreve modelo, split ou
  balanceamento.

## Proveniência e revisão

- Execução analítica canônica: `20261107T190651Z-bacdbe5`.
- Decisão técnica do pacote: `COMPLETE WITH NOTES`.
- `human_review_status = approved` em 2026-11-17.
- A documentação atual é um `documentation/provenance closeout`; não é novo run
  estatístico.
- `Dataset Readiness Report = FUTURE WORK — NOT IMPLEMENTED`.
- Stage 2 está `completed` com decisão `COMPLETE WITH NOTES`.

## Evidence map

| Parte | Finding | Dataset | Source artifact | Evidence type | Interpretation limit |
|---|---|---|---|---|---|
| 1 | Tamanho, classes observadas/declaradas e cobertura incompleta | V-LIBRASIL | `tables/dataset_overview.csv`; `tables/class_coverage.csv`; `tables/class_signer_counts.csv`; relatório histórico da Etapa 1; dataset card local | tabela + relatório de proveniência | Card declara classes; manifest conta classes observadas; diferença não é erro automaticamente. |
| 1 | Cobertura completa 20 × 8 × 5 | MINDS-Libras | `tables/dataset_overview.csv`; `tables/class_signer_counts.csv`; `tables/class_coverage.csv` | tabela | Resultado descritivo da cobertura publicada. |
| 2 | Distribuições, percentis, dispersão, assimetria e caudas | Ambos, separados | `tables/temporal_distribution_statistics.csv`; `tables/temporal_percentiles.csv`; `reports/temporal_distributions.md` | tabela + relatório | Flags não identificam causa ou erro. |
| 3 | Frequências e matriz classe × sinalizador | Ambos, separados | `tables/class_counts.csv`; `tables/signer_counts.csv`; `tables/class_signer_counts.csv`; `figures/composition/class_signer_heatmap.png` | tabelas + figura | Cobertura não determina balanceamento desejável. |
| 4 | Resolução, aspecto, FPS e codec | Ambos, separados | `tables/technical_distribution_statistics.csv`; `tables/technical_frequency_tables.csv`; `figures/technical/` | tabela + figuras | Sem evidência para inferir equipamento, ambiente ou causa. |
| 5 | Comparação descritiva de tamanho, variáveis e classes | V-LIBRASIL × MINDS-Libras | `tables/comparison_numeric.csv`; `tables/comparison_classes.csv`; `tables/signer_counts.csv`; `tables/signer_coverage.csv` | tabelas | Identidades de sinalizadores são locais; não equiparar indivíduos. |
| 6 | Candidatos extremos preservados para inspeção | Ambos, separados | `tables/outlier_flags.csv`; `tables/temporal_extreme_candidates.csv`; `reports/temporal_distributions.md` | tabela + relatório | Outlier estatístico não é automaticamente erro de dado. |
| 7 | Síntese, limites, riscos e implicações futuras | Ambos, separados | `reports/stage2_synthesis.md`; `tables/evidence_map.csv`; este closeout rastreado | síntese + mapa | Sem inferência ou decisão de modelagem; revisão humana aprovada. |

## Estado final

`Stage 2 completed` — `stage2_status = completed`, decisão `COMPLETE WITH NOTES`, revisão humana aprovada em 2026-11-17.
O run analítico canônico permanece `20261107T190651Z-bacdbe5`.