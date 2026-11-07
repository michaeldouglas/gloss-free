# Tasks: Etapa 2 — Caracterização estatística e análise exploratória dos datasets

**Input**: Design documents from `/specs/004-etapa2-eda/`

**Prerequisites**: `plan.md`, `spec.md` e `contracts/analysis-contract.md`.

**Tests**: Incluídos porque a especificação exige resultados determinísticos,
preservação dos inputs e cobertura automatizada dos contratos. Nenhuma tarefa
abaixo autoriza executar EDA durante esta formalização.

**Organization**: As tarefas seguem a ordem das sete partes analíticas. As
tarefas T001–T006 são preparação estrutural realmente revisada nesta sessão;
elas não significam que a análise dos datasets esteja concluída.

## Phase 1: Setup — preparação estrutural

**Purpose**: Alinhar o estado documental, os contratos e a superfície de
execução antes de qualquer análise.

- [x] T001 Registrar o fechamento canônico da Etapa 1 em `docs/status/0001-status-harness-2026-11-05.md`, com `global_stage1_decision = GO`, `stage1_status = completed`, V-LIBRASIL = GO e MINDS-Libras = GO; resultado: status atual corrigido sem editar relatórios históricos; aceite: o snapshot não afirma mais que a Etapa 1 aguarda revisão.
- [x] T002 Reconciliar `specs/004-etapa2-eda/contracts/analysis-contract.md` com `spec.md` e `plan.md`; resultado: um contrato normativo único para unidade, chaves, população, missingness e outputs; aceite: nenhuma regra duplicada ou conflitante e execução EDA continua explicitamente não autorizada.
- [x] T003 Revisar `app/dataset/src/libras_translation/analysis/data_dictionary.py` e `app/dataset/src/libras_translation/analysis/dataset_profile.py`; resultado: mapeamento documentado dos campos e das chaves físicas por dataset; aceite: 4.086 e 800 são referências de contrato, não contagens calculadas nesta tarefa.
- [x] T004 Revisar `app/dataset/src/libras_translation/analysis/output_contract.py` e `app/data/processed/eda/`; resultado: layout corrente, `archive/<run_id>` e `provenance/CURRENT.json` alinhados ao contrato; aceite: `figures/` permanece vazio até execução autorizada e nenhum output é produzido agora.
- [x] T005 Revisar `app/dataset/tests/test_analysis_contracts.py` e `app/dataset/tests/test_characterization.py`; resultado: lacunas de contrato e de caracterização identificadas para tarefas futuras; aceite: nenhum teste de dataset é executado durante a formalização.
- [x] T006 Revisar `app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb`; resultado: notebook confirmado como camada futura de execução, inspeção, visualização e interpretação; aceite: o notebook permanece sem execução, estatísticas, gráficos, `ffprobe` ou leitura de `data/raw/`.

**Checkpoint**: documentação e contrato alinhados; nenhuma EDA executada.

## Phase 2: Foundational — gates bloqueadores

**Purpose**: Completar os gates que devem bloquear todas as partes analíticas.

- [x] T007 [P] Completar testes de schema, população, unicidade, validade, chaves e preservação de bytes em `app/dataset/tests/test_analysis_contracts.py` (depende de T003; resultado: falhas determinísticas para inputs inválidos; aceite: schema incompatível, população incorreta e chave duplicada bloqueiam a execução sem mutar o frame).
- [x] T008 [P] Consolidar o dicionário analítico e os estados de missingness em `app/dataset/src/libras_translation/analysis/data_dictionary.py` e `specs/004-etapa2-eda/contracts/analysis-contract.md` (depende de T002–T003; resultado: cada campo usado possui unidade, origem, derivação e semântica; aceite: os cinco estados obrigatórios são distinguíveis e nenhum recebe imputação).
- [x] T009 [P] Completar a identidade de input e a proveniência em `app/dataset/src/libras_translation/analysis/dataset_profile.py` (depende de T003; resultado: SHA-256, schema, tamanho, linhas, colunas, commit, timestamp, versões e parâmetros são registráveis; aceite: a mesma entrada e configuração produzem identidade reprodutível).
- [x] T010 Definir o gate de publicação atômica em `app/dataset/src/libras_translation/analysis/output_contract.py` e `app/dataset/tests/test_analysis_contracts.py` (depende de T004 e T009; resultado: execução privada, validação, archive e `CURRENT.json`; aceite: execução anterior nunca é sobrescrita e falha de validação não promove publicação).
- [x] T011 [P] Definir o esquema de tabelas e figuras da etapa em `app/dataset/src/libras_translation/analysis/descriptive_statistics.py`, `app/dataset/src/libras_translation/analysis/distributions.py` e `app/dataset/src/libras_translation/analysis/comparison.py` (depende de T008; resultado: nomes, unidades, denominadores e metadados de saída; aceite: cada figura futura possui tabela correspondente e nenhum campo exige `ffprobe`).
- [x] T012 Executar os gates automatizados da aplicação somente quando a implementação for iniciada, usando `uv run python -m unittest discover -s dataset/tests -v` a partir de `app/` (depende de T007–T011; resultado: baseline de testes registrado; aceite: esta tarefa fica pendente até a fase de implementação e não é executada agora).

**Checkpoint**: inputs, semântica, proveniência, publicação e contratos de
saída prontos para uma execução posterior autorizada.

## Phase 3: User Story 1 — Caracterização geral (Priority: P1) 🎯 MVP

**Goal**: Produzir overview e resumos descritivos separados dos dois manifests,
com denominadores e missingness explícitos.

**Independent Test**: Usar fixtures controladas ou cópias derivadas autorizadas
para verificar overview, estatísticas, frequências, matriz e preservação das
entradas; não usar `data/raw/`.

- [x] T013 [P] [US1] Estender `app/dataset/tests/test_analysis_contracts.py` para validar 4.086 e 800 linhas, uma chave física por vídeo, validade e soma de denominadores (depende de T007; resultado: testes de população; aceite: qualquer divergência bloqueia a publicação).
- [x] T014 [P] [US1] Implementar overview e estatísticas numéricas em `app/dataset/src/libras_translation/analysis/characterization.py` e `app/dataset/src/libras_translation/analysis/descriptive_statistics.py` (depende de T008 e T011; resultado: `n`, missingness, média, mediana, desvio-padrão, mínimo, Q1, Q3, máximo e IQR por variável aplicável; aceite: nenhum valor é imputado e o denominador é gravado).
- [x] T015 [P] [US1] Implementar frequências categóricas e `class × user_id` em `app/dataset/src/libras_translation/analysis/characterization.py` (depende de T014; resultado: tabelas absolutas e relativas por dataset; aceite: somas, categorias ausentes e proporções são verificáveis).
- [x] T016 [US1] Publicar tabelas, relatório e proveniência da Parte 1 em `app/dataset/src/libras_translation/analysis/characterization.py` e `app/data/processed/eda/` (depende de T010, T014 e T015; resultado: execução arquivada e publicação corrente; aceite: inputs permanecem com SHA-256 idêntico e `figures/` não é criado como resultado da Parte 1).
- [x] T017 [US1] Integrar a execução autorizada da Parte 1 em `app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb` (depende de T016; resultado: notebook apenas orquestra e exibe tabelas; aceite: nenhuma lógica científica extensa, `ffprobe` ou acesso a `data/raw/`).

**Checkpoint**: Parte 1 reproduzível e auditável, sem interpretação inferencial.

## Phase 4: User Story 2 — Distribuições temporais (Priority: P1)

**Goal**: Descrever frames, duração e FPS real por dataset.

**Independent Test**: Verificar resumos, quantis, flags e figuras derivadas sem
alterar observações.

- [x] T018 [P] [US2] Criar testes de distribuição e missingness em `app/dataset/tests/test_distributions.py` (depende de T008 e T011; resultado: cobertura para caudas, nulos e valores extremos; aceite: o teste confirma preservação da escala original e ausência de imputação).
- [x] T019 [US2] Implementar resumos de `actual_frame_count`, `actual_duration` e `actual_fps` em `app/dataset/src/libras_translation/analysis/distributions.py` (depende de T014 e T018; resultado: tabelas de forma, dispersão, assimetria quando aplicável, caudas e extremos; aceite: campos são analisados separadamente e por dataset).
- [x] T020 [US2] Implementar metadados e publicação de histogramas, ECDFs e boxplots em `app/dataset/src/libras_translation/analysis/distributions.py` (depende de T019; resultado: figuras com unidades, denominador, tabela de origem, metadados e hashes; aceite: tabelas precedem figuras e a publicação é validada deterministicamente).
- [x] T021 [US2] Integrar tabelas, figuras e interpretação da Parte 2 no notebook `app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb` (depende de T020; resultado: notebook executa a Parte 2 do início ao fim e ordena passo a passo, tabela, figura, candidatos e interpretação; aceite: padrões são rotulados como exploratórios e não há erros de execução).

**Checkpoint**: distribuições temporais executadas no notebook canônico e
publicadas com validação; a revisão humana da Parte 2 ainda está pendente.

## Phase 5: User Story 3 — Classes e sinalizadores (Priority: P1)

**Goal**: Caracterizar cobertura, classes incompletas e participação cruzada.

**Independent Test**: Comparar matriz e frequências contra denominadores e
preservar ausências sem imputação.

- [x] T022 [P] [US3] Estender `app/dataset/tests/test_characterization.py` para cobertura de classes, sinalizadores, combinações e categorias ausentes (depende de T015; resultado: testes de soma, cobertura e semântica de ausência; aceite: zero verdadeiro e ausência estrutural não são confundidos).
- [x] T023 [US3] Implementar cobertura e classes incompletas em `app/dataset/src/libras_translation/analysis/characterization.py` (depende de T022; resultado: tabelas de cobertura por classe e sinalizador; aceite: nenhum limiar de balanceamento ou exclusão é aplicado).
- [x] T024 [US3] Integrar matriz e tabelas acessíveis da Parte 3 em `app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb` (depende de T023; resultado: tabela antecede qualquer heatmap; aceite: `dataset`, denominador e unidade aparecem na interpretação).

**Checkpoint**: estrutura cruzada documentada sem decisão de balanceamento.

## Phase 6: User Story 4 — Propriedades técnicas (Priority: P2)

**Goal**: Descrever resolução, aspecto, FPS, codec e demais campos técnicos.

**Independent Test**: Validar campos e unidades contra o dicionário, sem
reexecutar `ffprobe`.

- [x] T025 [P] [US4] Criar testes técnicos em `app/dataset/tests/test_technical_distributions.py` para dimensões, resolução, aspect ratio, FPS e codec (depende de T008 e T011; resultado: validação de tipos, unidades e missingness; aceite: o manifest não é modificado).
- [x] T026 [US4] Implementar resumos técnicos em `app/dataset/src/libras_translation/analysis/distributions.py` e `app/dataset/src/libras_translation/analysis/data_dictionary.py` (depende de T025; resultado: tabelas de resolução, codec, aspecto e medidas técnicas; aceite: medição nula é `failure_of_measurement`, não zero).
- [x] T027 [US4] Integrar propriedades técnicas no notebook `app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb` (depende de T026; resultado: visualizações e tabelas futuras; aceite: nenhuma chamada a vídeo físico ou `ffprobe`).

**Checkpoint**: heterogeneidade técnica descrita sem julgamento de qualidade
linguística ou prontidão para treinamento.

## Phase 7: User Story 5 — Comparação entre datasets (Priority: P2)

**Goal**: Comparar descritivamente os datasets mantendo suas identidades.

**Independent Test**: Verificar compatibilidade de unidade, campos e
denominadores em uma tabela comparativa separada por dataset.

- [x] T028 [P] [US5] Criar testes de compatibilidade e denominadores em `app/dataset/tests/test_comparison.py` (depende de T011 e T025; resultado: diferenças de unidade e semântica são rejeitadas; aceite: nenhum dataset é implicitamente concatenado como uma população única).
- [x] T029 [US5] Implementar tabelas de comparação, classes compartilhadas e exclusivas em `app/dataset/src/libras_translation/analysis/comparison.py` (depende de T028; resultado: comparação descritiva auditável; aceite: cada linha mantém `dataset`, denominador e unidade).
- [x] T030 [US5] Integrar comparação e limitações no notebook `app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb` (depende de T029; resultado: seção comparativa; aceite: não há p-valores, efeitos inferenciais ou alegações causais).

**Checkpoint**: comparação descritiva pronta para execução autorizada.

## Phase 8: User Story 6 — Observações atípicas (Priority: P2)

**Goal**: Detectar e documentar extremos sem remoção.

**Independent Test**: Verificar flags em tabela, critérios e hashes antes/depois.

- [x] T031 [P] [US6] Criar testes de flags não destrutivas em `app/dataset/tests/test_outlier_flags.py` (depende de T019 e T026; resultado: cobertura IQR, percentil, MAD e regras específicas; aceite: número de linhas e hashes das entradas permanecem iguais).
- [x] T032 [US6] Implementar flags de outlier em `app/dataset/src/libras_translation/analysis/distributions.py` ou módulo dedicado sob `app/dataset/src/libras_translation/analysis/` (depende de T031; resultado: critério, limiar, variável, dataset e ação recomendada; aceite: nenhuma remoção, winsorização ou imputação automática).
- [x] T033 [US6] Integrar inspeção e limitações de outlier no notebook `app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb` (depende de T032; resultado: tabela e figura opcional; aceite: flag estatística não é rotulada automaticamente como erro).

**Checkpoint**: extremos documentados, não excluídos.

## Phase 9: User Story 7 — Síntese científica e publicação (Priority: P2)

**Goal**: Produzir síntese rastreável das Partes 1–6.

**Independent Test**: Auditar cada afirmação contra tabela, figura, snapshot,
proveniência e manifest de execução.

- [x] T034 [P] [US7] Criar testes de proveniência e rastreabilidade em `app/dataset/tests/test_eda_provenance.py` (depende de T009 e T010; resultado: validação de hashes, versões, parâmetros e outputs; aceite: uma execução repetida é identificável e publicação anterior é preservada).
- [x] T035 [US7] Implementar relatório de síntese e mapa de evidências em `app/dataset/src/libras_translation/analysis/` (depende de T016, T021, T024, T027, T030 e T033; resultado: estrutura, heterogeneidade, cobertura, riscos, limitações e implicações futuras; aceite: padrões pós-hoc são rotulados como exploratórios).
- [x] T036 [US7] Integrar síntese, limitações e escopo no notebook `app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb` (depende de T035; resultado: camada de interpretação sem lógica científica duplicada; aceite: não há decisão implícita de modelagem).
- [x] T037 [US7] Validar o pacote publicado em `app/data/processed/eda/` e documentar o quickstart da execução em `specs/004-etapa2-eda/` (depende de T034–T036; resultado: pacote corrente, archive, snapshots e relatório auditáveis; aceite: nenhum output foi produzido antes da autorização formal da EDA).

**Checkpoint**: Etapa 2 concluída somente após todas as partes, validações e
síntese atenderem aos critérios de `spec.md`.

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: concluída nesta formalização; apenas documentação e inspeção.
- **Phase 2**: bloqueia todas as partes analíticas.
- **Phases 3–6**: dependem da Phase 2; Partes 1–4 podem ser implementadas em
  grupos separados após os gates, mas a execução de cada parte continua
  autorizada somente pela governança do projeto.
- **Phase 7**: depende dos contratos de entrada e das partes anteriores para
  comparar variáveis compatíveis.
- **Phase 8**: depende dos resumos temporais e técnicos das Phases 3 e 6.
- **Phase 9**: depende de todas as partes e dos testes de proveniência.

### Parallel Opportunities

- T007–T009 podem ser desenvolvidas em paralelo em arquivos distintos.
- T013, T018, T022 e T025 podem ser preparadas em paralelo como testes
  independentes após os gates comuns.
- T019 e T023 podem avançar em paralelo após seus contratos específicos.
- A integração do notebook deve ocorrer após cada módulo produzir tabelas
  estáveis; não deve antecipar execução no notebook.

## Implementation Strategy

1. Manter a Phase 1 como evidência documental já revisada.
2. Completar os gates da Phase 2 sem ler `data/raw/` e sem executar EDA.
3. Entregar a Parte 1 como MVP e validar seus denominadores e hashes.
4. Adicionar distribuições, fatores cruzados e propriedades técnicas.
5. Adicionar comparação, flags de outliers e síntese rastreável.
6. Somente após autorização explícita executar a análise no ambiente do
   aplicativo e publicar artefatos derivados.

## Notes

- Todas as tarefas pendentes permanecem `[ ]`; os itens `[x]` representam
  preparação/inspeção documental realizada nesta sessão, não execução da EDA.
- Nenhuma tarefa permite treinamento, inferência, split, balanceamento,
  imputação, remoção de outliers, reexecução de `ffprobe` ou escrita em
  `data/raw/`.
- O contrato existente é a fonte única para unidade, chaves, população,
  missingness e publicação; `spec.md` e `plan.md` definem objetivos e execução
  sem criar um contrato paralelo.
