import { getRepoRoot, resolveTemplateContent } from "../../lib/spec-kit.ts";
import { fail, normalizeOption, printJson } from "./cli.ts";

let templateName = "";
let json = false;
for (const arg of process.argv.slice(2)) {
  const key = normalizeOption(arg);
  if (key === "help" || key === "h") {
    process.stdout.write("Usage: bun run scripts/speckit/resolve-template.ts <template-name> [--json]\n");
    process.exit(0);
  }
  if (key === "json") json = true;
  else if (arg.startsWith("-")) fail(`ERROR: Unknown option '${arg}'`);
  else if (!templateName) templateName = arg;
  else fail(`ERROR: Unexpected argument '${arg}'`);
}
if (!templateName) fail("ERROR: Template name is required");
const root = getRepoRoot();
if (!root) process.exit(1);
const content = await resolveTemplateContent(templateName, root);
if (content === null) fail(`ERROR: Could not resolve required ${templateName} from the template override stack for ${root}`);
if (json) printJson({ TEMPLATE_NAME: templateName, TEMPLATE_CONTENT: content });
else process.stdout.write(content);
