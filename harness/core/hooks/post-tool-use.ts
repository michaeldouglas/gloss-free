import path from "node:path";
import { stat } from "node:fs/promises";
import { emitHook, readHookEvent, type HookEvent, toolInputString } from "../lib/hook-protocol.ts";
import { runCommand, type CommandResult } from "../lib/process.ts";
import { createHarnessPaths, getHarnessPaths } from "../lib/paths.ts";

export type CommandRunner = (command: string, args: string[], options?: { cwd?: string; quiet?: boolean }) => Promise<CommandResult>;
const appGraphPath = ["..", "app", "graphify-out"].join("/");

export function isRelevantEdit(command: string, filePath = ""): boolean {
  const paths = [...command.matchAll(/^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s+(.+)$/gim), ...command.matchAll(/^\*\*\*\s+Move to:\s+(.+)$/gim)].map((match) => match[1].trim());
  if (!paths.length && command.trim() && !command.includes("***")) paths.push(command.trim());
  if (filePath.trim()) paths.push(...filePath.split(/\r?\n/).map((value) => value.trim()).filter(Boolean));
  return paths.some((value) => {
    const normalized = value.replaceAll("\\", "/").replace(/^\.\//, "");
    const relative = normalized.replace(/^(?:.*\/)?harness\//i, "");
    return /^(?:\.\.?\/)?app\//i.test(normalized)
      || /(?:^|\/)app\//i.test(normalized)
      || /^(?:specs|\.specify|\.agents|\.codex|artifacts\/(?:architecture|reports)|core\/(?:scripts|hooks|lib|assets)|scripts|hooks|lib|assets|tests)\//i.test(relative)
      || /^(?:package\.json|AGENTS\.md)$/.test(relative);
  });
}

export async function handlePostToolUse(event: HookEvent, root: string, run: CommandRunner = runCommand): Promise<void> {
  const paths = createHarnessPaths(root);
  const command = toolInputString(event, "command");
  const filePath = ["file_path", "path", "new_path", "old_path"]
    .map((key) => toolInputString(event, key))
    .filter(Boolean)
    .join("\n");
  if (!isRelevantEdit(command, filePath)) return;
  const emitMessage = (message: string, systemMessage: string) => emitHook({
    systemMessage,
    hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: message },
  });
  if (!(await Bun.file(paths.graphifyGraph).exists())) {
    emitMessage("Relevant files changed, but the canonical Graphify graph does not exist yet. Run graphify . before relying on graph queries.", "Graphify refresh skipped: canonical graph is missing.");
    return;
  }
  try {
    await stat(path.join(paths.appRoot, "graphify-out"));
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
  const architecture = await run("bun", ["run", "core/scripts/refresh-architecture.ts", "--dataset", "code-edit"], { cwd: root, quiet: true }).catch(() => null);
  const architectureMessage = architecture?.exitCode === 0 ? "Archify refresh checked; generated diagrams remain under harness/artifacts/architecture/." : "Archify refresh failed; inspect artifacts/architecture/architecture-refresh.json.";
  const projectRoot = paths.repositoryRoot;
  const showroom = await run("bun", ["run", "core/scripts/build-showroom.ts", "--repo-root", projectRoot], { cwd: root, quiet: true }).catch(() => null);
  const showroomMessage = showroom?.exitCode === 0 ? "Showroom atualizado em docs/ a partir dos artefatos derivados." : "Showroom refresh falhou; execute o notebook ou revise o gerador.";
  emitMessage(`Graphify was incrementally refreshed after the relevant edit. The canonical output remains harness/graphify-out/. ${architectureMessage} ${showroomMessage}`, "Canonical Graphify, architecture and showroom state refreshed.");
}

if (import.meta.main) {
  const event = await readHookEvent();
  if (event) {
    await handlePostToolUse(event, getHarnessPaths().harnessRoot);
  }
}
