# Feature Specification: Etapa 2 — Caracterização estatística e análise exploratória dos datasets

**Feature Branch**: `feature/etapa2-contratos-eda`

**Created**: 2026-11-05

**Status**: Draft

**Input**: Formalização da Etapa 2 a partir dos manifests validados da Etapa 1.

## Objetivo e escopo científico

Caracterizar estatisticamente e explorar de forma reprodutível os datasets
V-LIBRASIL e MINDS-Libras a partir dos manifests validados da Etapa 1,
identificando suas distribuições, estrutura de classes e sinalizadores,
propriedades técnicas, heterogeneidades e possíveis observações atípicas, sem
modificar os dados originais nem antecipar decisões de modelagem.

A Etapa 1 — Metadata Validation é uma pré-condição concluída para esta
especificação: `global_stage1_decision = GO`, `stage1_status = completed`,
V-LIBRASIL = `GO` e MINDS-Libras = `GO`. Os artefatos de fechamento da Etapa 1
são fontes de proveniência e controle, não uma nova fonte analítica.

Esta especificação define o que a Etapa 2 deve responder. Ela não autoriza sua
execução durante a formalização deste documento.

## Unidade observacional e dependência

`1 linha = 1 vídeo validado`.

- O vídeo é a unidade observacional principal.
- `class` é um fator categórico do sinal.
- `user_id` é um fator categórico do sinalizador/articulador.
- `class` e `user_id` são fatores cruzados quando aplicável; nenhum deles é
  tratado como uma hierarquia estritamente aninhada.
- Frames são medidas internas do vídeo, não observações independentes.

Tratar frames como observações independentes inflaria artificialmente o número
de unidades e a precisão aparente. Vídeos do mesmo `user_id` também podem
compartilhar características do sinalizador, da captura e do contexto. A
Etapa 2 deve registrar esse risco de pseudorreplicação e não pode sustentar
inferência que ignore a dependência entre vídeos do mesmo sinalizador ou os
fatores cruzados.

## Pré-condições e fontes

As entradas analíticas são somente os manifests canônicos validados:

- `app/data/processed/metadata-validation/v-librasil-raw/manifests/v_librasil_validated.parquet`
- `app/data/processed/metadata-validation/minds-libras-raw/manifests/minds_libras_validated.parquet`

O contrato normativo completo de chaves, população, exceções, missingness e
saídas está em [contracts/analysis-contract.md](contracts/analysis-contract.md).
Os denominadores de referência são 4.086 vídeos válidos no V-LIBRASIL e 800
vídeos válidos no MINDS-Libras. As três exceções documentadas do V-LIBRASIL
permanecem fora do corpus analítico e devem ser explicitadas, não reincorporadas.

## Cenários de uso e testes

### User Story 1 — Caracterizar as populações validadas (Priority: P1) 🎯 MVP

Como pesquisador, quero uma caracterização descritiva separada dos dois
manifests para saber qual população de vídeos está disponível e quais
denominadores sustentam cada resultado.

**Por que esta prioridade**: toda distribuição, comparação ou interpretação
posterior depende de uma unidade observacional e de denominadores corretos.

**Teste independente**: executar a Parte 1 sobre cópias controladas dos
manifests e verificar tabelas de overview, missingness, estatísticas numéricas,
frequências categóricas e validações de soma sem alterar as entradas.

**Cenários de aceitação**:

1. **Dado** um manifest canônico válido, **quando** a caracterização for
   autorizada, **então** o resultado registrará uma linha por vídeo validado,
   o número de classes, sinalizadores e combinações `class × user_id`, além do
   denominador usado em cada tabela.
2. **Dado** um campo ausente ou estruturalmente não aplicável, **quando** ele
   for resumido, **então** seu estado será preservado segundo o contrato e não
   haverá imputação.

### User Story 2 — Explorar distribuições temporais e técnicas (Priority: P1)

Como pesquisador, quero descrever as distribuições de frames, duração, FPS e
propriedades técnicas para identificar heterogeneidade e extremos sem tratá-los
automaticamente como erros.

**Por que esta prioridade**: duração, quantidade de frames e características de
captura condicionam a interpretação do corpus e as decisões futuras.

**Teste independente**: verificar, em artefatos derivados, tabelas e metadados
de figuras para `actual_frame_count`, `actual_duration`, `actual_fps`,
resolução, proporção de aspecto e codec, mantendo o valor original disponível.

**Cenários de aceitação**:

1. **Dado** um campo técnico aplicável, **quando** sua distribuição for
   resumida, **então** o resultado exibirá forma, dispersão, assimetria quando
   justificada, caudas e valores extremos com o escopo e os missingness
   correspondentes.
2. **Dado** um valor extremo, **quando** ele for sinalizado, **então** o
   registro permanecerá disponível e a sinalização será distinguida de erro,
   exclusão ou correção.

### User Story 3 — Caracterizar classes e sinalizadores (Priority: P1)

Como pesquisador, quero observar a cobertura por classe, por sinalizador e por
combinação cruzada para identificar classes incompletas e diferenças de
participação entre os datasets.

**Teste independente**: verificar frequências absolutas e relativas, matriz
`class × user_id`, cobertura e validação dos denominadores para cada dataset.

**Cenários de aceitação**:

1. **Dado** cada manifest, **quando** as categorias forem resumidas, **então**
   classes, sinalizadores e combinações serão reportados separadamente por
   dataset.
2. **Dado** uma combinação ausente ou uma classe com cobertura desigual,
   **quando** a matriz for publicada, **então** a ausência será visível e não
   será convertida em zero sem semântica documentada.

### User Story 4 — Comparar descritivamente os datasets (Priority: P2)

Como pesquisador, quero comparar V-LIBRASIL e MINDS-Libras preservando suas
identidades para entender semelhanças, diferenças e limites de comparabilidade.

**Teste independente**: verificar uma tabela comparativa que mantenha `dataset`
como agrupamento e cubra tamanho, vocabulário, sinalizadores, classes
compartilhadas e exclusivas, duração, frames, FPS, resolução e propriedades
técnicas compatíveis.

**Cenários de aceitação**:

1. **Dado** dois manifests com semânticas específicas, **quando** forem
   comparados, **então** somente variáveis compatíveis e unidades iguais serão
   colocadas lado a lado.
2. **Dado** um resultado descritivo entre datasets, **quando** ele for
   interpretado, **então** não será apresentado como teste inferencial, efeito
   causal ou evidência de uma população única.

### User Story 5 — Documentar observações atípicas sem exclusão (Priority: P2)

Como pesquisador, quero identificar observações potencialmente atípicas com
critérios documentados para orientar inspeções posteriores sem apagar dados.

**Teste independente**: verificar uma tabela de flags que informe variável,
critério, valor de referência, escopo e observação original, sem alterar o
manifest nem reduzir automaticamente o corpus.

**Cenários de aceitação**:

1. **Dado** um critério IQR, percentil ou específico da variável, **quando** um
   registro for sinalizado, **então** o critério aplicado e sua limitação serão
   registrados.
2. **Dado** um registro sinalizado, **quando** a execução terminar, **então**
   nenhuma remoção, winsorização ou imputação terá ocorrido automaticamente.

### User Story 6 — Produzir uma síntese científica rastreável (Priority: P2)

Como pesquisador, quero uma síntese das evidências, limitações e riscos para
decidir quais perguntas podem ser levadas às próximas etapas sem antecipar
modelagem ou inferência.

**Teste independente**: revisar o relatório final contra as tabelas, figuras,
metadados e manifestos de execução publicados, confirmando que cada conclusão
tem uma origem rastreável e que padrões exploratórios estão identificados como
tais.

**Cenários de aceitação**:

1. **Dado** um conjunto de artefatos derivados, **quando** a síntese for
   produzida, **então** ela cobrirá estrutura, heterogeneidade, cobertura,
   limitações, riscos e implicações futuras sem conclusões causais.
2. **Dado** uma execução repetida com os mesmos inputs e parâmetros, **quando**
   os resultados forem comparados, **então** a identidade de execução e os
   hashes permitirão verificar a reprodutibilidade.

## Requisitos funcionais

- **FR-001**: A Etapa 2 MUST usar os dois manifests canônicos da Etapa 1 como
  fontes analíticas primárias e não MUST usar `data/raw/` como fonte principal.
- **FR-002**: A Etapa 2 MUST tratar uma linha como um vídeo validado e MUST
  manter `dataset` como agrupamento explícito.
- **FR-003**: A Etapa 2 MUST preservar a semântica cruzada de `class` e
  `user_id` e MUST registrar o risco de pseudorreplicação por frames e por
  sinalizador.
- **FR-004**: A Etapa 2 MUST produzir uma caracterização geral separada para
  cada dataset, incluindo vídeos, classes, sinalizadores, combinações e
  frequências básicas.
- **FR-005**: A Etapa 2 MUST produzir estatísticas descritivas fundamentais
  para variáveis numéricas quando aplicáveis: `n`, missingness aplicável,
  média, mediana, desvio-padrão, mínimo, Q1, Q3, máximo e IQR.
- **FR-006**: A Etapa 2 MUST produzir frequências absolutas, relativas e número
  de categorias para variáveis categóricas relevantes.
- **FR-007**: A Etapa 2 MUST explorar `actual_frame_count`, `actual_duration` e
  `actual_fps`, incluindo forma, dispersão, assimetria quando aplicável, caudas
  e valores extremos.
- **FR-008**: A Etapa 2 MUST caracterizar resolução, proporção de aspecto, FPS
  real, codec e demais características técnicas disponíveis nos manifests.
- **FR-009**: A Etapa 2 MUST caracterizar vídeos por classe, por sinalizador e
  pela matriz `class × user_id`, incluindo cobertura, classes incompletas e
  diferenças de participação.
- **FR-010**: A Etapa 2 MUST comparar descritivamente tamanho, vocabulário,
  sinalizadores, classes compartilhadas e exclusivas, duração, frames, FPS,
  resolução e propriedades técnicas compatíveis.
- **FR-011**: A Etapa 2 MUST manter V-LIBRASIL e MINDS-Libras como datasets
  separados e MUST NOT tratá-los automaticamente como uma única população.
- **FR-012**: A Etapa 2 MUST identificar possíveis observações atípicas com
  critérios documentados e MUST NOT remover, corrigir ou winsorizar
  automaticamente qualquer registro.
- **FR-013**: A Etapa 2 MUST preservar `missing_real`, `structural_absence`,
  `not_applicable`, `failure_of_measurement` e `zero_true`, sem imputação.
- **FR-014**: A Etapa 2 MUST registrar denominadores explícitos, população
  coberta, exceções fora do corpus e o escopo de cada tabela, figura e síntese.
- **FR-015**: A Etapa 2 MUST registrar SHA-256, schema, número de linhas,
  timestamp, commit, `run_id`, parâmetros, versões das bibliotecas, outputs e
  validações de cada execução.
- **FR-016**: A Etapa 2 MUST publicar somente artefatos derivados em
  `app/data/processed/eda/`, preservando execuções anteriores e evitando
  sobrescrita silenciosa.
- **FR-017**: A Etapa 2 MUST NOT executar novamente `ffprobe` para construir a
  EDA.
- **FR-018**: A Etapa 2 MUST NOT executar testes inferenciais, treinamento,
  fine-tuning, feature learning, criação de splits ou balanceamento como parte
  desta entrega.
- **FR-019**: A Etapa 2 MUST produzir síntese científica sustentada por
  evidências, identificar padrões pós-hoc como exploratórios e registrar
  limitações sem alegações linguísticas, causais ou inferenciais não planejadas.

## Fora do escopo

Esta feature não inclui:

- treinamento, fine-tuning ou feature learning;
- criação de splits, balanceamento, oversampling ou undersampling;
- remoção automática de outliers;
- imputação;
- transformação automática de distribuições;
- testes inferenciais sem hipótese previamente definida;
- comparação de desempenho de modelos;
- alteração, renomeação, substituição ou remoção em `data/raw/`;
- reexecução de `ffprobe`;
- decisão implícita de modelagem.

## Casos-limite e riscos

- Um manifest ausente, com schema incompatível, população incorreta ou chave
  duplicada deve bloquear a análise e produzir uma falha explicável.
- `filename_valid = null` no MINDS-Libras representa ausência estrutural por
  desenho, não dado ausente e não problema de qualidade.
- As três exceções do V-LIBRASIL permanecem documentadas fora do corpus válido;
  todo relatório deve declarar se o denominador é o corpus analítico ou a
  população de origem.
- Medição técnica nula representa falha de medição, não zero verdadeiro.
- Diferenças de vocabulário, cobertura ou participação podem refletir desenho
  de corpus e não devem ser tratadas como viés ou causalidade sem investigação.
- Frames e vídeos do mesmo sinalizador não devem ser contados como réplicas
  independentes.
- Critérios de outlier podem sinalizar captura legítima, cauda natural ou erro;
  flag não é decisão de exclusão.

## Entidades analíticas

- **Manifest validado**: uma população derivada da Etapa 1, com uma linha por
  vídeo e campos de identidade, qualidade, medidas técnicas e proveniência.
- **Vídeo validado**: unidade observacional com `filesystem_key`, `class`,
  `user_id` e medidas internas de frames, duração e captura.
- **Fator cruzado**: relação entre `class` e `user_id`, sem pressupor desenho
  aninhado.
- **Resumo descritivo**: tabela ou figura com denominador, missingness,
  parâmetros, escopo e origem identificáveis.
- **Flag de observação atípica**: indicação não destrutiva de possível extremo,
  sempre acompanhada do critério e da variável.
- **Execução analítica**: conjunto determinístico de inputs, parâmetros,
  versões, artefatos, hashes, validações e decisão de publicação.

## Critérios de sucesso

- **SC-001**: Os dois manifests canônicos são caracterizados separadamente com
  denominadores explícitos e uma linha por vídeo validado.
- **SC-002**: As tabelas numéricas relevantes incluem, quando aplicável, `n`,
  missingness, média, mediana, desvio-padrão, mínimo, Q1, Q3, máximo e IQR.
- **SC-003**: Classes, sinalizadores e combinações `class × user_id` são
  reportados com frequências, proporções e validação dos totais.
- **SC-004**: As distribuições temporais e técnicas são documentadas com
  tabelas antes das figuras e com interpretação limitada ao caráter exploratório.
- **SC-005**: A comparação entre datasets identifica variáveis compatíveis,
  classes compartilhadas e exclusivas, e mantém os datasets separados.
- **SC-006**: Toda observação atípica aparece como flag documentada ou como
  limitação explícita; nenhuma é excluída automaticamente.
- **SC-007**: Cada artefato publicado possui origem, hash, schema, timestamp,
  commit, `run_id`, parâmetros, versões e validações suficientes para auditoria.
- **SC-008**: Uma execução com inputs e parâmetros idênticos pode ser
  reconhecida como a mesma configuração analítica e não altera os manifests.
- **SC-009**: O relatório final apresenta estrutura, heterogeneidade,
  cobertura, limitações, riscos e implicações futuras sem conclusões causais,
  linguísticas ou inferenciais não sustentadas.
- **SC-010**: Nenhum treinamento, split, balanceamento, imputação, exclusão de
  outlier, teste inferencial ou escrita em `data/raw/` ocorre nesta etapa.

## Assumptions

- A decisão canônica de fechamento da Etapa 1 fornecida pelo projeto é a fonte
  de estado atual, enquanto os relatórios históricos permanecem imutáveis.
- Os manifests Parquet validados são suficientes para a caracterização; a EDA
  não precisa acessar os vídeos físicos nem reexecutar `ffprobe`.
- As bibliotecas já presentes no ambiente do aplicativo são suficientes para a
  primeira fase descritiva; dependências inferenciais adicionais não serão
  instaladas nesta feature.
- O notebook 02 é uma camada de execução, inspeção, visualização e
  interpretação; a lógica reutilizável permanece no pacote de análise.
- Critérios e interpretações descobertos durante a EDA serão marcados como
  exploratórios e não serão convertidos automaticamente em hipóteses
  confirmatórias.
