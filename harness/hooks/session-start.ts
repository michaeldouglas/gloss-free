import path from "node:path";
import { fileURLToPath } from "node:url";
import { runCommand } from "../lib/process.ts";
import { emitContext } from "../lib/hook-protocol.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const branchResult = await runCommand("git", ["branch", "--show-current"], { cwd: root, quiet: true }).catch(() => null);
const branch = branchResult?.stdout.trim() ?? "";
const graph = await Bun.file(path.join(root, "graphify-out", "graph.json")).exists();
const appGraph = ["..", "app", "graphify-out"].join("/");
const duplicateGraph = await Bun.file(path.resolve(root, "..", "app", "graphify-out")).exists();
const constitution = await Bun.file(path.join(root, ".specify", "memory", "constitution.md")).exists();
let feature: string | null = null;
try {
  const config = await Bun.file(path.join(root, ".specify", "feature.json")).json() as { feature_directory?: string };
  feature = config.feature_directory ?? null;
} catch {
  feature = null;
}
const lines = [
  `Harness context: repository root is '${root}'.`,
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
