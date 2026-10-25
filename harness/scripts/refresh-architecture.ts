import path from "node:path";
import { fileURLToPath } from "node:url";
import { mkdir, readdir } from "node:fs/promises";
import { runCommand, type CommandResult } from "../lib/process.ts";

type RefreshRecord = {
  schema_version: string;
  dataset: string;
  executed_at: string;
  status: "pending" | "completed" | "failed";
  candidates: string[];
  outputs: Array<{ candidate: string; html: string; result_tail: string[] }>;
  reason?: string;
};
export type ArchitectureRunner = (command: string, args: string[], options?: { cwd?: string; quiet?: boolean }) => Promise<CommandResult>;

export async function refreshArchitecture(harnessRoot: string, dataset = "unknown", run: ArchitectureRunner = runCommand): Promise<{ exitCode: number; record: RefreshRecord }> {
  const architectureRoot = path.join(harnessRoot, "artifacts", "architecture");
  const sourceRoot = path.join(architectureRoot, "source");
  const htmlRoot = path.join(architectureRoot, "html");
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
    for (const candidateName of record.candidates) {
      const slug = candidateName.replace(/\.architecture\.json$/, "");
      const candidatePath = path.join(sourceRoot, candidateName);
      const outputPath = path.join(htmlRoot, `${slug}.html`);
      const result = await run("bun", ["run", archifyCli, "finalize", "architecture", candidatePath, outputPath, "--repo-root", repositoryRoot, "--quality", "showcase", "--json"], { cwd: harnessRoot, quiet: true });
      if (result.exitCode !== 0) throw new Error(`Archify falhou para ${candidateName} com código ${result.exitCode}.`);
      const tail = `${result.stdout}\n${result.stderr}`.trim().split(/\r?\n/).slice(-5);
      record.outputs.push({ candidate: candidateName, html: outputPath, result_tail: tail });
    }
    record.status = "completed";
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
  const harnessRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  let dataset = "unknown";
  const args = process.argv.slice(2);
  for (let index = 0; index < args.length; index += 1) {
    if (args[index] === "--dataset" || args[index] === "-Dataset") dataset = args[++index] ?? "unknown";
    else if (args[index] === "--help" || args[index] === "-h") {
      process.stdout.write("Usage: bun run scripts/refresh-architecture.ts [--dataset name]\n");
      process.exit(0);
    } else throw new Error(`Opção desconhecida: ${args[index]}`);
  }
  const result = await refreshArchitecture(harnessRoot, dataset);
  if (result.exitCode !== 0) process.stderr.write(`${result.record.reason ?? "Archify refresh failed."}\n`);
  process.exitCode = result.exitCode;
}
