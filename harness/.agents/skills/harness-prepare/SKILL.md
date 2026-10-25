---
name: harness-prepare
description: Validate the current feature branch and Spec Kit artifacts before implementation begins.
---

Run the project-local validation from the harness repository root:

```bash
bun run core/scripts/verify-harness.ts prepare
```

This command is read-only. It must report failures instead of editing Spec Kit artifacts, changing branches, committing, or invoking any MCP server.
