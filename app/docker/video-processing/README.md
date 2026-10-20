# Video Processing Docker

Container base para inspeção e pré-processamento de vídeos com Python,
FFmpeg e `ffprobe`.

O serviço monta `data/raw` somente para leitura e grava resultados derivados
em `data/processed`. Não há portas publicadas nem acesso de rede por padrão.

## Verificar o Compose

A partir da raiz de `app/`:

```powershell
docker compose -f docker/video-processing/compose.yaml config --quiet
```

## Construir a imagem

```powershell
docker compose -f docker/video-processing/compose.yaml build
```

## Verificar as ferramentas

```powershell
docker compose -f docker/video-processing/compose.yaml run --rm video-processing ffprobe -version
docker compose -f docker/video-processing/compose.yaml run --rm video-processing ffmpeg -version
```

## Inspecionar um vídeo

```powershell
docker compose -f docker/video-processing/compose.yaml run --rm video-processing `
  ffprobe -v error -show_format -show_streams -of json /workspace/app/data/raw/exemplo.mp4
```

## Validar um dataset

O comando de validação usa a mesma imagem do serviço e mantém `data/raw` como
somente leitura:

```powershell
docker compose -f docker/video-processing/compose.yaml run --rm -T video-processing `
  python -m libras_translation.cli video validate-metadata `
  --dataset v-librasil-raw
```

Os resultados ficam em `/workspace/app/data/processed/metadata-validation/` e são
projetados para `data/processed/metadata-validation/` no host. O artefato
`metadata_validation.json` é a fonte de verdade; `video_metadata.csv`,
`metadata_comparison.csv` e `fps_hypotheses_summary.csv` facilitam a leitura no
notebook. Divergências nos dados não são tratadas como falha da ferramenta,
mas entradas ausentes, erros do `ffprobe` e falhas do contrato de saída ficam
registrados e causam status não zero quando a execução não puder ser concluída.

O `toolchain.json` registra as versões efetivas do FFmpeg/ffprobe, comandos e
parâmetros. A imagem deve ser reconstruída quando o código da aplicação mudar.

## Proveniência e decisão GO/NO-GO

Depois da validação da convenção de nomes, gere as evidências de qualidade a
partir do JSON técnico já existente:

```powershell
docker compose -f docker/video-processing/compose.yaml run --rm -T video-processing `
  python -m libras_translation.cli video validate-quality `
  --dataset v-librasil-raw
```

Para o MINDS-Libras, repita com `--dataset minds-libras-raw`. O comando não
executa novamente o `ffprobe` quando `metadata_validation.json` já existe; ele
reconcilia os resultados com `annotations.csv`, `error.csv` e `videos/`.

No V-LIBRASIL, `error.csv` faz parte da proveniência obrigatória. A rotina
verifica sobreposição com `annotations.csv`, existência física das exceções,
consistência do motivo e arquivos ausentes sem exceção correspondente.

Os artefatos são gravados em `data/processed/metadata-validation/`:

```text
reports/metadata_validation_report.md
reports/metadata_issues.csv
reports/metadata_summary.json
manifests/v_librasil_validated.parquet
manifests/minds_libras_validated.parquet
```

`metadata_summary.json` registra a decisão `GO` ou `NO-GO`. O comando retorna
`2` para `NO-GO`, depois de gravar o relatório e o manifest. Os níveis são
`CRITICAL`, `ERROR`, `WARNING` e `INFO`; os detalhes e as evidências ficam em
`metadata_issues.csv`. O Parquet é sempre derivado, e os arquivos sob
`data/raw/` permanecem somente leitura.

Os arquivos brutos não devem ser sobrescritos. Processamentos futuros devem
gravar em `/workspace/app/data/processed` e registrar seus parâmetros e resultados.
