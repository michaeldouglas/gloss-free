# Como contribuir

Este projeto está em desenvolvimento acadêmico. Alterações devem preservar a
rastreabilidade dos dados, a reprodutibilidade dos experimentos e a separação
entre a aplicação (`app/`) e a coordenação do projeto (`harness/`).

## Ambiente local

```powershell
cd app
uv sync --locked
uv run python -m unittest discover -s dataset/tests -v
```

Para validar o ambiente de vídeos:

```powershell
docker compose -f docker/video-processing/compose.yaml config --quiet
docker compose -f docker/video-processing/compose.yaml build
```

## Branches e Pull Requests

- Crie uma branch no formato `feature/<slug>`.
- Abra o primeiro Pull Request da feature para `develop`.
- Use o título `develop <- feature/<slug>`.
- A promoção para `main` acontece por Pull Request de `develop` para `main`,
  com o título `main <- develop`.
- Explique no Pull Request o que foi alterado e como a validação foi feita.

## Dados e credenciais

- Não inclua vídeos brutos, tokens, arquivos `.env` ou credenciais no Git.
- Preserve os arquivos originais e grave resultados processados em diretórios
  separados.
- Mantenha manifestos e parâmetros suficientes para reproduzir uma execução.
- Respeite as licenças, autorizações e condições de uso dos datasets.

Alterações que possam afetar movimentos das mãos, expressões faciais ou outras
informações relevantes para vídeos de Libras devem explicar essa decisão e
seus impactos nos resultados.
