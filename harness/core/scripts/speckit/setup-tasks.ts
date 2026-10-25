import path from "node:path";
import { getFeaturePaths, hasEntries, resolveTemplate, resolveTemplateContent } from "../../lib/spec-kit.ts";
import { fail, normalizeOption, printJson } from "./cli.ts";

let json = false;
let help = false;
if (process.argv.slice(2).some((arg) => ["help", "h"].includes(normalizeOption(arg)))) {
  process.stdout.write("Usage: bun run core/scripts/speckit/setup-tasks.ts [--json]\n");
  process.exit(0);
}
for (const arg of process.argv.slice(2)) {
  const key = normalizeOption(arg);
  if (key === "help" || key === "h") help = true;
  else if (key === "json") json = true;
  else if (arg.startsWith("-")) fail(`ERROR: Unknown option '${arg}'`);
  else fail(`ERROR: Unknown option '${arg}'`);
}
if (help) { process.stdout.write("Usage: bun run core/scripts/speckit/setup-tasks.ts [--json]\n"); process.exit(0); }
const paths = await getFeaturePaths({ returnNullOnError: true });
if (!paths) fail("ERROR: Failed to resolve feature paths");
if (!(await Bun.file(paths.IMPL_PLAN).exists())) fail(`ERROR: plan.md not found in ${paths.FEATURE_DIR}\nRun $speckit-plan first to create the implementation plan.`);
if (!(await Bun.file(paths.FEATURE_SPEC).exists())) fail(`ERROR: spec.md not found in ${paths.FEATURE_DIR}\nRun $speckit-specify first to create the feature structure.`);
const docs: string[] = [];
if (await Bun.file(paths.RESEARCH).exists()) docs.push("research.md");
if (await Bun.file(paths.DATA_MODEL).exists()) docs.push("data-model.md");
if (await hasEntries(paths.CONTRACTS_DIR)) docs.push("contracts/");
if (await Bun.file(paths.QUICKSTART).exists()) docs.push("quickstart.md");
const templatePath = await resolveTemplate("tasks-template", paths.REPO_ROOT);
const templateContent = await resolveTemplateContent("tasks-template", paths.REPO_ROOT);
if (templateContent === null) fail(`ERROR: Could not resolve required tasks-template from the template override stack for ${paths.REPO_ROOT}\nTemplate 'tasks-template' was not found in any supported location (overrides, presets, extensions, or shared core). Add an override at .specify/templates/overrides/tasks-template.md, or run 'specify init' / reinstall shared infra to restore the core .specify/templates/tasks-template.md template.`);
const resolvedPath = templatePath && await Bun.file(templatePath).exists() ? path.resolve(templatePath) : "";
if (json) printJson({ FEATURE_DIR: paths.FEATURE_DIR, AVAILABLE_DOCS: docs, TASKS_TEMPLATE: resolvedPath, TASKS_TEMPLATE_CONTENT: templateContent });
else process.stdout.write(`FEATURE_DIR: ${paths.FEATURE_DIR}\nTASKS_TEMPLATE: ${resolvedPath || "not found"}\nAVAILABLE_DOCS:\n${docs.map((item) => `  [OK] ${item}`).join("\n")}\n`);
