# Feature Specification: Validar Metadados Técnicos de Vídeo

**Feature Branch**: `feature/validar-metadados-video`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "Validar os metadados técnicos contra o vídeo real, comparar width, height e fps do CSV com os valores observados nos vídeos, descobrir se a coluna fps representa taxa de quadros ou quantidade de frames e exibir o resultado no notebook antes da validação da convenção do nome do arquivo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conferir os metadados reais dos vídeos (Priority: P1)

Como pesquisador do dataset, quero comparar os metadados registrados no CSV
com as propriedades reais dos vídeos, para identificar registros incorretos,
incompletos ou incompatíveis antes de usar o dataset.

**Why this priority**: A resolução, a taxa temporal, a duração e o codec
afetam diretamente a interpretação e o preparo dos vídeos de Libras. Sem essa
conferência, o dataset pode parecer consistente apenas por causa dos valores do
CSV.

**Independent Test**: Executar a validação em um pequeno conjunto de vídeos de
teste e verificar uma linha de resultado por vídeo, com os valores do CSV, os
valores observados e um status para cada comparação.

**Acceptance Scenarios**:

1. **Given** um vídeo válido e uma linha correspondente no CSV, **When** a
   validação é executada, **Then** o resultado registra largura, altura, taxa
   de quadros, quantidade de frames, duração e codec observados no arquivo.
2. **Given** um vídeo cujo tamanho ou taxa temporal difere do CSV, **When** a
   validação é executada, **Then** a divergência aparece no detalhe e no
   resumo, sem alterar o vídeo ou o CSV.
3. **Given** um vídeo para o qual a quantidade de frames não está disponível
   diretamente, **When** a validação é executada, **Then** o resultado
   diferencia valor ausente de zero e registra que a quantidade não pôde ser
   determinada ou precisou de uma contagem complementar.

---

### User Story 2 - Descobrir o significado da coluna `fps` (Priority: P1)

Como pesquisador, quero testar explicitamente as interpretações possíveis da
coluna `fps`, para não renomeá-la ou usá-la como frames por segundo sem
evidência.

**Why this priority**: Uma interpretação errada dessa coluna pode contaminar a
análise temporal, a amostragem dos vídeos e qualquer experimento posterior.

**Independent Test**: Executar a validação com um CSV de fixture contendo
valores conhecidos e conferir um resumo separado para as hipóteses `fps` como
taxa de quadros, `fps` como quantidade de frames e nenhuma correspondência.

**Acceptance Scenarios**:

1. **Given** um valor CSV que coincide com a taxa de quadros observada,
   **When** as hipóteses são avaliadas, **Then** a hipótese de taxa de quadros
   é marcada como correspondente.
2. **Given** um valor CSV que coincide com a quantidade de frames observada,
   **When** as hipóteses são avaliadas, **Then** a hipótese de quantidade de
   frames é marcada como correspondente.
3. **Given** um valor CSV que não coincide com nenhuma observação confiável,
   **When** as hipóteses são avaliadas, **Then** o resultado é marcado como
   divergente ou inconclusivo, conforme a disponibilidade dos dados, sem
   modificar o nome original da coluna.

---

### User Story 3 - Visualizar a validação no inventário do dataset (Priority: P2)

Como pesquisador, quero ver os resultados no notebook de inventário, para
interpretar a qualidade do dataset em sequência com as demais verificações.

**Why this priority**: O notebook é o ponto de inspeção exploratória do
V-Librasil. Integrar a nova análise nele torna a descoberta auditável e evita
que o resultado fique apenas em arquivos de execução difíceis de consultar.

**Independent Test**: Executar o notebook com um dataset de teste e verificar
que a seção de metadados técnicos aparece depois da reconciliação CSV ×
filesystem e antes de `Validação da convenção do nome do arquivo`.

**Acceptance Scenarios**:

1. **Given** resultados estruturados de uma execução de validação, **When** o
   notebook é executado, **Then** ele exibe detalhes por vídeo e resumos de
   largura, altura, taxa temporal, frames, duração, codec e hipóteses de `fps`.
2. **Given** uma falha de inspeção em um vídeo, **When** o notebook é
   executado, **Then** a falha aparece na tabela e as outras entradas continuam
   visíveis.
3. **Given** a seção existente de convenção de nomes, **When** o notebook é
   revisado, **Then** a validação técnica fica imediatamente antes dela e as
   duas análises permanecem conceitualmente separadas.

### User Story 4 - Auditar proveniência e produzir decisão de uso (Priority: P1)

Como pesquisador, quero validar `error.csv` e receber uma decisão GO/NO-GO
com evidências e um manifest derivado, para não confundir uma exceção
documentada com perda silenciosa de dados.

**Independent Test**: Executar a etapa após a convenção de nomes em fixtures
com exceções conhecidas, exceções sobrepostas, arquivos ausentes e arquivos
físicos sem registro; conferir a classificação, o relatório, o resumo e o
Parquet sem alteração dos arquivos brutos.

**Acceptance Scenarios**:

1. **Given** um item em `error.csv`, **When** a proveniência é validada,
   **Then** o resultado informa se ele aparece em `annotations.csv`, se possui
   arquivo físico e se o motivo é consistente com o estado observado.
2. **Given** um registro de `annotations.csv` sem vídeo e sem item equivalente
   em `error.csv`, **When** a validação é executada, **Then** ele é classificado
   como perda silenciosa `ERROR`, não como exceção conhecida.
3. **Given** problemas de severidades distintas, **When** a execução termina,
   **Then** `metadata_validation_report.md`, `metadata_issues.csv`,
   `metadata_summary.json` e o manifest Parquet são produzidos, com decisão
   `GO` somente quando não há `CRITICAL` ou `ERROR`.

### Edge Cases

- O CSV não possui uma das colunas esperadas ou possui valores vazios,
  negativos ou não numéricos.
- O `video_name` do CSV não corresponde a um arquivo físico ou há um arquivo
  físico sem registro no CSV.
- O arquivo existe, mas está vazio, corrompido, sem stream de vídeo ou usa um
  contêiner que não pode ser inspecionado.
- O vídeo possui taxa variável, múltiplas streams ou valores diferentes para
  taxa nominal e taxa média.
- O contêiner não informa `nb_frames`; o resultado deve registrar a ausência
  ou uma contagem complementar de forma explícita.
- O conjunto contém vídeos válidos e inválidos ao mesmo tempo; uma falha por
  arquivo não deve ocultar os resultados dos demais.
- O Docker, a ferramenta de inspeção ou um pré-requisito local não está
  disponível; a execução deve falhar de modo acionável, sem relatar sucesso.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST ler os registros de vídeo e os campos `width`,
  `height` e `fps` do CSV sem modificar o arquivo original.
- **FR-002**: O sistema MUST obter do próprio vídeo, quando disponível,
  `actual_width`, `actual_height`, `actual_fps`, `actual_frame_count`,
  `actual_duration_seconds` e `codec`.
- **FR-003**: O sistema MUST distinguir valor zero, valor ausente, valor não
  determinado e erro de inspeção nos resultados.
- **FR-004**: O sistema MUST comparar `csv.width` com `actual_width` e
  `csv.height` com `actual_height`, registrando status por campo e por vídeo.
- **FR-005**: O sistema MUST avaliar separadamente se `csv.fps` corresponde a
  `actual_fps`, a `actual_frame_count` ou a nenhum dos dois.
- **FR-006**: O sistema MUST preservar o nome e o valor original da coluna
  `fps` e MUST NOT renomeá-la ou reinterpretá-la silenciosamente.
- **FR-007**: O sistema MUST produzir detalhes por vídeo, um resumo agregado,
  um registro da ferramenta e dos parâmetros usados e falhas identificadas.
- **FR-008**: O sistema MUST manter vídeos e CSVs em `data/raw/` intactos e
  gravar resultados derivados somente sob `data/processed/`.
- **FR-009**: O notebook de inventário MUST exibir a validação técnica depois
  da validação CSV × filesystem e antes da seção `Validação da convenção do
  nome do arquivo`.
- **FR-010**: O notebook MUST consumir os resultados da validação reutilizável,
  sem duplicar a lógica de inspeção ou comparação.
- **FR-011**: A validação MUST continuar processando entradas independentes
  quando uma entrada falhar e MUST registrar a falha correspondente.
- **FR-012**: O projeto MUST fornecer testes determinísticos com fixtures
  pequenos, sem exigir download, credenciais, corpus bruto ou rede por padrão.
- **FR-013**: A documentação MUST explicar como executar a validação, ler os
  status e interpretar as três hipóteses para `fps`.
- **FR-014**: Para o V-LIBRASIL, o sistema MUST tratar `error.csv` como fonte
  obrigatória de proveniência e MUST verificar sobreposição com
  `annotations.csv`, presença em `videos/`, consistência do motivo e ausências
  não registradas.
- **FR-015**: O sistema MUST classificar problemas como `CRITICAL`, `ERROR`,
  `WARNING` ou `INFO` e MUST recordar a evidência da classificação por item.
- **FR-016**: O sistema MUST produzir `reports/metadata_validation_report.md`,
  `reports/metadata_issues.csv` e `reports/metadata_summary.json` sob a área
  derivada, além de manifests Parquet validados para V-LIBRASIL e MINDS-Libras.
- **FR-017**: O manifest validado MUST ser derivado, preservar os campos
  originais quando disponíveis e poder acrescentar metadados observados,
  flags de existência/leitura, validade do nome, validade técnica, status e
  notas de validação, sem alterar `data/raw/`.
- **FR-018**: A decisão MUST ser `NO-GO` quando houver pelo menos um problema
  `CRITICAL` ou `ERROR`, mesmo que cada artefato de evidência seja
  gravados.

### Key Entities

- **Registro CSV de vídeo**: linha de `annotations.csv` ou arquivo de exceções,
  contendo o nome do vídeo e os valores declarados pelo dataset.
- **Metadados observados do vídeo**: propriedades lidas do arquivo físico,
  incluindo dimensões, taxa temporal, frames, duração e codec.
- **Resultado de comparação**: associação entre um registro CSV e um vídeo,
  com valores esperados, valores observados, status, hipótese de `fps` e erro,
  quando houver.
- **Resumo de validação**: contagens agregadas por status, hipótese, dataset e
  tipo de falha.
- **Execução da ferramenta**: registro do momento, parâmetros, versões,
  entradas, saídas e status da execução.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para cada arquivo de vídeo processado, existe exatamente um
  resultado de detalhe ou um erro explícito associado ao arquivo.
- **SC-002**: Em fixtures determinísticos, 100% das divergências conhecidas de
  largura, altura e `fps` são classificadas conforme a hipótese correspondente.
- **SC-003**: Uma falha em um arquivo não impede que os demais arquivos do lote
  tenham seus resultados registrados.
- **SC-004**: O notebook apresenta a seção de metadados técnicos na posição
  definida e permite consultar os detalhes e os resumos sem editar o corpus.
- **SC-005**: A execução padrão de testes termina sem rede, credenciais ou
  alteração dos arquivos em `data/raw/`.
- **SC-006**: Um colaborador consegue executar a validação e interpretar os
  status consultando o quickstart em uma única sequência documentada.
- **SC-007**: Fixtures com ausência silenciosa, exceção conhecida, exceção
  inconsistente e arquivo não registrado são diferenciadas com 100% de
  classificação determinística.
- **SC-008**: Cada execução de qualidade produz os três artefatos de relatório
  e o manifest Parquet sem modificar qualquer arquivo em `data/raw/`.

## Assumptions

- A primeira versão trata a validação como inspeção e diagnóstico; ela não
  converte, normaliza, renomeia ou exclui vídeos.
- `annotations.csv` é a fonte principal dos valores declarados e `error.csv`
  continua representando exceções explícitas do dataset.
- O nome do vídeo continua sendo a chave de ligação entre o CSV e o arquivo
  físico, enquanto a convenção `class_user_id.mp4` é validada em uma etapa
  separada.
- Quando houver taxa nominal e média disponíveis, ambas podem ser preservadas
  para auditoria, mas o resultado precisa declarar qual foi usado na hipótese
  principal de comparação.
- A execução em lote pode usar o Docker de processamento audiovisual já
  existente, com entrada bruta somente para leitura e saída derivada separada.
- `error.csv` pode não possuir uma coluna textual de motivo; quando isso ocorre,
  a implementação registra a inferência baseada nos campos técnicos zerados e
  na existência/legibilidade do vídeo, sem inventar um motivo textual.
