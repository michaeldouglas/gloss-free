# Implementation Plan: Etapa 2 — Caracterização estatística e análise exploratória dos datasets

**Branch**: `feature/etapa2-contratos-eda` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-etapa2-eda/spec.md`

## Summary

Executar, somente após autorização posterior, uma caracterização descritiva e
uma análise exploratória reprodutível de V-LIBRASIL e MINDS-Libras. A execução
consumirá exclusivamente os manifests Parquet validados da Etapa 1, manterá os
datasets separados, preservará a unidade vídeo e publicará tabelas, figuras,
relatórios e proveniência em uma execução versionada. Esta formalização não
executa EDA, não calcula estatísticas, não gera gráficos e não altera dados.

## Technical Context

**Language/Version**: Python do aplicativo, executado com `uv`; a versão
efetiva será registrada pela execução.

**Primary Dependencies**: pandas, NumPy, SciPy, Matplotlib, scikit-learn e
PyArrow já disponíveis no ambiente do aplicativo para a fase descritiva. Não
instalar statsmodels, pingouin, PyMC ou ArviZ nesta etapa.

**Storage**: Entradas em `app/data/processed/metadata-validation/.../manifests/`;
saídas derivadas em `app/data/processed/eda/`. `app/data/raw/` permanece
somente leitura e fora da fonte analítica principal.

**Testing**: testes determinísticos com `uv run python -m unittest discover -s
dataset/tests -v` quando a implementação for executada; testes de contrato não
devem depender de rede, Docker ou de uma nova inspeção audiovisual.

**Target Platform**: Windows local do projeto, com caminhos explícitos e
execução reprodutível pelo ambiente Python do aplicativo.

**Project Type**: pacote Python de análise descritiva, com notebook Jupyter
como superfície de execução, inspeção, visualização e interpretação.

**Performance Goals**: processar os dois manifests completos de forma
determinística, sem leitura dos vídeos e sem escopo silenciosamente truncado.

**Constraints**: uma linha por vídeo; datasets separados; denominadores
explícitos; missingness sem imputação; flags sem remoção; nenhum teste
inferencial; nenhum split ou balanceamento; nenhum `ffprobe`; publicação
atômica com arquivo corrente e arquivo de execução.

**Scale/Scope**: V-LIBRASIL com 4.086 vídeos válidos e três exceções externas ao
corpus; MINDS-Libras com 800 vídeos válidos; variáveis existentes nos manifests
validados e seus campos derivados não destrutivos.

## Constitution Check

*GATE: Must pass before implementation and re-check after design.*

- **Preservação e reprodutibilidade: PASS** — inputs canônicos, hashes,
  parâmetros, versões, outputs e validações são registrados; execuções antigas
  permanecem em `archive/<run_id>`.
- **Fronteira dos dados: PASS** — `data/raw/` não é fonte analítica principal,
  não é alterado e não recebe saídas.
- **Unidade e dependência: PASS** — vídeo é a unidade; frames e vídeos do mesmo
  sinalizador não são tratados como réplicas independentes.
- **Arquitetura: PASS** — a lógica reutilizável permanece em
  `app/dataset/src/libras_translation/analysis/`; o notebook não vira camada de
  domínio nem exige Clean Architecture.
- **Escopo científico: PASS** — a etapa é descritiva e exploratória; não
  autoriza inferência, causalidade ou modelagem.

## Entradas, semântica e políticas

### Entradas canônicas

```text
app/data/processed/metadata-validation/v-librasil-raw/manifests/v_librasil_validated.parquet
app/data/processed/metadata-validation/minds-libras-raw/manifests/minds_libras_validated.parquet
```

O loader deve validar schema, população esperada e unicidade de
`filesystem_key` antes de qualquer resumo. A semântica específica de
`video_name`, `video_id`, `filesystem_key`, `class`, `user_id` e
`filename_valid` vem de `contracts/analysis-contract.md` e do dicionário de
dados; não deve ser inferida novamente a partir dos nomes.

### Variáveis

- População e fatores: `dataset`, `class`, `user_id`, `filesystem_key`.
- Temporalidade interna do vídeo: `actual_frame_count`, `actual_duration`,
  `actual_fps`.
- Técnica: `actual_width`, `actual_height`, `resolution`, `codec` e demais
  campos técnicos presentes no manifest.
- Controle e proveniência: campos de validade, origem, status e
  `filename_valid`, com os estados de missingness do contrato.
- A coluna original `fps` permanece contextual; a interpretação da Etapa 1
  continua sendo `frame_count` e não será renomeada silenciosamente.

## Ordem de execução planejada

As partes abaixo são a ordem normativa. Nenhuma parte será executada nesta
tarefa de formalização.

### Parte 1 — Caracterização geral

**Pergunta analítica**: qual é a composição, o tamanho e a completude
descritiva de cada população validada?

**Variáveis**: denominador de linhas, `class`, `user_id`, `class × user_id`,
campos numéricos temporais e técnicos, estados de missingness.

**Transformação permitida**: derivar apenas campos não destrutivos, como
`resolution`, e resumir valores no eixo da variável; não filtrar, imputar ou
alterar linhas.

**Tabelas**: overview por dataset; estatísticas numéricas; frequências de
classes, sinalizadores, resolução e codec; matriz `class × user_id`; missingness
por campo e estado; tabela de denominadores e exceções.

**Gráficos esperados**: barras de frequência para categorias e, se necessários
para leitura, tabelas equivalentes antes da figura. Nenhuma figura será criada
na formalização.

**Validações**: 4.086 e 800 linhas; uma chave física por linha; totais de
frequências iguais ao denominador; entradas inalteradas; datasets não
concatenados para interpretação.

**Riscos**: somar categorias com missingness incorreto, confundir exceções com
vídeos válidos ou assumir que a combinação cruzada é aninhada.

**Critério de conclusão**: overview, tabelas, metadados e validações publicados
por dataset, com denominadores explícitos e sem alteração dos inputs.

### Parte 2 — Distribuições temporais

**Pergunta analítica**: como se distribuem frames, duração e FPS real dentro de
cada dataset?

**Variáveis**: `actual_frame_count`, `actual_duration`, `actual_fps`.

**Transformação permitida**: estatísticas no eixo original; quantis, IQR, MAD,
percentis e transformações somente como análises de sensibilidade rotuladas,
sem substituir a escala original.

**Tabelas**: resumo n/missing/média/mediana/desvio-padrão/mínimo/Q1/Q3/máximo/IQR;
percentis adicionais quando justificados; flags de cauda e extremos.

**Gráficos esperados**: histograma ou ECDF, boxplot e, se útil, escala
logarítmica apenas como visão auxiliar; cada figura deve ter escopo, unidades,
denominador e tabela correspondente.

**Validações**: campos positivos quando o contrato exigir; missingness separado;
contagens e quantis reproduzíveis; nenhum valor extremo excluído.

**Riscos**: caudas longas ocultadas por média, escala inadequada, zeros
verdadeiros confundidos com falha de medição e dependência entre frames.

**Critério de conclusão**: distribuições descritas por dataset, com forma,
dispersão, assimetria quando aplicável, caudas, extremos e limitações.

### Parte 3 — Classes e sinalizadores

**Pergunta analítica**: qual é a cobertura por classe, por sinalizador e por
combinação cruzada?

**Variáveis**: `class`, `user_id`, `class × user_id`, `dataset`.

**Transformação permitida**: contagens e proporções com denominador explícito;
construção da matriz esparsa sem preencher ausência com imputação.

**Tabelas**: classes por dataset; sinalizadores por dataset; matriz cruzada;
cobertura de sinalizadores por classe; classes incompletas; participação
relativa e lista de classes compartilhadas.

**Gráficos esperados**: barras ordenadas, heatmap da matriz e tabela alternativa
acessível. O gráfico nunca substitui a tabela.

**Validações**: soma das células igual ao denominador; categorias nulas
preservadas; chaves específicas por dataset respeitadas; ausência e zero
distintos.

**Riscos**: interpretar cobertura como balanceamento desejável, apagar classes
raras por limiar visual ou supor que `user_id` é independente.

**Critério de conclusão**: estrutura cruzada e cobertura publicadas sem decisão
de balanceamento ou de exclusão.

### Parte 4 — Propriedades técnicas

**Pergunta analítica**: quais propriedades de captura e codificação são
observadas e quão heterogêneas são?

**Variáveis**: `actual_width`, `actual_height`, `resolution`, proporção de
aspecto derivada, `actual_fps`, `codec` e demais campos técnicos disponíveis.

**Transformação permitida**: derivar proporção de aspecto e categorias técnicas
sem sobrescrever o manifest; manter valores ausentes com estado semântico.

**Tabelas**: frequências de resolução e codec; resumo numérico de dimensões,
aspect ratio e FPS; combinações técnicas; missingness técnico.

**Gráficos esperados**: barras de resolução/codec e distribuições de aspect
ratio/FPS, sempre acompanhadas de tabela e metadados.

**Validações**: dimensões não negativas quando aplicável; codec e resolução
compatíveis com o schema; unidade e denominador declarados; `ffprobe` não
executado.

**Riscos**: confundir característica técnica com qualidade linguística, perder
diferenças de unidade ou transformar categoria rara em erro.

**Critério de conclusão**: propriedades técnicas reportadas por dataset sem
reinspeção audiovisual ou decisão de aceitabilidade para treinamento.

### Parte 5 — Comparação V-LIBRASIL × MINDS-Libras

**Pergunta analítica**: onde os dois corpora são descritivamente semelhantes ou
heterogêneos, respeitando seus desenhos e chaves?

**Variáveis**: tamanho, classes, sinalizadores, classes compartilhadas e
exclusivas, duração, frames, FPS, resolução, codec e medidas compatíveis.

**Transformação permitida**: alinhar nomes e unidades somente quando o contrato
confirmar compatibilidade; calcular diferenças descritivas e proporções sem
teste de hipótese.

**Tabelas**: quadro comparativo por dataset; classes compartilhadas/exclusivas;
resumos técnicos lado a lado; notas sobre denominadores e exceções.

**Gráficos esperados**: comparações descritivas pareadas por variável, sem
anotações de significância e sem gráfico que implique população única.

**Validações**: `dataset` sempre preservado; mesma unidade de medida; chaves e
semânticas específicas não transferidas; nenhuma inferência causal.

**Riscos**: comparar campos incompatíveis, confundir diferenças de desenho com
efeito, ou concatenar os corpora sem justificativa.

**Critério de conclusão**: uma comparação descritiva auditável, com
compatibilidades, incomparabilidades e limitações explícitas.

### Parte 6 — Observações atípicas

**Pergunta analítica**: quais observações merecem inspeção posterior por serem
extremas ou inconsistentes com o padrão descritivo?

**Variáveis**: campos temporais, técnicos e combinações categóricas relevantes.

**Transformação permitida**: flags por IQR, percentil, MAD, inspeção gráfica ou
regra específica justificada; manter escala e valor originais.

**Tabelas**: flags por variável, regra, limiar, valor observado, dataset,
`filesystem_key` tokenizada no relatório e ação recomendada; análise de
sensibilidade sem remoção.

**Gráficos esperados**: boxplots, dispersões ou ECDFs para tornar a flag
inspecionável; sempre com tabela correspondente.

**Validações**: flag não reduz número de linhas; critério determinístico;
outlier estatístico não é rotulado automaticamente como erro; nenhum registro
é removido, imputado ou winsorizado.

**Riscos**: caudas legítimas, múltiplos testes exploratórios, identificadores
diretos em relatórios e uso posterior da flag como filtro silencioso.

**Critério de conclusão**: flags e critérios publicados com limitações e sem
alteração dos manifests.

### Parte 7 — Síntese científica

**Pergunta analítica**: o que as evidências permitem afirmar sobre estrutura,
heterogeneidade, cobertura, limitações e próximos riscos?

**Variáveis**: somente resultados publicados nas Partes 1–6 e seus metadados.

**Transformação permitida**: síntese textual rastreável; nenhuma nova métrica
oculta no relatório.

**Tabelas**: índice de evidências, limitações, riscos e implicações para a
próxima etapa; mapa de origem entre afirmação e artefato.

**Gráficos esperados**: não necessários; se uma figura for usada, ela deve ser
derivada de tabela publicada e ter descrição acessível.

**Validações**: cada conclusão aponta para artefato; padrões pós-hoc são
rotulados como exploratórios; nenhuma alegação causal, linguística ou
inferencial não planejada.

**Riscos**: duplicar números manualmente, transformar exploração em hipótese,
ou antecipar decisão de modelagem.

**Critério de conclusão**: relatório reproduzível com limites, riscos,
proveniência e recomendações para a próxima etapa, sem decisão de treinamento.

## Missingness, outliers e inferência

Os estados `missing_real`, `structural_absence`, `not_applicable`,
`failure_of_measurement` e `zero_true` permanecem distintos. Nenhum valor é
imputado. O `filename_valid = null` do MINDS-Libras é ausência estrutural por
desenho. Medição técnica nula é falha de medição, não zero.

Outliers são detectados, descritos e submetidos a análise de sensibilidade
quando necessário; nunca são removidos automaticamente. IQR, percentis, MAD,
inspeção gráfica e regras específicas devem ser documentados por variável.

Não haverá testes inferenciais nesta feature. Qualquer hipótese futura deve ser
pré-especificada em uma etapa própria, com unidade, dependência, estimando,
contrastes, pressupostos, multiplicidade, tamanho de efeito e incerteza.

## Reprodutibilidade e publicação

Cada execução registra, para ambos os manifests, caminho relativo, SHA-256,
tamanho, número de linhas e colunas, schema, timestamp UTC, commit, parâmetros,
versões de pandas/NumPy/SciPy/Matplotlib/scikit-learn/PyArrow, `run_id`, raiz
de saída, outputs, hashes dos outputs e resultado das validações.

O processo monta a execução em `archive/<run_id>`, valida entradas, tabelas e
figuras e publica atomicamente a versão corrente. `provenance/CURRENT.json`
identifica a publicação atual. Nenhuma execução arquivada é sobrescrita.

## Código e notebooks

A lógica reutilizável deve permanecer em:

```text
app/dataset/src/libras_translation/analysis/
```

O notebook deve permanecer em:

```text
app/notebooks/dataset/02_caracterizacao_estatistica_eda.ipynb
```

Ele somente orquestra, inspeciona, visualiza e interpreta. Não deve conter a
lógica científica extensa, não deve ler `data/raw/` como fonte principal e não
deve reexecutar `ffprobe`.

## Saídas

```text
app/data/processed/eda/
├── reports/       # publicação corrente
├── tables/        # publicação corrente
├── figures/       # publicação corrente; vazio até a execução autorizada
├── snapshots/     # snapshots públicos/reprodutíveis
├── provenance/    # CURRENT.json e execução corrente
└── archive/       # execuções anteriores por run_id
```

## Estrutura de implementação

A arquitetura permanece Flat Architecture híbrida. O dicionário, os contratos
de input/output, a caracterização, as distribuições, a comparação e as regras
de outlier ficam em módulos pragmáticos de `analysis/`. O notebook chama esses
módulos e apresenta resultados. Não será introduzida uma camada formal de
domínio, adaptadores ou Clean Architecture.

## Complexity Tracking

Nenhuma violação constitucional ou complexidade adicional não justificada foi
identificada.
