---
name: harness-verify
description: Run the harness implementation quality gate, including the application test suite and Spec Kit task completion check.
---

Run the project-local validation from the harness repository root:

```bash
bun run core/scripts/verify-harness.ts verify
```

Do not modify files, change branches, commit, or invoke an MCP server. Report the command result and any remaining task or test failures.
