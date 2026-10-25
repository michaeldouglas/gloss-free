import path from "node:path";
import { readFile } from "node:fs/promises";
import { getHarnessPaths } from "../lib/paths.ts";

const root = getHarnessPaths().harnessRoot;
const configPath = path.join(root, ".codex", "hooks.json");
const config = JSON.parse(await readFile(configPath, "utf8")) as { hooks?: Record<string, Array<{ hooks?: Array<{ command?: string }> }>> };
const errors: string[] = [];
for (const [eventName, matchers] of Object.entries(config.hooks ?? {})) {
  for (const matcher of matchers) {
    for (const hook of matcher.hooks ?? []) {
      const command = hook.command ?? "";
      const match = /^bun run (core\/hooks\/[a-z0-9-]+\.ts)$/.exec(command);
      if (!match) errors.push(`${eventName}: expected a Bun TypeScript entrypoint, found '${command}'.`);
      else if (!(await Bun.file(path.join(root, match[1])).exists())) errors.push(`${eventName}: entrypoint does not exist: ${match[1]}`);
    }
  }
}
if (errors.length) {
  process.stderr.write(`${errors.map((error) => `- ${error}`).join("\n")}\n`);
  process.exit(1);
}
process.stdout.write("Infrastructure check passed: all Codex hooks point to existing Bun/TypeScript entrypoints.\n");
