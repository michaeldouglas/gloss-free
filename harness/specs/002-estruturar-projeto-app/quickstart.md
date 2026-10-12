# Quickstart: Estruturar Projeto App

## Pré-requisitos

- Windows com PowerShell.
- Python >=3.10.
- `uv` instalado.
- `HF_TOKEN` configurado somente quando a operação exigir acesso ao Hugging
  Face; o valor não deve ser exibido ou versionado.

## Preparar o ambiente

A partir da raiz da aplicação:

```powershell
Set-Location C:\Users\mdbaa\development\Dissertacao\app
uv sync
```

## Validar a suíte local

Os testes usam fakes e não baixam datasets:

```powershell
uv run python -m unittest discover -s dataset/tests -v
```

Resultado validado em 2026-10-11: 11 testes executados com sucesso.

## Verificar a CLI

```powershell
uv run libras --help
uv run libras data --help
```

## Listar um dataset sem baixar vídeos

Essa operação consulta o Hugging Face e atualiza o manifesto correspondente:

```powershell
uv run libras data list --dataset minds-libras-raw
```

## Baixar uma amostra limitada

Use uma seleção explícita e limite pequeno para uma verificação operacional:

```powershell
uv run libras data download --dataset minds-libras-raw --limit 2 --workers 2
```

Os dados ficam em `data/raw/<dataset>/` e os manifestos em
`data/manifests/`. Downloads reais não fazem parte da suíte automatizada
padrão.

## Limites do projeto

O código da aplicação permanece em `app/`; os artefatos Spec Kit permanecem em
`harness/`. A pasta `old/` é legado e não participa da validação.
