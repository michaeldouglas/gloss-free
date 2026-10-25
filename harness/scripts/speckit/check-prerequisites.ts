import path from "node:path";
import { stat } from "node:fs/promises";
import { getFeaturePaths, hasEntries, resolveTemplateContent } from "../../lib/spec-kit.ts";
import { fail, normalizeOption, printJson } from "./cli.ts";

const options = new Set<string>();
let template = "";
for (let index = 2; index < process.argv.length; index += 1) {
  const key = normalizeOption(process.argv[index]);
  if (key === "help" || key === "h") {
    process.stdout.write("Usage: bun run scripts/speckit/check-prerequisites.ts [--json] [--require-tasks] [--include-tasks] [--paths-only] [--template name]\n");
    process.exit(0);
  }
  if (key === "template") template = process.argv[++index] ?? "";
  else if (["json", "requiretasks", "requirespec", "includetasks", "pathsonly"].includes(key)) options.add(key);
  else fail(`ERROR: Unknown option '${process.argv[index]}'`);
}
const paths = await getFeaturePaths({ noPersist: options.has("pathsonly"), returnNullOnError: true });
if (!paths) process.exit(1);
if (options.has("pathsonly")) {
  const result = { REPO_ROOT: paths.REPO_ROOT, BRANCH: paths.CURRENT_BRANCH, FEATURE_DIR: paths.FEATURE_DIR, FEATURE_SPEC: paths.FEATURE_SPEC, IMPL_PLAN: paths.IMPL_PLAN, TASKS: paths.TASKS };
  if (options.has("json")) printJson(result);
  else for (const [key, value] of Object.entries(result)) process.stdout.write(`${key}: ${value}\n`);
  process.exit(0);
}
const exists = async (file: string) => Bun.file(file).exists();
const isDirectory = async (dir: string) => { try { return (await stat(dir)).isDirectory(); } catch { return false; } };
if (!(await isDirectory(paths.FEATURE_DIR))) fail(`ERROR: Feature directory not found: ${paths.FEATURE_DIR}\nRun $speckit-specify first to create the feature structure.`);
if (options.has("requirespec") && !(await exists(paths.FEATURE_SPEC))) fail(`ERROR: spec.md not found in ${paths.FEATURE_DIR}\nRun $speckit-specify first to create the feature structure.`);
if (!(await exists(paths.IMPL_PLAN))) fail(`ERROR: plan.md not found in ${paths.FEATURE_DIR}\nRun $speckit-plan first to create the implementation plan.`);
if (options.has("requiretasks") && !(await exists(paths.TASKS))) fail(`ERROR: tasks.md not found in ${paths.FEATURE_DIR}\nRun $speckit-tasks first to create the task list.`);
const docs: string[] = [];
if (await exists(paths.RESEARCH)) docs.push("research.md");
if (await exists(paths.DATA_MODEL)) docs.push("data-model.md");
if (await hasEntries(paths.CONTRACTS_DIR)) docs.push("contracts/");
if (await exists(paths.QUICKSTART)) docs.push("quickstart.md");
if (options.has("includetasks") && await exists(paths.TASKS)) docs.push("tasks.md");
let templateContent: string | null = null;
if (template) {
  templateContent = await resolveTemplateContent(template, paths.REPO_ROOT);
  if (templateContent === null) fail(`ERROR: Could not resolve required ${template} from the template override stack for ${paths.REPO_ROOT}`);
}
if (options.has("json")) {
  printJson({ FEATURE_DIR: paths.FEATURE_DIR, AVAILABLE_DOCS: docs, ...(template ? { TEMPLATE_CONTENT: templateContent } : {}) });
} else {
  process.stdout.write(`FEATURE_DIR:${paths.FEATURE_DIR}\nAVAILABLE_DOCS:\n`);
  for (const doc of ["research.md", "data-model.md", "contracts/", "quickstart.md", ...(options.has("includetasks") ? ["tasks.md"] : [])]) {
    const file = doc === "contracts/" ? paths.CONTRACTS_DIR : path.join(paths.FEATURE_DIR, doc);
    const available = doc === "contracts/" ? await hasEntries(file) : await exists(file);
    process.stdout.write(`  [${available ? "OK" : "FAIL"}] ${doc}\n`);
  }
}
