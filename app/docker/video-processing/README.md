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
  ffprobe -v error -show_format -show_streams -of json /workspace/data/raw/exemplo.mp4
```

Os arquivos brutos não devem ser sobrescritos. Processamentos futuros devem
gravar em `/workspace/data/processed` e registrar seus parâmetros e resultados.
