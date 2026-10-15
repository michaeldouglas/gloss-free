# Quickstart: Validar Metadados Técnicos de Vídeo

## Pré-requisitos

- Windows com PowerShell, Docker Desktop, `uv` e o ambiente do projeto.
- Dataset presente em `app/data/raw/<dataset>/`.
- `annotations.csv` disponível no diretório do dataset.

## Preparar e validar o contêiner

A partir de `app/`:

```powershell
uv sync
docker compose -f docker/video-processing/compose.yaml config --quiet
docker compose -f docker/video-processing/compose.yaml build
```

## Executar a validação

```powershell
docker compose -f docker/video-processing/compose.yaml run --rm -T video-processing `
  python -m libras_translation.cli video validate-metadata `
  --dataset v-librasil-raw
```

O comando lê `data/raw/v-librasil-raw/` e grava os resultados em
`data/processed/metadata-validation/v-librasil-raw/`. A pasta `data/raw/` é
montada como somente leitura.

## Ler os resultados

1. Abra `metadata_validation.json` para a fonte de verdade da execução.
2. Abra `video_metadata.csv` para conferir os valores reais e os erros de
   inspeção.
3. Abra `metadata_comparison.csv` para comparar largura, altura e as duas
   hipóteses para `fps` por vídeo.
4. Abra `fps_hypotheses_summary.csv` para ver a distribuição das evidências.
5. Consulte `toolchain.json` e `validation.log` para rastreabilidade.

`fps_rate_status` e `fps_frame_count_status` são hipóteses separadas, e
`fps_hypothesis` registra a interpretação da linha (`rate`, `frame_count`,
`ambiguous`, `none` ou `inconclusive`). Nenhum resultado renomeia ou
substitui a coluna original `fps`.

## Executar testes determinísticos

A partir de `app/`:

```powershell
uv run python -m unittest discover -s dataset/tests -v
```

Os testes usam diretórios temporários e respostas controladas do `ffprobe`;
eles não baixam datasets, não usam credenciais e não leem o corpus bruto.

## Visualizar no notebook

Abra `notebooks/dataset/01_inventario_v-librasil.ipynb` a partir da raiz de
`app/` e execute as células em ordem. A seção **Validação dos metadados
técnicos CSV × vídeo real** aparece depois de **Validação CSV × filesystem** e
antes de **Validação da convenção do nome do arquivo**.

O notebook exibe os arquivos derivados; ele não corrige, renomeia, remove ou
substitui vídeos e CSVs.

## Validar proveniência e gerar manifest

Depois da seção **Validação da convenção do nome do arquivo**, execute a etapa
de qualidade. Ela reutiliza `metadata_validation.json` e não repete a inspeção
dos vídeos quando esse arquivo já existe:

```powershell
uv run libras video validate-quality --dataset v-librasil-raw
uv run libras video validate-quality --dataset minds-libras-raw
```

No V-LIBRASIL, `error.csv` é obrigatório como fonte de proveniência. Para cada
exceção, a validação verifica se o item também aparece em `annotations.csv`, se
há arquivo correspondente em `videos/` e se o motivo é compatível com o estado
observado. Também são reportados arquivos ausentes que não aparecem em
`error.csv`, evitando transformar perda silenciosa em exceção conhecida.

Os artefatos ficam sob `data/processed/metadata-validation/`:

```text
reports/metadata_validation_report.md
reports/metadata_issues.csv
reports/metadata_summary.json
manifests/v_librasil_validated.parquet
manifests/minds_libras_validated.parquet
```

Os problemas usam quatro níveis: `CRITICAL`, `ERROR`, `WARNING` e `INFO`.
`metadata_summary.json` registra `GO` quando não há problemas críticos ou
erros; caso contrário registra `NO-GO` e o comando termina com código 2, sem
deixar de gravar as evidências. Os manifests adicionam os metadados observados
e flags como `file_exists`, `file_readable`, `filename_valid`,
`metadata_valid`, `validation_status` e `validation_notes`. O dataset original
em `data/raw/` nunca é alterado.

## Verificação desta feature

Nesta implementação foram executados a suíte determinística com 24 testes,
`docker compose config --quiet`, a construção da imagem
`libras-video-processing:0.1.0` e um smoke test do contêiner com um vídeo
temporário criado em `/tmp`. O corpus real não foi processado durante a
implementação: essa execução deve ocorrer depois que o dataset estiver
presente em `data/raw/`, usando o comando acima ou as células do notebook.
