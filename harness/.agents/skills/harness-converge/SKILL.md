---
name: harness-converge
description: Validate a converged Spec Kit feature and refresh the canonical Graphify graph.
---

Run the project-local convergence validation from the harness repository root:

```powershell
$root = (Get-Location).Path
& (Join-Path $root '.codex/hooks/verify-harness.ps1') -Mode converge
```

The command may update generated Graphify output under `graphify-out/`, but it must not alter source code, Spec Kit documents, branches, commits, or MCP configuration. Report any open tasks as follow-up work rather than silently changing them.
