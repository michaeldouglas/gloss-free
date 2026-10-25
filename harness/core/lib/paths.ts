import path from "node:path";
import { existsSync, statSync } from "node:fs";

export interface HarnessPaths {
  harnessRoot: string;
  coreRoot: string;
  hooksRoot: string;
  scriptsRoot: string;
  libRoot: string;
  assetsRoot: string;
  repositoryRoot: string;
  appRoot: string;
  specifyRoot: string;
  specsRoot: string;
  constitutionPath: string;
  featureStatePath: string;
  graphifyRoot: string;
  graphifyGraph: string;
  artifactsRoot: string;
  architectureRoot: string;
  architectureSourceRoot: string;
  architectureHtmlRoot: string;
  reportsRoot: string;
  executionReportsRoot: string;
  docsRoot: string;
  materialsRoot: string;
  metadataValidationRoot: string;
}

function isDirectory(candidate: string): boolean {
  try { return statSync(candidate).isDirectory(); } catch { return false; }
}

function isHarnessRoot(candidate: string): boolean {
  return isDirectory(path.join(candidate, ".specify"))
    && isDirectory(path.join(candidate, ".codex"))
    && existsSync(path.join(candidate, "AGENTS.md"));
}

export function findHarnessRoot(startDir: string): string {
  let current = path.resolve(startDir);
  while (true) {
    if (isHarnessRoot(current)) return current;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(`Could not locate the harness root from '${startDir}'.`);
}

export function createHarnessPaths(harnessRoot: string): HarnessPaths {
  const resolvedHarnessRoot = path.resolve(harnessRoot);
  const coreRoot = path.join(resolvedHarnessRoot, "core");
  const repositoryRoot = path.resolve(resolvedHarnessRoot, "..");
  const appRoot = path.join(repositoryRoot, "app");
  const specifyRoot = path.join(resolvedHarnessRoot, ".specify");
  const specsRoot = path.join(resolvedHarnessRoot, "specs");
  const graphifyRoot = path.join(resolvedHarnessRoot, "graphify-out");
  const artifactsRoot = path.join(resolvedHarnessRoot, "artifacts");
  const architectureRoot = path.join(artifactsRoot, "architecture");
  const reportsRoot = path.join(artifactsRoot, "reports");
  return {
    harnessRoot: resolvedHarnessRoot,
    coreRoot,
    hooksRoot: path.join(coreRoot, "hooks"),
    scriptsRoot: path.join(coreRoot, "scripts"),
    libRoot: path.join(coreRoot, "lib"),
    assetsRoot: path.join(coreRoot, "assets"),
    repositoryRoot,
    appRoot,
    specifyRoot,
    specsRoot,
    constitutionPath: path.join(specifyRoot, "memory", "constitution.md"),
    featureStatePath: path.join(specifyRoot, "feature.json"),
    graphifyRoot,
    graphifyGraph: path.join(graphifyRoot, "graph.json"),
    artifactsRoot,
    architectureRoot,
    architectureSourceRoot: path.join(architectureRoot, "source"),
    architectureHtmlRoot: path.join(architectureRoot, "html"),
    reportsRoot,
    executionReportsRoot: path.join(reportsRoot, "executions"),
    docsRoot: path.join(repositoryRoot, "docs"),
    materialsRoot: path.join(repositoryRoot, "materiais"),
    metadataValidationRoot: path.join(appRoot, "data", "processed", "metadata-validation"),
  };
}

export function getHarnessPaths(startDir = import.meta.dir): HarnessPaths {
  return createHarnessPaths(findHarnessRoot(startDir));
}
