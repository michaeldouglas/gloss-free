import path from "node:path";
import { createHash } from "node:crypto";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { getHarnessPaths } from "../lib/paths.ts";

type JsonObject = Record<string, any>;

const paths = getHarnessPaths();
const releaseRoot = path.join(paths.reportsRoot, "publications");
const knownSeverities = ["CRITICAL", "ERROR", "WARNING", "INFO"] as const;

function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

async function readJson(file: string): Promise<JsonObject> {
  const value: unknown = JSON.parse(await readFile(file, "utf8"));
  if (!isObject(value)) throw new Error(`${file} precisa conter um objeto JSON.`);
  return value;
}

async function sha256(file: string): Promise<string> {
  return createHash("sha256").update(await readFile(file)).digest("hex");
}

function repoRelative(file: string): string {
  const relative = path.relative(paths.repositoryRoot, file).split(path.sep).join("/");
  if (relative.startsWith("../") || path.isAbsolute(relative)) throw new Error(`A fonte está fora do repositório: ${file}`);
  return relative;
}

function pickNumbers(source: JsonObject, keys: readonly string[]): JsonObject {
  return Object.fromEntries(keys.filter((key) => Number.isFinite(source?.[key])).map((key) => [key, source[key]]));
}

async function collectSummaryFiles(): Promise<string[]> {
  const files: string[] = [];
  for (const entry of await readdir(paths.metadataValidationRoot, { withFileTypes: true }).catch(() => [])) {
    if (!entry.isDirectory()) continue;
    const candidate = path.join(paths.metadataValidationRoot, entry.name, "reports", "metadata_summary.json");
    if (await Bun.file(candidate).exists()) files.push(candidate);
  }
  const legacy = path.join(paths.metadataValidationRoot, "reports", "metadata_summary.json");
  if (await Bun.file(legacy).exists()) files.push(legacy);
  return files;
}

async function sanitizeSummary(file: string): Promise<JsonObject> {
  const source = await readJson(file);
  if (source.schema_version !== "dataset-validation-summary.v1") throw new Error(`${file} não usa dataset-validation-summary.v1.`);
  if (typeof source.dataset !== "string" || !source.dataset.trim()) throw new Error(`${file} não informa o dataset.`);
  if (!isObject(source.counts) || !isObject(source.counts.by_severity)) throw new Error(`${file} não contém counts.by_severity.`);
  const counts = pickNumbers(source.counts, ["annotations", "exceptions", "physical_videos", "manifest_rows", "issues"]);
  counts.by_severity = pickNumbers(source.counts.by_severity, knownSeverities);
  if (isObject(source.counts.provenance)) {
    counts.provenance = pickNumbers(source.counts.provenance, ["error_rows", "error_in_annotations", "error_with_physical_file", "error_missing_file"]);
  }

  const key = isObject(source.key_reconciliation) ? source.key_reconciliation : {};
  const keyReconciliation: JsonObject = {
    ...pickNumbers(key, ["csv_records", "filesystem_records", "matched", "missing", "extra"]),
  };
  if (typeof key.filesystem_key_column === "string") keyReconciliation.filesystem_key_column = key.filesystem_key_column;

  return {
    schema_version: "dataset-validation-summary.v1",
    dataset: source.dataset,
    generated_at_utc: typeof source.generated_at_utc === "string" ? source.generated_at_utc : null,
    decision: source.decision,
    counts,
    key_reconciliation: keyReconciliation,
    source_record: {
      path: repoRelative(file),
      sha256: await sha256(file),
    },
  };
}

function sanitizedExecution(latest: JsonObject, reportHash: string): JsonObject {
  const technical = latest.technical_summary ?? {};
  const quality = latest.quality_counts ?? {};
  return {
    dataset: latest.dataset,
    executed_at: latest.executed_at,
    decision: latest.decision,
    technical_summary: {
      ...pickNumbers(technical, [
        "videos_seen", "videos_ok", "videos_partial", "videos_with_probe_error",
        "width_matches", "height_matches", "fps_rate_matches", "fps_frame_count_matches",
        "fps_none_matches", "fps_inconclusive", "fps_tolerance",
      ]),
      ...(isObject(technical.fps_hypothesis_counts) ? { fps_hypothesis_counts: technical.fps_hypothesis_counts } : {}),
      ...(typeof technical.dataset_fps_interpretation === "string" ? { dataset_fps_interpretation: technical.dataset_fps_interpretation } : {}),
    },
    quality_counts: pickNumbers(quality, knownSeverities),
    source_record: {
      path: "harness/artifacts/reports/latest.json",
      sha256: reportHash,
    },
  };
}

function readOptions(argv: string[]): { id: string; title: string; summary: string } {
  const values: Record<string, string> = {};
  for (let index = 2; index < argv.length; index += 1) {
    const key = argv[index];
    if (key === "--help" || key === "-h") {
      process.stdout.write("Usage: bun run core/scripts/prepare-presentation-release.ts --id YYYY-MM-DD-slug --title <title> --summary <summary>\n");
      process.exit(0);
    }
    if (!["--id", "--title", "--summary"].includes(key)) throw new Error(`Opção desconhecida: ${key}`);
    values[key.slice(2)] = argv[++index] ?? "";
  }
  const { id = "", title = "", summary = "" } = values;
  if (!/^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id)) throw new Error("--id precisa seguir YYYY-MM-DD-slug em minúsculas.");
  const date = id.slice(0, 10);
  if (Number.isNaN(Date.parse(`${date}T00:00:00Z`))) throw new Error(`Data inválida no identificador: ${date}`);
  if (!title.trim()) throw new Error("--title é obrigatório.");
  if (!summary.trim()) throw new Error("--summary é obrigatório.");
  return { id, title: title.trim(), summary: summary.trim() };
}

async function prepareRelease(): Promise<void> {
  const { id, title, summary } = readOptions(process.argv);
  const snapshotPath = path.join(releaseRoot, `${id}.json`);
  const indexPath = path.join(releaseRoot, "index.json");
  if (await Bun.file(snapshotPath).exists()) throw new Error(`A versão ${id} já existe; snapshots publicados são imutáveis.`);

  const latestFile = path.join(paths.reportsRoot, "latest.json");
  const latest = await readJson(latestFile);
  if (latest.schema_version !== "execution-report.v1") throw new Error("latest.json precisa usar execution-report.v1.");

  const summaryFiles = await collectSummaryFiles();
  if (summaryFiles.length === 0) throw new Error(`Nenhum metadata_summary.json encontrado em ${paths.metadataValidationRoot}. Execute a validação no app antes de preparar a versão.`);
  const datasets = await Promise.all(summaryFiles.map(sanitizeSummary));
  const uniqueDatasets = new Set(datasets.map((item) => item.dataset));
  if (uniqueDatasets.size !== datasets.length) throw new Error("Há mais de um metadata_summary.json para o mesmo dataset.");
  if (!uniqueDatasets.has(latest.dataset)) throw new Error(`O dataset ${latest.dataset} de latest.json não tem resumo correspondente.`);

  const specDirectory = path.join(paths.specsRoot, "003-validar-metadados-video");
  const specFile = path.join(specDirectory, "spec.md");
  const tasksFile = path.join(specDirectory, "tasks.md");
  const specText = await readFile(specFile, "utf8");
  const tasksText = await readFile(tasksFile, "utf8");
  const specStatus = specText.match(/^\*\*Status\*\*:\s*(.+)$/m)?.[1]?.trim();
  if (!specStatus) throw new Error("Não foi possível ler o status da feature 003-validar-metadados-video.");
  const taskMarks = [...tasksText.matchAll(/^\s*-\s+\[([ xX])\]/gm)].map((match) => match[1]);
  const completedTasks = taskMarks.filter((mark) => mark.toLowerCase() === "x").length;

  const snapshot: JsonObject = {
    schema_version: "research-presentation-evidence.v1",
    release_id: id,
    release_date: id.slice(0, 10),
    title,
    summary,
    prepared_at_utc: new Date().toISOString(),
    feature_progress: {
      feature_id: "003-validar-metadados-video",
      spec_status: specStatus,
      tasks_complete: completedTasks,
      tasks_total: taskMarks.length,
      sources: [
        { path: repoRelative(specFile), sha256: await sha256(specFile) },
        { path: repoRelative(tasksFile), sha256: await sha256(tasksFile) },
      ],
    },
    datasets: datasets.sort((left, right) => left.dataset.localeCompare(right.dataset)),
    latest_execution: sanitizedExecution(latest, await sha256(latestFile)),
  };

  const snapshotText = `${JSON.stringify(snapshot, null, 2)}\n`;
  if (/(?:[A-Z]:\\|\/workspace\/)/i.test(snapshotText)) throw new Error("O snapshot contém um caminho absoluto; publicação cancelada.");

  let index: JsonObject = { schema_version: "research-presentation-index.v1", latest_release: id, releases: [] };
  if (await Bun.file(indexPath).exists()) {
    index = await readJson(indexPath);
    if (index.schema_version !== "research-presentation-index.v1" || !Array.isArray(index.releases)) throw new Error("artifacts/reports/publications/index.json tem schema inválido.");
  }
  if (index.releases.some((release: JsonObject) => release.id === id)) throw new Error(`A versão ${id} já está no catálogo.`);
  index.releases.push({ id, release_date: snapshot.release_date, title, summary, snapshot: `${id}.json` });
  index.releases.sort((left: JsonObject, right: JsonObject) => right.release_date.localeCompare(left.release_date) || right.id.localeCompare(left.id));
  index.latest_release = index.releases[0].id;

  await mkdir(releaseRoot, { recursive: true });
  await writeFile(snapshotPath, snapshotText, "utf8");
  await writeFile(indexPath, `${JSON.stringify(index, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify({ release_id: id, snapshot: repoRelative(snapshotPath), latest_release: index.latest_release, datasets: datasets.length, feature_tasks: `${completedTasks}/${taskMarks.length}`, spec_status: specStatus })}\n`);
}

if (import.meta.main) {
  prepareRelease().catch((error) => {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
  });
}
