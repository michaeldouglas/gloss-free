---
name: harness-prepare
description: Validate the current feature branch and Spec Kit artifacts before implementation begins.
---

Run the project-local validation from the harness repository root:

```powershell
$root = (Get-Location).Path
& (Join-Path $root '.codex/hooks/verify-harness.ps1') -Mode prepare
```

This command is read-only. It must report failures instead of editing Spec Kit artifacts, changing branches, committing, or invoking any MCP server.
