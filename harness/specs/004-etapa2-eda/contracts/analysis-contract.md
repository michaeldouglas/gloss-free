# Contrato metodológico e estrutural — Etapa 2

Status: formalizado para planejamento da Etapa 2. Este contrato não executa
EDA, não calcula estatísticas, não cria gráficos, não altera datasets e não
inicia treinamento.

## Pré-condição de entrada

A Etapa 1 — Metadata Validation está formalmente encerrada antes da execução
analítica: `global_stage1_decision = GO`, `stage1_status = completed`, com
V-LIBRASIL = `GO` e MINDS-Libras = `GO`. Os relatórios históricos da Etapa 1
continuam preservados; este contrato usa o fechamento canônico atual como
pré-condição e não reescreve evidências históricas.

## Unidade observacional e fatores cruzados

Em ambos os datasets, `1 linha = 1 vídeo validado`. O vídeo é a unidade
observacional principal. `class` é um fator categórico relacionado ao sinal
executado e `user_id` é um fator categórico relacionado ao
sinalizador/articulador. Esses fatores não devem ser representados como uma
hierarquia estritamente aninhada: uma classe pode ocorrer para múltiplos
sinalizadores e um sinalizador pode executar múltiplas classes. A estrutura
analítica é, portanto:

```text
class (fator categórico) ─┐
                          ├── vídeo validado (unidade observacional)
user_id (fator categórico)┘
                          └── frames (medidas internas do vídeo)
```

Os frames pertencem ao vídeo e não são observações amostrais independentes.
Tratar frames como observações independentes inflaria artificialmente o número
de unidades e a precisão aparente. Tratar vídeos do mesmo `user_id` como
completamente independentes também pode produzir pseudorreplicação, porque
características do sinalizador, da captura e do contexto podem ser compartilhadas.
Análises futuras devem declarar o vídeo como unidade, modelar ou controlar os
fatores cruzados quando necessário e evitar inferência que ignore essa
dependência.

## Entradas e semântica das chaves

As entradas primárias são somente os manifests canônicos:

- `app/data/processed/metadata-validation/v-librasil-raw/manifests/v_librasil_validated.parquet`
- `app/data/processed/metadata-validation/minds-libras-raw/manifests/minds_libras_validated.parquet`

No V-LIBRASIL, `video_name` identifica o nome físico por meio de
`filesystem_key`; `video_id` é auxiliar/descritivo. No MINDS-Libras,
`filesystem_key_column = video_id`: `video_id` é a chave física e `video_name` é
descritivo. No manifest derivado, `filesystem_key` é a coluna de reconciliação
gerada a partir dessa chave; `class` representa o sinal e `user_id` representa o
sinalizador.
Essas definições específicas estão no dicionário analítico e não devem ser
transferidas entre datasets.

`metadata_validation.json`, `video_metadata.csv`, `metadata_comparison.csv`,
`metadata_summary.json` e `stage1_global_closeout.json` são apenas evidência de
proveniência, verificações específicas e contexto. A Etapa 2 não deve reexecutar
`ffprobe` para construir a EDA.

## Política de população e exceções

- V-LIBRASIL: corpus analítico principal com 4.086 vídeos validados. As três
  entradas de `error.csv` permanecem documentadas separadamente, não entram nas
  estatísticas dos vídeos válidos e exigem denominador explícito em cada relatório.
- MINDS-Libras: corpus analítico com 800 vídeos válidos. A ausência de
  `error.csv` é informação de proveniência e não constitui erro.

Nenhuma imputação, remoção de outliers, balanceamento ou criação de split ocorre
nesta preparação.

## Missingness

Os estados devem permanecer distintos: `missing_real`, `structural_absence`,
`not_applicable`, `failure_of_measurement` e `zero_true`. O caso obrigatório do
MINDS-Libras é `filename_valid = null`: isso é ausência estrutural por desenho,
pois `video_name` é descritivo e não a chave física; não é dado ausente nem
problema de qualidade. Medições técnicas nulas significam falha de medição, não
zero. Nenhum estado é imputado nesta etapa. A tabela completa está em
`analysis/data_dictionary.py`.

## Contrato de saída

O layout canônico futuro é:

```text
app/data/processed/eda/
├── reports/       # publicação corrente
├── tables/        # publicação corrente
├── figures/       # publicação corrente; vazio até a execução autorizada
├── snapshots/     # snapshots públicos/reprodutíveis
└── provenance/    # manifest de execução e CURRENT.json
```

Cada execução receberá `run_id = timestamp UTC + prefixo curto do commit`. A
execução será montada privadamente, validada e publicada atomicamente. A versão
anterior será preservada em `archive/<run_id>` e nunca será confundida com a
publicação corrente, identificada por `provenance/CURRENT.json`. Não há
sobrescrita silenciosa.

## Reprodutibilidade

O registro de execução deve conter, para as duas entradas: caminho relativo,
SHA-256, tamanho, número de linhas e colunas; timestamp UTC; commit do código;
parâmetros; versões de pandas, NumPy, SciPy, Matplotlib, scikit-learn e PyArrow;
raiz de saída; `run_id`; e decisão de publicação. As tabelas devem ser
determinísticas para a mesma entrada e configuração. O helper
`build_execution_provenance` cria o registro em memória, sem escrever ou
executar uma análise.

## Dependências e separação de responsabilidades

O ambiente atual com pandas, NumPy, SciPy, Matplotlib, scikit-learn e PyArrow é
suficiente para a primeira fase descritiva. Não instalar `statsmodels`,
`pingouin`, `PyMC` ou `ArviZ`, nem criar ambiente estatístico separado, até que
uma pergunta inferencial os exija. A lógica científica reutilizável permanece
em `app/dataset/src/libras_translation/analysis/`; o notebook somente orquestra,
inspeciona, visualiza e interpreta.

## Testes mínimos

Os testes de contrato devem cobrir: leitura dos manifests canônicos; uma linha
por chave física; contagens esperadas; agrupamento determinístico; classificação
de nulo estrutural; separação das três exceções do V-LIBRASIL; hash inalterado
das entradas; e identidade reprodutível para a mesma entrada/configuração.

## Limites da Etapa 2

Este contrato prepara caracterização descritiva e EDA. Não autoriza conclusões
linguísticas, inferenciais ou causais, não trata frames como amostras, e não
substitui a validação técnica da Etapa 1.
