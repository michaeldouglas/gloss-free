import path from "node:path";
import { existsSync, statSync } from "node:fs";
import { mkdir, readdir, readFile, stat, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { getHarnessPaths } from "./paths.ts";

type JsonObject = Record<string, any>;

export interface FeaturePaths {
  REPO_ROOT: string;
  CURRENT_BRANCH: string;
  FEATURE_DIR: string;
  FEATURE_SPEC: string;
  IMPL_PLAN: string;
  TASKS: string;
  RESEARCH: string;
  DATA_MODEL: string;
  QUICKSTART: string;
  CONTRACTS_DIR: string;
}

const isRecord = (value: unknown): value is Record<string, any> => value !== null && typeof value === "object" && !Array.isArray(value);

export function findSpecifyRoot(startDir = process.cwd()): string | null {
  let current = path.resolve(startDir);
  while (true) {
    try { if (statSync(path.join(current, ".specify")).isDirectory()) return current; } catch { /* continue upward */ }
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

export function resolveSpecifyInitDir(returnNullOnError = false): string | null {
  const requested = process.env.SPECIFY_INIT_DIR ?? "";
  const resolved = path.resolve(requested);
  const isDirectory = (() => { try { return statSync(resolved).isDirectory(); } catch { return false; } })();
  const problem = !isDirectory
    ? `ERROR: SPECIFY_INIT_DIR does not point to an existing directory: ${requested}`
    : !existsSync(path.join(resolved, ".specify"))
      ? `ERROR: SPECIFY_INIT_DIR is not a Spec Kit project (no .specify/ directory): ${resolved}`
      : null;
  if (problem) {
    process.stderr.write(`${problem}\n`);
    if (returnNullOnError) return null;
    throw new Error(problem);
  }
  return resolved;
}

export function getRepoRoot(scriptDir = process.cwd(), returnNullOnError = false): string | null {
  if (process.env.SPECIFY_INIT_DIR) return resolveSpecifyInitDir(returnNullOnError);
  return findSpecifyRoot() ?? getHarnessPaths(scriptDir).harnessRoot;
}

export function getCurrentBranch(): string {
  return process.env.SPECIFY_FEATURE ?? "";
}

async function saveFeatureJson(repoRoot: string, featureDirectory: string): Promise<void> {
  let stored = featureDirectory;
  const prefix = `${repoRoot}${path.sep}`;
  const compareStored = process.platform === "win32" ? stored.toLowerCase() : stored;
  const comparePrefix = process.platform === "win32" ? prefix.toLowerCase() : prefix;
  if (compareStored.startsWith(comparePrefix)) stored = stored.slice(prefix.length);
  stored = stored.replaceAll(path.sep, "/");
  const featureJson = path.join(repoRoot, ".specify", "feature.json");
  try {
    const current = JSON.parse(await readFile(featureJson, "utf8"));
    if (current.feature_directory === stored) return;
  } catch {
    // Corrupt or missing state is repaired below.
  }
  await mkdir(path.dirname(featureJson), { recursive: true });
  await writeFile(featureJson, `${JSON.stringify({ feature_directory: stored })}\n`, "utf8");
}

export async function getFeaturePaths(options: { noPersist?: boolean; returnNullOnError?: boolean } = {}): Promise<FeaturePaths | null> {
  const repoRoot = getRepoRoot(path.dirname(fileURLToPath(import.meta.url)), options.returnNullOnError);
  if (!repoRoot) return null;
  let featureDir = "";
  let currentBranch = getCurrentBranch();
  if (process.env.SPECIFY_FEATURE_DIRECTORY) {
    const configured = process.env.SPECIFY_FEATURE_DIRECTORY;
    featureDir = path.isAbsolute(configured) ? configured : path.resolve(repoRoot, configured);
    if (!options.noPersist) await saveFeatureJson(repoRoot, configured);
  } else {
    const featureJson = path.join(repoRoot, ".specify", "feature.json");
    try {
      const config = JSON.parse(await readFile(featureJson, "utf8"));
      if (typeof config.feature_directory !== "string" || !config.feature_directory) throw new Error("missing feature_directory");
      featureDir = path.isAbsolute(config.feature_directory) ? config.feature_directory : path.resolve(repoRoot, config.feature_directory);
    } catch {
      process.stderr.write("ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or ensure .specify/feature.json contains feature_directory.\n");
      if (options.returnNullOnError) return null;
      throw new Error("Feature directory not found.");
    }
  }
  if (!currentBranch) currentBranch = path.basename(featureDir.replace(/[\\/]+$/, ""));
  return {
    REPO_ROOT: repoRoot,
    CURRENT_BRANCH: currentBranch,
    FEATURE_DIR: featureDir,
    FEATURE_SPEC: path.join(featureDir, "spec.md"),
    IMPL_PLAN: path.join(featureDir, "plan.md"),
    TASKS: path.join(featureDir, "tasks.md"),
    RESEARCH: path.join(featureDir, "research.md"),
    DATA_MODEL: path.join(featureDir, "data-model.md"),
    QUICKSTART: path.join(featureDir, "quickstart.md"),
    CONTRACTS_DIR: path.join(featureDir, "contracts"),
  };
}

function priority(value: unknown): number {
  if (typeof value === "boolean") return 10;
  if (typeof value === "string") {
    const normalized = value.trim();
    if (!/^[+-]?[0-9]+(?:_[0-9]+)*$/.test(normalized)) return 10;
    value = normalized.replaceAll("_", "");
  }
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed >= 1 ? parsed : 10;
}

async function getSortedIds(directory: string, kind: "presets" | "extensions", loosePresetFallback = false): Promise<string[]> {
  const registryFile = path.join(directory, ".registry");
  let entries: Array<{ id: string; priority: number }> = [];
  const fileExists = await Bun.file(registryFile).exists();
  if (fileExists) {
    let registry: unknown;
    try { registry = JSON.parse(await readFile(registryFile, "utf8")); }
    catch (error) {
      if (kind === "extensions") throw new Error(`Invalid extension registry ${registryFile}: ${String(error)}`);
      registry = null;
    }
    const sectionName = kind;
    if (isRecord(registry) && (registry[sectionName] === undefined || isRecord(registry[sectionName]))) {
      const section = isRecord(registry[sectionName]) ? registry[sectionName] as Record<string, any> : {};
      const registered = new Set(Object.keys(section));
      entries = Object.entries(section)
        .filter(([id, value]) => /^[a-z0-9-]+$/.test(id) && isRecord(value) && value.enabled !== false)
        .map(([id, value]) => ({ id, priority: priority(value.priority) }));
      if (kind === "extensions") {
        for (const entry of await readdir(directory, { withFileTypes: true }).catch(() => [])) {
          if (entry.isDirectory() && /^[a-z0-9-]+$/.test(entry.name) && !registered.has(entry.name)) entries.push({ id: entry.name, priority: 10 });
        }
      }
      return entries.sort((a, b) => a.priority - b.priority || a.id.localeCompare(b.id)).map((entry) => entry.id);
    }
    if (kind === "extensions") throw new Error(`Invalid extension registry ${registryFile}: root must be a mapping`);
  }
  const dirs = (await readdir(directory, { withFileTypes: true }).catch(() => []))
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith(".") && ((kind === "presets" && loosePresetFallback) || /^[a-z0-9-]+$/.test(entry.name)))
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b));
  return dirs;
}

export async function resolveTemplate(templateName: string, repoRoot: string): Promise<string | null> {
  if (!/^[a-z0-9-]+$/.test(templateName)) return null;
  const base = path.join(repoRoot, ".specify", "templates");
  const candidates: string[] = [path.join(base, "overrides", `${templateName}.md`)];
  const presetsDir = path.join(repoRoot, ".specify", "presets");
  for (const id of await getSortedIds(presetsDir, "presets", true)) candidates.push(path.join(presetsDir, id, "templates", `${templateName}.md`), path.join(presetsDir, id, `${templateName}.md`));
  const extensionsDir = path.join(repoRoot, ".specify", "extensions");
  for (const id of await getSortedIds(extensionsDir, "extensions")) candidates.push(path.join(extensionsDir, id, "templates", `${templateName}.md`), path.join(extensionsDir, id, `${templateName}.md`));
  candidates.push(path.join(base, `${templateName}.md`));
  for (const candidate of candidates) if (await Bun.file(candidate).exists()) return candidate;
  return null;
}

type TemplateLayer = { file: string; strategy: string };
async function presetLayers(repoRoot: string, templateName: string): Promise<TemplateLayer[]> {
  const presetsDir = path.join(repoRoot, ".specify", "presets");
  const layers: TemplateLayer[] = [];
  for (const id of await getSortedIds(presetsDir, "presets")) {
    const manifestPath = path.join(presetsDir, id, "preset.yml");
    let declared = false;
    let strategy = "replace";
    let manifestFile = "";
    if (await Bun.file(manifestPath).exists()) {
      let manifest: unknown;
      try { manifest = Bun.YAML.parse(await readFile(manifestPath, "utf8")); }
      catch (error) { throw new Error(`Invalid preset manifest ${manifestPath}: ${String(error)}`); }
      if (!isRecord(manifest) || !isRecord(manifest.provides) || !Array.isArray(manifest.provides.templates) || manifest.provides.templates.length === 0) throw new Error(`Invalid preset manifest ${manifestPath}`);
      for (const item of manifest.provides.templates) {
        if (!isRecord(item) || typeof item.type !== "string" || typeof item.name !== "string" || typeof item.file !== "string") throw new Error(`Invalid preset manifest ${manifestPath}`);
        const type = item.type;
        const itemStrategy = typeof item.strategy === "string" ? item.strategy.toLowerCase() : "replace";
        if (!["template", "command", "script"].includes(type) || !["replace", "prepend", "append", "wrap"].includes(itemStrategy) || (type === "script" && !["replace", "wrap"].includes(itemStrategy))) throw new Error(`Invalid preset manifest ${manifestPath}`);
      }
      const found = manifest.provides.templates.find((item: JsonObject) => item.name === templateName && (item.type ?? "template") === "template") as JsonObject | undefined;
      if (found) {
        declared = true;
        strategy = typeof found.strategy === "string" ? found.strategy.toLowerCase() : "replace";
        manifestFile = found.file;
      }
    }
    let candidate = "";
    if (manifestFile && !path.isAbsolute(manifestFile) && !/(^|[/\\])\.\.([/\\]|$)/.test(manifestFile)) {
      const fromManifest = path.join(presetsDir, id, manifestFile);
      if (await Bun.file(fromManifest).exists()) candidate = fromManifest;
    }
    if (!candidate && !declared) {
      const conventional = [path.join(presetsDir, id, "templates", `${templateName}.md`), path.join(presetsDir, id, `${templateName}.md`)];
      for (const file of conventional) if (await Bun.file(file).exists()) { candidate = file; break; }
    }
    if (candidate) {
      layers.push({ file: candidate, strategy });
      if (strategy === "replace") break;
    }
  }
  return layers;
}

export async function resolveTemplateContent(templateName: string, repoRoot: string): Promise<string | null> {
  if (!/^[a-z0-9-]+$/.test(templateName)) return null;
  const base = path.join(repoRoot, ".specify", "templates");
  const override = path.join(base, "overrides", `${templateName}.md`);
  if (await Bun.file(override).exists()) return readFile(override, "utf8");
  const layers = await presetLayers(repoRoot, templateName);
  let effectiveBaseFound = layers.some((layer) => layer.strategy === "replace");
  if (!effectiveBaseFound) {
    const extDir = path.join(repoRoot, ".specify", "extensions");
    for (const id of await getSortedIds(extDir, "extensions")) {
      const candidates = [path.join(extDir, id, "templates", `${templateName}.md`), path.join(extDir, id, `${templateName}.md`)];
      for (const candidate of candidates) {
        if (await Bun.file(candidate).exists()) {
          layers.push({ file: candidate, strategy: "replace" });
          effectiveBaseFound = true;
          break;
        }
      }
      if (effectiveBaseFound) break;
    }
  }
  const core = path.join(base, `${templateName}.md`);
  if (!effectiveBaseFound && await Bun.file(core).exists()) layers.push({ file: core, strategy: "replace" });
  if (!layers.length) return null;
  if (layers[0].strategy === "replace") return readFile(layers[0].file, "utf8");
  const baseIndex = layers.findIndex((layer) => layer.strategy === "replace");
  if (baseIndex < 0) throw new Error(`Template '${templateName}' has composing layers but no replace base`);
  let content = await readFile(layers[baseIndex].file, "utf8");
  for (let index = baseIndex - 1; index >= 0; index -= 1) {
    const layer = layers[index];
    const layerContent = await readFile(layer.file, "utf8");
    switch (layer.strategy) {
      case "replace": content = layerContent; break;
      case "prepend": content = `${layerContent}\n\n${content}`; break;
      case "append": content = `${content}\n\n${layerContent}`; break;
      case "wrap":
        if (!layerContent.includes("{CORE_TEMPLATE}")) throw new Error("Wrap strategy missing {CORE_TEMPLATE} placeholder");
        content = layerContent.replaceAll("{CORE_TEMPLATE}", content);
        break;
      default: throw new Error(`Unknown strategy: ${layer.strategy}`);
    }
  }
  return content;
}

export async function hasEntries(directory: string): Promise<boolean> {
  return (await readdir(directory).catch(() => [])).length > 0;
}

export async function featurePathsForScript(): Promise<FeaturePaths | null> {
  return getFeaturePaths({ returnNullOnError: true });
}
