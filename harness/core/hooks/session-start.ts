import path from "node:path";
import { runCommand } from "../lib/process.ts";
import { emitContext } from "../lib/hook-protocol.ts";
import { getHarnessPaths } from "../lib/paths.ts";

const paths = getHarnessPaths();
const root = paths.harnessRoot;
const branchResult = await runCommand("git", ["-C", paths.repositoryRoot, "branch", "--show-current"], { cwd: root, quiet: true }).catch(() => null);
const branch = branchResult?.stdout.trim() ?? "";
const graph = await Bun.file(paths.graphifyGraph).exists();
const appGraph = "../app/graphify-out";
const duplicateGraph = await Bun.file(path.join(paths.appRoot, "graphify-out")).exists();
const constitution = await Bun.file(paths.constitutionPath).exists();
let feature: string | null = null;
try {
  const config = await Bun.file(paths.featureStatePath).json() as { feature_directory?: string };
  feature = config.feature_directory ?? null;
} catch {
  feature = null;
}
const lines = [
  `Harness context: harness root is '${paths.harnessRoot}'; repository root is '${paths.repositoryRoot}'.`,
  `Architecture: application is '../app/'; canonical Graphify output is 'graphify-out/'; never create '${appGraph}/'.`,
  "Codebase questions: run 'graphify query <question>' before browsing broadly; after relevant code or artifact edits, keep the canonical graph current with 'graphify update .'.",
  "Spec Kit artifacts live under 'specs/<feature>/'; use the constitution and the feature's spec, plan, and tasks as the workflow source of truth.",
  "Protected branches: make changes only on an existing 'feature/*' branch; do not commit directly to main or develop.",
];
if (branch) lines.push(`Current branch: ${branch}.`);
if (feature) lines.push(`Current Spec Kit feature: ${feature}.`);
if (!graph) lines.push("Graphify status: graphify-out/graph.json is missing; do not assume graph queries are available.");
if (duplicateGraph) lines.push(`WARNING: '${appGraph}/' exists and violates the canonical graph layout.`);
if (!constitution) lines.push("WARNING: .specify/memory/constitution.md is missing.");
emitContext("SessionStart", lines.join("\n"));
