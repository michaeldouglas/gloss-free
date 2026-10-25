import { mkdir, writeFile } from "node:fs/promises";
import { getFeaturePaths, resolveTemplateContent } from "../../lib/spec-kit.ts";
import { fail, normalizeOption, printJson } from "./cli.ts";

let json = false;
for (const arg of process.argv.slice(2)) {
  const key = normalizeOption(arg);
  if (key === "help" || key === "h") { process.stdout.write("Usage: bun run core/scripts/speckit/setup-plan.ts [--json]\n"); process.exit(0); }
  if (key === "json") json = true;
  else fail(`ERROR: Unknown option '${arg}'`);
}
const paths = await getFeaturePaths({ returnNullOnError: true });
if (!paths) fail("ERROR: Failed to resolve feature paths");
await mkdir(paths.FEATURE_DIR, { recursive: true });
if (await Bun.file(paths.IMPL_PLAN).exists()) {
  const message = `Plan already exists at ${paths.IMPL_PLAN}, skipping template copy`;
  (json ? process.stderr : process.stdout).write(`${message}\n`);
} else {
  const content = await resolveTemplateContent("plan-template", paths.REPO_ROOT);
  if (content === null) {
    const message = "Warning: Plan template not found";
    (json ? process.stderr : process.stdout).write(`${message}\n`);
    await writeFile(paths.IMPL_PLAN, "", "utf8");
  } else {
    await writeFile(paths.IMPL_PLAN, content, "utf8");
    (json ? process.stderr : process.stdout).write(`Copied plan template to ${paths.IMPL_PLAN}\n`);
  }
}
if (json) printJson({ FEATURE_SPEC: paths.FEATURE_SPEC, IMPL_PLAN: paths.IMPL_PLAN, FEATURE_DIR: paths.FEATURE_DIR, SPECS_DIR: paths.FEATURE_DIR, BRANCH: paths.CURRENT_BRANCH });
else process.stdout.write(`FEATURE_SPEC: ${paths.FEATURE_SPEC}\nIMPL_PLAN: ${paths.IMPL_PLAN}\nFEATURE_DIR: ${paths.FEATURE_DIR}\nSPECS_DIR: ${paths.FEATURE_DIR}\nBRANCH: ${paths.CURRENT_BRANCH}\n`);
