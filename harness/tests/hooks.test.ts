import { afterEach, describe, expect, test } from "bun:test";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import type { CommandResult } from "../lib/process.ts";
import { handlePostToolUse, isRelevantEdit } from "../hooks/post-tool-use.ts";
import { buildShowroom } from "../scripts/build-showroom.ts";
import { refreshArchitecture } from "../scripts/refresh-architecture.ts";
import { resolveTemplateContent } from "../lib/spec-kit.ts";

const root = path.resolve(import.meta.dir, "..");
const tempDirs: string[] = [];

async function runHook(name: string, event?: unknown): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  const child = Bun.spawn(["bun", "run", path.join(root, "hooks", `${name}.ts`)], {
    cwd: root,
    stdin: "pipe",
    stdout: "pipe",
    stderr: "pipe",
    windowsHide: true,
  });
  if (event !== undefined) child.stdin.write(`${JSON.stringify(event)}\n`);
  child.stdin.end();
  const [stdout, stderr, exitCode] = await Promise.all([new Response(child.stdout).text(), new Response(child.stderr).text(), child.exited]);
  return { stdout, stderr, exitCode };
}

afterEach(async () => {
  await Promise.all(tempDirs.splice(0).map((dir) => rm(dir, { recursive: true, force: true })));
});

describe("Codex hook protocol", () => {
  test("SessionStart emits one JSON hook payload", async () => {
    const result = await runHook("session-start");
    expect(result.exitCode).toBe(0);
    expect(result.stderr).toBe("");
    const payload = JSON.parse(result.stdout);
    expect(payload.hookSpecificOutput.hookEventName).toBe("SessionStart");
    expect(payload.hookSpecificOutput.additionalContext).toContain("feature/validar-metadados-video");
  });

  test("UserPromptSubmit stays silent unless the prompt concerns the repository", async () => {
    const irrelevant = await runHook("user-prompt-context", { prompt: "What is the weather?" });
    expect(irrelevant.stdout).toBe("");
    const relevant = await runHook("user-prompt-context", { prompt: "Como funciona a arquitetura deste projeto?" });
    expect(JSON.parse(relevant.stdout).hookSpecificOutput.hookEventName).toBe("UserPromptSubmit");
  });

  test("PreToolUse preserves allow-silence and deny JSON", async () => {
    const allowed = await runHook("pre-tool-policy", { tool_name: "Bash", tool_input: { command: "git status --short" } });
    expect(allowed.stdout).toBe("");
    const denied = await runHook("pre-tool-policy", { tool_name: "Bash", tool_input: { command: "git clean -fd" } });
    const payload = JSON.parse(denied.stdout);
    expect(payload.hookSpecificOutput).toMatchObject({ hookEventName: "PreToolUse", permissionDecision: "deny" });
    expect(payload.hookSpecificOutput.permissionDecisionReason).toContain("destructive command");
  });

  test("Python policy blocks bare app Python but permits uv run", async () => {
    const denied = await runHook("project-venv-policy", { tool_event_name: "PreToolUse", tool_input: { command: "python -m unittest", workdir: path.resolve(root, "..", "app") } });
    expect(JSON.parse(denied.stdout).hookSpecificOutput.permissionDecision).toBe("deny");
    const allowed = await runHook("project-venv-policy", { tool_event_name: "PreToolUse", tool_input: { command: "uv run python -m unittest", workdir: path.resolve(root, "..", "app") } });
    expect(allowed.stdout).toBe("");
  });

  test("malformed or irrelevant events stay silent", async () => {
    const result = await runHook("user-prompt-context", { prompt: "hello" });
    expect(result.stdout).toBe("");
    expect(result.exitCode).toBe(0);
  });
});

describe("PostToolUse orchestration", () => {
  test("recognizes relevant paths and refreshes each downstream artifact once", async () => {
    expect(isRelevantEdit("*** Update File: scripts/build-showroom.ts")).toBe(true);
    expect(isRelevantEdit("*** Update File: assets/showroom.css")).toBe(true);
    expect(isRelevantEdit("*** Update File: package.json")).toBe(true);
    expect(isRelevantEdit("*** Update File: README.md")).toBe(false);
    const temp = await mkdtemp(path.join(os.tmpdir(), "harness-post-hook-"));
    tempDirs.push(temp);
    const harnessRoot = path.join(temp, "harness");
    await mkdir(path.join(harnessRoot, "graphify-out"), { recursive: true });
    await writeFile(path.join(harnessRoot, "graphify-out", "graph.json"), "{}\n");
    const commands: Array<{ command: string; args: string[]; cwd?: string }> = [];
    const fakeRunner = async (command: string, args: string[], options?: { cwd?: string }): Promise<CommandResult> => {
      commands.push({ command, args, cwd: options?.cwd });
      return { exitCode: 0, stdout: "ok", stderr: "" };
    };
    let output = "";
    const originalWrite = process.stdout.write;
    process.stdout.write = ((chunk: string | Uint8Array) => { output += String(chunk); return true; }) as typeof process.stdout.write;
    try {
      await handlePostToolUse({ tool_input: { command: "*** Update File: scripts/build-showroom.ts" } }, harnessRoot, fakeRunner);
    } finally {
      process.stdout.write = originalWrite;
    }
    expect(commands.map((item) => item.command)).toEqual(["graphify", "bun", "bun"]);
    expect(commands[1].args).toContain("scripts/refresh-architecture.ts");
    expect(commands[2].args).toContain("scripts/build-showroom.ts");
    const payload = JSON.parse(output);
    expect(payload.hookSpecificOutput.hookEventName).toBe("PostToolUse");
    expect(payload.systemMessage).toContain("Canonical Graphify");
  });
});

describe("showroom generation", () => {
  test("builds the dashboard from derived summaries and copies architecture HTML", async () => {
    const temp = await mkdtemp(path.join(os.tmpdir(), "harness-showroom-"));
    tempDirs.push(temp);
    const harness = path.join(temp, "harness");
    const docs = path.join(temp, "docs");
    await mkdir(path.join(harness, "artifacts", "reports"), { recursive: true });
    await mkdir(path.join(harness, "artifacts", "architecture", "html"), { recursive: true });
    await mkdir(path.join(temp, "app", "data", "processed", "metadata-validation", "demo", "reports"), { recursive: true });
    await mkdir(path.join(harness, "assets"), { recursive: true });
    await mkdir(path.join(docs, "assets"), { recursive: true });
    await mkdir(path.join(docs, "architecture"), { recursive: true });
    await writeFile(path.join(harness, "artifacts", "reports", "latest.json"), JSON.stringify({ dataset: "demo", decision: "GO", quality_counts: { INFO: 2 }, technical_summary: { videos_seen: 5 } }));
    await writeFile(path.join(harness, "artifacts", "reports", "latest.md"), "Relatório de teste");
    await writeFile(path.join(harness, "artifacts", "architecture", "html", "pipeline.html"), "<h1>Pipeline</h1>");
    await writeFile(path.join(temp, "app", "data", "processed", "metadata-validation", "demo", "reports", "metadata_summary.json"), JSON.stringify({ dataset: "demo", decision: "GO", counts: { physical_videos: 5, annotations: 5, manifest_rows: 5, issues: 0, by_severity: { INFO: 0 } }, key_reconciliation: { matched: 5, missing: 0, extra: 0, filesystem_key_column: "video_id" } }));
    await writeFile(path.join(harness, "assets", "showroom.css"), "body{}");
    await writeFile(path.join(docs, "assets", "style.css"), "stale-style");
    await writeFile(path.join(docs, "architecture", "old.html"), "old");
    const result = await buildShowroom(temp);
    expect(result).toMatchObject({ datasets: 1, architecture_files: 1 });
    expect(await Bun.file(path.join(docs, "index.html")).text()).toContain("Libras Research Showroom");
    expect(await Bun.file(path.join(docs, "datasets", "index.html")).text()).toContain("demo");
    expect(await Bun.file(path.join(docs, "architecture", "pipeline.html")).text()).toContain("Pipeline");
    expect(await Bun.file(path.join(docs, "architecture", "old.html")).exists()).toBe(false);
    expect(await Bun.file(path.join(docs, "assets", "style.css")).text()).toBe("body{}\n");
  });
});

describe("Archify refresh orchestration", () => {
  test("invokes the local Archify CLI through Bun and records the result", async () => {
    const temp = await mkdtemp(path.join(os.tmpdir(), "harness-archify-"));
    tempDirs.push(temp);
    const harness = path.join(temp, "harness");
    const candidate = path.join(harness, "artifacts", "architecture", "source", "flow.architecture.json");
    await mkdir(path.dirname(candidate), { recursive: true });
    await mkdir(path.join(harness, ".agents", "skills", "archify", "bin"), { recursive: true });
    await writeFile(candidate, "{}\n");
    await writeFile(path.join(harness, ".agents", "skills", "archify", "bin", "archify.mjs"), "// test stub\n");
    const calls: Array<{ command: string; args: string[] }> = [];
    const fakeRunner = async (command: string, args: string[]): Promise<CommandResult> => {
      calls.push({ command, args });
      return command === "git"
        ? { exitCode: 0, stdout: harness, stderr: "" }
        : { exitCode: 0, stdout: "validated\nrendered", stderr: "" };
    };
    const result = await refreshArchitecture(harness, "test-dataset", fakeRunner);
    expect(result.exitCode).toBe(0);
    expect(result.record.status).toBe("completed");
    expect(calls[1].command).toBe("bun");
    expect(calls[1].args).toContain("finalize");
    expect(result.record.outputs[0].result_tail).toEqual(["validated", "rendered"]);
    expect(JSON.parse(await Bun.file(path.join(harness, "artifacts", "architecture", "architecture-refresh.json")).text()).dataset).toBe("test-dataset");
  });
});

describe("Spec Kit template composition", () => {
  test("honors override precedence and composes preset wraps using Bun YAML", async () => {
    const temp = await mkdtemp(path.join(os.tmpdir(), "harness-speckit-"));
    tempDirs.push(temp);
    const specify = path.join(temp, ".specify");
    const overrides = path.join(specify, "templates", "overrides");
    const presets = path.join(specify, "presets");
    await mkdir(overrides, { recursive: true });
    await mkdir(path.join(presets, "wrap", "templates"), { recursive: true });
    await mkdir(path.join(presets, "base", "templates"), { recursive: true });
    await writeFile(path.join(presets, ".registry"), JSON.stringify({ presets: { wrap: { priority: 1 }, base: { priority: 10 } } }));
    await writeFile(path.join(presets, "wrap", "preset.yml"), "provides:\n  templates:\n    - type: template\n      name: spec-template\n      file: templates/spec-template.md\n      strategy: wrap\n");
    await writeFile(path.join(presets, "base", "preset.yml"), "provides:\n  templates:\n    - type: template\n      name: spec-template\n      file: templates/spec-template.md\n      strategy: replace\n");
    await writeFile(path.join(presets, "wrap", "templates", "spec-template.md"), "Before\n{CORE_TEMPLATE}\nAfter");
    await writeFile(path.join(presets, "base", "templates", "spec-template.md"), "Base template");
    expect(await resolveTemplateContent("spec-template", temp)).toBe("Before\nBase template\nAfter");
    await writeFile(path.join(overrides, "spec-template.md"), "Project override");
    expect(await resolveTemplateContent("spec-template", temp)).toBe("Project override");
  });
});
