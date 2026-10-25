import path from "node:path";
import { mkdir, readdir } from "node:fs/promises";
import { runCommand, type CommandResult } from "../lib/process.ts";
import { createHarnessPaths, getHarnessPaths } from "../lib/paths.ts";

type RefreshRecord = {
  schema_version: string;
  dataset: string;
  executed_at: string;
  status: "pending" | "completed" | "completed_with_warnings" | "failed";
  candidates: string[];
  outputs: Array<{ candidate: string; html: string; result_tail: string[] }>;
  warnings?: string[];
  reason?: string;
};
export type ArchitectureRunner = (command: string, args: string[], options?: { cwd?: string; quiet?: boolean }) => Promise<CommandResult>;

function parseArchifySummary(stdout: string): Record<string, any> | null {
  for (const line of stdout.trim().split(/\r?\n/).reverse()) {
    if (!line.trim().startsWith("{")) continue;
    try {
      const value = JSON.parse(line) as Record<string, any>;
      if (value && typeof value === "object") return value;
    } catch {
      // Archify may prefix diagnostics before its final JSON summary.
    }
  }
  return null;
}

function isBrowserOnlyFailure(result: CommandResult): boolean {
  const summary = parseArchifySummary(result.stdout);
  const gates = summary?.gates;
  return result.exitCode !== 0
    && gates?.validate === "pass"
    && gates?.deliver === "pass"
    && gates?.check === "pass"
    && gates?.["browser-check"] === "fail";
}

export async function refreshArchitecture(harnessRoot: string, dataset = "unknown", run: ArchitectureRunner = runCommand): Promise<{ exitCode: number; record: RefreshRecord }> {
  const paths = createHarnessPaths(harnessRoot);
  const architectureRoot = paths.architectureRoot;
  const sourceRoot = paths.architectureSourceRoot;
  const htmlRoot = paths.architectureHtmlRoot;
  const statusPath = path.join(architectureRoot, "architecture-refresh.json");
  await Promise.all([mkdir(sourceRoot, { recursive: true }), mkdir(htmlRoot, { recursive: true })]);
  const record: RefreshRecord = {
    schema_version: "architecture-refresh.v1",
    dataset,
    executed_at: new Date().toISOString(),
    status: "pending",
    candidates: [],
    outputs: [],
  };
  const saveStatus = async () => { await Bun.write(statusPath, `${JSON.stringify(record, null, 2)}\n`); };
  try {
    record.candidates = (await readdir(sourceRoot, { withFileTypes: true }))
      .filter((entry) => entry.isFile() && entry.name.endsWith(".architecture.json"))
      .map((entry) => entry.name)
      .sort();
    if (!record.candidates.length) {
      record.reason = "Nenhum candidato Archify em artifacts/architecture/source.";
      await saveStatus();
      return { exitCode: 0, record };
    }
    const archifyCli = path.join(harnessRoot, ".agents", "skills", "archify", "bin", "archify.mjs");
    if (!(await Bun.file(archifyCli).exists())) {
      record.reason = "A CLI local do Archify não está disponível.";
      await saveStatus();
      return { exitCode: 0, record };
    }
    const repository = await run("git", ["-C", harnessRoot, "rev-parse", "--show-toplevel"], { quiet: true });
    if (repository.exitCode !== 0 || !repository.stdout.trim()) throw new Error("Não foi possível localizar a raiz Git do repositório.");
    const repositoryRoot = repository.stdout.trim();
    let hadWarnings = false;
    for (const candidateName of record.candidates) {
      const slug = candidateName.replace(/\.architecture\.json$/, "");
      const candidatePath = path.join(sourceRoot, candidateName);
      const outputPath = path.join(htmlRoot, `${slug}.html`);
      const result = await run("bun", ["run", archifyCli, "finalize", "architecture", candidatePath, outputPath, "--repo-root", repositoryRoot, "--quality", "showcase", "--json"], { cwd: harnessRoot, quiet: true });
      const tail = `${result.stdout}\n${result.stderr}`.trim().split(/\r?\n/).slice(-5);
      if (isBrowserOnlyFailure(result)) {
        hadWarnings = true;
        record.warnings ??= [];
        record.warnings.push(`${candidateName}: validação, entrega e checagem passaram; browser-check falhou por indisponibilidade do Chrome/DevTools.`);
        record.outputs.push({ candidate: candidateName, html: outputPath, result_tail: tail });
        continue;
      }
      if (result.exitCode !== 0) throw new Error(`Archify falhou para ${candidateName} com código ${result.exitCode}.`);
      record.outputs.push({ candidate: candidateName, html: outputPath, result_tail: tail });
    }
    record.status = hadWarnings ? "completed_with_warnings" : "completed";
    if (hadWarnings) record.reason = "Archify gerou e validou os diagramas, mas a evidência browser-check não pôde ser concluída neste ambiente.";
    await saveStatus();
    return { exitCode: 0, record };
  } catch (error) {
    record.status = "failed";
    record.reason = error instanceof Error ? error.message : String(error);
    await saveStatus();
    return { exitCode: 1, record };
  }
}

if (import.meta.main) {
  const harnessRoot = getHarnessPaths().harnessRoot;
  let dataset = "unknown";
  const args = process.argv.slice(2);
  for (let index = 0; index < args.length; index += 1) {
    if (args[index] === "--dataset" || args[index] === "-Dataset") dataset = args[++index] ?? "unknown";
    else if (args[index] === "--help" || args[index] === "-h") {
      process.stdout.write("Usage: bun run core/scripts/refresh-architecture.ts [--dataset name]\n");
      process.exit(0);
    } else throw new Error(`Opção desconhecida: ${args[index]}`);
  }
  const result = await refreshArchitecture(harnessRoot, dataset);
  if (result.exitCode !== 0) process.stderr.write(`${result.record.reason ?? "Archify refresh failed."}\n`);
  process.exitCode = result.exitCode;
}
