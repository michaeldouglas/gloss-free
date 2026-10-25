import path from "node:path";
import { readdir, mkdir, writeFile, stat } from "node:fs/promises";
import { getRepoRoot, resolveTemplateContent } from "../../lib/spec-kit.ts";
import { fail, normalizeOption, printJson } from "./cli.ts";

const flags = { json: false, allowExisting: false, dryRun: false, timestamp: false };
let shortName = "";
let explicitNumber: string | undefined;
const description: string[] = [];
const args = process.argv.slice(2);
for (let index = 0; index < args.length; index += 1) {
  const arg = args[index];
  const key = normalizeOption(arg);
  if (key === "help" || key === "h") {
    process.stdout.write("Usage: bun run scripts/speckit/create-new-feature.ts [--json] [--dry-run] [--allow-existing-branch] [--short-name name] [--number N] [--timestamp] <description>\n");
    process.exit(0);
  }
  if (key === "json") flags.json = true;
  else if (key === "allowexistingbranch") flags.allowExisting = true;
  else if (key === "dryrun") flags.dryRun = true;
  else if (key === "timestamp") flags.timestamp = true;
  else if (key === "shortname") shortName = args[++index] ?? "";
  else if (key === "number") explicitNumber = args[++index] ?? "";
  else if (arg.startsWith("-")) fail(`ERROR: Unknown option '${arg}'`);
  else description.push(arg);
}
const featureDesc = description.join(" ").trim();
if (!featureDesc) fail("Error: Feature description cannot be empty or contain only whitespace");
const root = getRepoRoot();
if (!root) process.exit(1);
const specsDir = path.join(root, "specs");
const maxBranchLength = 244;
const cleanBranch = (name: string) => name.toLowerCase().replace(/[^a-z0-9]/g, "-").replace(/-{2,}/g, "-").replace(/^-|-$/g, "");
const fitBranch = (number: string, suffix: string) => {
  const combined = `${number}-${suffix}`;
  if (combined.length <= maxBranchLength) return combined;
  const fitted = suffix.slice(0, maxBranchLength - number.length - 1).replace(/-$/, "");
  return `${number}-${fitted}`;
};
const stopWords = new Set("i a an the to for of in on at by with from is are was were be been being have has had do does did will would should could can may might must shall this that these those my your our their want need add get set".split(" "));
function branchFromDescription(value: string): string {
  const words = value.toLowerCase().replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter(Boolean);
  const meaningful = words.filter((word) => !stopWords.has(word) && (word.length >= 3 || new RegExp(`\\b${word.toUpperCase()}\\b`).test(value)));
  if (meaningful.length) return meaningful.slice(0, meaningful.length === 4 ? 4 : 3).join("-");
  return cleanBranch(value).split("-").filter(Boolean).slice(0, 3).join("-");
}
async function specDirs(): Promise<string[]> {
  return (await readdir(specsDir, { withFileTypes: true }).catch(() => [])).filter((entry) => entry.isDirectory()).map((entry) => entry.name);
}
async function highestNumber(): Promise<bigint> {
  let highest = 0n;
  for (const name of await specDirs()) {
    const match = /^(\d{3,})-/.exec(name);
    if (!match || /^\d{8}-\d{6}-/.test(name)) continue;
    const value = BigInt(match[1]);
    if (value > highest) highest = value;
  }
  return highest;
}
const prefixInUse = async (number: string) => (await specDirs()).some((name) => name.startsWith(`${number}-`));
const numberFormat = (value: bigint) => value.toString().padStart(3, "0");
const pathExists = async (file: string) => { try { await stat(file); return true; } catch { return false; } };
let suffix = shortName ? cleanBranch(shortName) : branchFromDescription(featureDesc);
let number = "";
const hasNumber = explicitNumber !== undefined && explicitNumber !== "";
if (flags.timestamp && hasNumber) {
  process.stderr.write("[specify] Warning: -Number is ignored when -Timestamp is used\n");
  explicitNumber = "";
}
if (flags.timestamp) {
  const now = new Date();
  const part = (value: number) => String(value).padStart(2, "0");
  number = `${now.getFullYear()}${part(now.getMonth() + 1)}${part(now.getDate())}-${part(now.getHours())}${part(now.getMinutes())}${part(now.getSeconds())}`;
} else {
  let resolved: bigint;
  if (!hasNumber) resolved = await highestNumber() + 1n;
  else {
    if (!/^\d+$/.test(explicitNumber!)) fail(`Error: -Number must be an unsigned integer, got '${explicitNumber}'`);
    resolved = BigInt(explicitNumber!);
    if (resolved > 9223372036854775807n) fail(`Error: -Number must be between 0 and 9223372036854775807, got '${explicitNumber}'`);
  }
  number = numberFormat(resolved);
  if (hasNumber && await prefixInUse(number)) {
    const requested = number;
    const highest = await highestNumber();
    if (!flags.allowExisting || !(await pathExists(path.join(specsDir, fitBranch(number, suffix))))) {
      let next = highest;
      do { next += 1n; if (next > 9223372036854775807n) fail("Error: feature number exceeds supported integer range"); number = numberFormat(next); } while (await prefixInUse(number));
      process.stderr.write(`[specify] Warning: -Number ${requested} conflicts with an existing spec directory; using ${number} instead\n`);
    }
  }
}
const originalBranch = `${number}-${suffix}`;
const branchName = fitBranch(number, suffix);
if (branchName !== originalBranch) {
  process.stderr.write(`[specify] Warning: Branch name exceeded GitHub's 244-byte limit\n[specify] Original: ${originalBranch} (${originalBranch.length} bytes)\n[specify] Truncated to: ${branchName} (${branchName.length} bytes)\n`);
}
const featureDir = path.join(specsDir, branchName);
const specFile = path.join(featureDir, "spec.md");
if (!flags.dryRun) {
  if (await pathExists(featureDir) && !flags.allowExisting) fail(`Error: Feature directory '${featureDir}' already exists. Please use a different feature name or specify a different number with -Number.`);
  const needsSpec = !(await Bun.file(specFile).exists());
  const content = needsSpec ? await resolveTemplateContent("spec-template", root) : null;
  await mkdir(featureDir, { recursive: true });
  if (needsSpec) {
    if (content !== null) await writeFile(specFile, content, "utf8");
    else {
      process.stderr.write("Warning: Spec template not found; created empty spec file\n");
      await writeFile(specFile, "", "utf8");
    }
  }
  const relative = path.relative(root, featureDir).replaceAll(path.sep, "/");
  const statePath = path.join(root, ".specify", "feature.json");
  const current = await Bun.file(statePath).json().catch(() => ({})) as { feature_directory?: string };
  if (current.feature_directory !== relative) await writeFile(statePath, `${JSON.stringify({ feature_directory: relative })}\n`, "utf8");
  process.env.SPECIFY_FEATURE = branchName;
  process.env.SPECIFY_FEATURE_DIRECTORY = featureDir;
}
if (flags.json) printJson({ BRANCH_NAME: branchName, SPEC_FILE: specFile, FEATURE_NUM: number, ...(flags.dryRun ? { DRY_RUN: true } : {}) });
else {
  process.stdout.write(`BRANCH_NAME: ${branchName}\nSPEC_FILE: ${specFile}\nFEATURE_NUM: ${number}\n`);
  if (!flags.dryRun) process.stdout.write(`# To persist in your shell: SPECIFY_FEATURE='${branchName}'\n#                           SPECIFY_FEATURE_DIRECTORY='${featureDir}'\n`);
}
