import path from "node:path";
import { fileURLToPath } from "node:url";
import { emitContext, emitDeny, eventString, readHookEvent, toolInputString } from "../lib/hook-protocol.ts";

const event = await readHookEvent();
if (!event) process.exit(0);
const harnessRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appRoot = path.resolve(harnessRoot, "..", "app");
const venvPython = process.platform === "win32"
  ? path.join(appRoot, ".venv", "Scripts", "python.exe")
  : path.join(appRoot, ".venv", "bin", "python");
const venvExists = await Bun.file(venvPython).exists();
const hookEvent = eventString(event, "hook_event_name");
if (hookEvent === "SessionStart" || (Boolean(event.session_id) && !event.tool_input)) {
  emitContext("SessionStart", venvExists
    ? "Application Python environment detected at app/.venv. For app commands, use workdir app with 'uv run ...' or 'uv add ...'. Bare python, pip, and pytest commands are blocked unless they explicitly use the app/.venv interpreter or activate that environment."
    : "Application Python environment is missing at app/.venv. Run 'uv sync' from app before using Python, pytest, or the libras CLI. Prefer 'uv run ...' so the project environment is selected explicitly.");
  process.exit(0);
}
const command = toolInputString(event, "command");
if (!command || /(\buv\s+(add|remove|sync|lock|run|pip)\b|\b(?:python|python3|pip|pytest|libras)(?:\.exe)?\b)/i.test(command) === false) process.exit(0);
let workdir = toolInputString(event, "workdir") || process.cwd();
if (!path.isAbsolute(workdir)) workdir = path.resolve(harnessRoot, workdir);
workdir = path.resolve(workdir);
const normalize = (value: string) => process.platform === "win32" ? value.toLowerCase() : value;
const appPrefix = `${appRoot}${path.sep}`;
const inApp = normalize(workdir) === normalize(appRoot) || normalize(workdir).startsWith(normalize(appPrefix));
if (!inApp || /\buv\s+(add|remove|sync|lock)\b/i.test(command)) process.exit(0);
if (/\buv\s+run\b|\.venv[/\\](?:Scripts[/\\](?:python|python3|pip|pytest)(?:\.exe)?|bin[/\\](?:python|python3|pip|pytest))\b|Activate\.ps1/i.test(command)) process.exit(0);
if (!venvExists) emitDeny(`Application environment not found at '${venvPython}'. Run 'uv sync' with workdir set to app, then use 'uv run ...'.`);
else emitDeny(`Use the application's virtual environment for this command. Prefer 'uv run ...' from app, or explicitly invoke '${venvPython}'. A bare global python/pip/pytest command is blocked.`);
