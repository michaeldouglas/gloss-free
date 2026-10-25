import path from "node:path";
import { fileURLToPath } from "node:url";
import { readdir, readFile, stat } from "node:fs/promises";
import { runCommand } from "../lib/process.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const mode = process.argv[2] ?? "verify";
if (!["prepare", "verify", "converge"].includes(mode)) {
  process.stderr.write("Usage: bun run scripts/verify-harness.ts [prepare|verify|converge]\n");
  process.exit(2);
}
const failures: string[] = [];
const warnings: string[] = [];
const branch = (await runCommand("git", ["branch", "--show-current"], { cwd: root, quiet: true }).catch(() => null))?.stdout.trim() ?? "";
if (!/^feature\/.+/.test(branch)) failures.push(`Current branch '${branch}' is not a feature/* branch.`);
if (!(await Bun.file(path.join(root, ".specify", "memory", "constitution.md")).exists())) failures.push("Missing .specify/memory/constitution.md.");

let featureDir = "";
const featureFile = path.join(root, ".specify", "feature.json");
if (await Bun.file(featureFile).exists()) {
  try {
    const config = await Bun.file(featureFile).json() as { feature_directory?: string };
    featureDir = config.feature_directory ?? "";
  } catch {
    failures.push("Could not parse .specify/feature.json.");
  }
}
if (!featureDir) {
  const specsRoot = path.join(root, "specs");
  try {
    const candidates = await readdir(specsRoot, { withFileTypes: true });
    const dirs = await Promise.all(candidates.filter((entry) => entry.isDirectory()).map(async (entry) => ({ name: entry.name, modified: (await stat(path.join(specsRoot, entry.name))).mtimeMs })));
    dirs.sort((left, right) => left.modified - right.modified);
    featureDir = dirs.at(-1)?.name ?? "";
  } catch {
    // Missing specs is reported below as an unresolved feature.
  }
}
if (!featureDir) failures.push("Could not resolve the active Spec Kit feature directory.");
else {
  const featurePath = path.isAbsolute(featureDir) ? featureDir : path.resolve(root, featureDir);
  const featureLabel = path.relative(root, featurePath).replaceAll(path.sep, "/");
  for (const name of ["spec.md", "plan.md", "tasks.md"]) {
    if (!(await Bun.file(path.join(featurePath, name)).exists())) failures.push(`Missing ${featureLabel}/${name}.`);
  }
  const markdown: string[] = [];
  const walkMarkdown = async (dir: string): Promise<void> => {
    for (const entry of await readdir(dir, { withFileTypes: true }).catch(() => [])) {
      const file = path.join(dir, entry.name);
      if (entry.isDirectory()) await walkMarkdown(file);
      else if (entry.isFile() && entry.name.endsWith(".md")) markdown.push(await readFile(file, "utf8"));
    }
  };
  await walkMarkdown(featurePath);
  if (/(NEEDS CLARIFICATION|\[FEATURE NAME\]|\[TITLE\]|TODO:?)/i.test(markdown.join("\n"))) failures.push(`Unresolved Spec Kit placeholder detected under ${featureLabel}.`);
  const tasksPath = path.join(featurePath, "tasks.md");
  if (await Bun.file(tasksPath).exists()) {
    const tasks = await Bun.file(tasksPath).text();
    const done = [...tasks.matchAll(/^\s*[-*]\s+\[[xX]\]\s+/gm)].length;
    const open = [...tasks.matchAll(/^\s*[-*]\s+\[\s\]\s+/gm)].length;
    if (done + open === 0) failures.push(`No executable task checkboxes found in ${featureLabel}/tasks.md.`);
    if (open > 0) warnings.push(`${open} open task(s) remain in ${featureLabel}/tasks.md.`);
    if (mode === "verify" && open > 0) failures.push(`Implementation verification requires all tasks to be checked; ${open} remain open.`);
    process.stdout.write(`Spec Kit tasks: ${done} done, ${open} open (${featureLabel}).\n`);
  }
}

const graph = path.join(root, "graphify-out", "graph.json");
if (!(await Bun.file(graph).exists())) failures.push("Missing canonical graphify-out/graph.json.");
const duplicateGraphPath = path.resolve(root, "..", "app", "graphify-out");
try {
  await stat(duplicateGraphPath);
  failures.push("Duplicate application graph detected; use harness/graphify-out/.");
} catch {
  // Not present.
}
const appRoot = path.resolve(root, "..", "app");
if (mode !== "prepare" && await Bun.file(path.join(appRoot, "pyproject.toml")).exists()) {
  const tests = await runCommand("uv", ["run", "python", "-m", "unittest", "discover", "-s", "dataset/tests", "-v"], { cwd: appRoot, quiet: true }).catch(() => null);
  if (!tests || tests.exitCode !== 0) failures.push("Application test suite failed: uv run python -m unittest discover -s dataset/tests -v");
  else process.stdout.write("Application tests: passed.\n");
}
if (mode === "converge" && failures.length === 0) {
  const update = await runCommand("graphify", ["update", "."], { cwd: root, quiet: true }).catch(() => null);
  if (!update || update.exitCode !== 0) failures.push("Graphify update failed during convergence.");
  else process.stdout.write("Graphify: canonical graph refreshed.\n");
}
for (const warning of warnings) process.stderr.write(`Warning: ${warning}\n`);
if (failures.length) {
  process.stderr.write(`${failures.map((failure) => `- ${failure}`).join("\n")}\n`);
  process.exit(1);
}
process.stdout.write(`Harness verification passed (${mode}).\n`);
