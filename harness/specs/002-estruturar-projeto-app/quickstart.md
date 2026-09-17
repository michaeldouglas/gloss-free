# Quickstart: Estruturar Projeto App

## Pré-requisitos

- Windows com PowerShell.
- Python 3.14 ou superior, conforme `app/pyproject.toml`.
- `uv` é recomendado para os próximos ciclos, mas não é necessário para a
  execução mínima atual.

> No ambiente usado para este plano foi encontrado Python 3.13.7. A validação
> deve ser considerada bloqueada até que Python 3.14+ esteja disponível ou o
> requisito do projeto seja revisado explicitamente.

## Executar a verificação mínima

A partir da raiz do repositório:

```powershell
Set-Location .\app
python --version
python .\main.py
```

Resultado esperado após atender ao requisito de versão:

```text
Hello from app!
```

## Validar a separação dos diretórios

```powershell
Test-Path .\README.md
Test-Path .\pyproject.toml
Test-Path ..\harness\.specify
Test-Path ..\harness\specs
```

Os quatro comandos devem retornar `True`. A implementação da aplicação deve
ser criada em `app/`; especificações, planos e tarefas devem permanecer em
`harness/specs/`.

## Falhas esperadas

- Se `python --version` indicar uma versão menor que 3.14, interrompa a
  validação e instale/ative Python 3.14+ antes de continuar.
- Se `main.py` não for encontrado, confirme que o diretório atual é
  `C:\Users\mdbaa\development\Dissertacao\app`.
- Se a saída mínima mudar, atualize a especificação e este quickstart antes de
  considerar a base aprovada.

## Próxima fase

Depois da revisão deste plano, execute `speckit-tasks` para transformar a
feature em tarefas ordenadas. A implementação deve ocorrer somente após a
aprovação do plano.
