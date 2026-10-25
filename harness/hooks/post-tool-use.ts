import path from "node:path";
import { fileURLToPath } from "node:url";
import { stat } from "node:fs/promises";
import { emitHook, readHookEvent, type HookEvent, toolInputString } from "../lib/hook-protocol.ts";
import { runCommand, type CommandResult } from "../lib/process.ts";

export type CommandRunner = (command: string, args: string[], options?: { cwd?: string; quiet?: boolean }) => Promise<CommandResult>;
const appGraphPath = ["..", "app", "graphify-out"].join("/");

export function isRelevantEdit(command: string): boolean {
  return /^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s+(?:\.\.[/\\]app[/\\]|specs[/\\]|\.specify[/\\]|\.agents[/\\]|\.codex[/\\]|artifacts[/\\](?:architecture|reports)[/\\]|scripts[/\\]|hooks[/\\]|lib[/\\]|assets[/\\]|tests[/\\]|package\.json|AGENTS\.md)/im.test(command);
}

export async function handlePostToolUse(event: HookEvent, root: string, run: CommandRunner = runCommand): Promise<void> {
  const command = toolInputString(event, "command");
  if (!isRelevantEdit(command)) return;
  const emitMessage = (message: string, systemMessage: string) => emitHook({
    systemMessage,
    hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: message },
  });
  if (!(await Bun.file(path.join(root, "graphify-out", "graph.json")).exists())) {
    emitMessage("Relevant files changed, but the canonical Graphify graph does not exist yet. Run graphify . before relying on graph queries.", "Graphify refresh skipped: canonical graph is missing.");
    return;
  }
  try {
    await stat(path.resolve(root, "..", "app", "graphify-out"));
    emitMessage(`Relevant files changed, but ${appGraphPath}/ exists. The canonical graph remains harness/graphify-out/.`, "Graphify layout warning: duplicate application graph detected.");
    return;
  } catch {
    // No duplicate graph directory.
  }
  const graphResult = await run("graphify", ["update", "."], { cwd: root, quiet: true }).catch(() => null);
  if (!graphResult || graphResult.exitCode !== 0) {
    emitMessage(`Graphify update failed after a relevant edit (exit ${graphResult?.exitCode ?? "unknown"}). Run graphify update . manually before answering graph-based questions.`, "Graphify refresh failed after the edit.");
    return;
  }
  const architecture = await run("bun", ["run", "scripts/refresh-architecture.ts", "--dataset", "code-edit"], { cwd: root, quiet: true }).catch(() => null);
  const architectureMessage = architecture?.exitCode === 0 ? "Archify refresh checked; generated diagrams remain under harness/artifacts/architecture/." : "Archify refresh failed; inspect artifacts/architecture/architecture-refresh.json.";
  const projectRoot = path.resolve(root, "..");
  const showroom = await run("bun", ["run", "scripts/build-showroom.ts", "--repo-root", projectRoot], { cwd: root, quiet: true }).catch(() => null);
  const showroomMessage = showroom?.exitCode === 0 ? "Showroom atualizado em docs/ a partir dos artefatos derivados." : "Showroom refresh falhou; execute o notebook ou revise o gerador.";
  emitMessage(`Graphify was incrementally refreshed after the relevant edit. The canonical output remains harness/graphify-out/. ${architectureMessage} ${showroomMessage}`, "Canonical Graphify, architecture and showroom state refreshed.");
}

if (import.meta.main) {
  const event = await readHookEvent();
  if (event) {
    const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
    await handlePostToolUse(event, root);
  }
}
