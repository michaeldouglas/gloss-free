import { runCommand } from "../lib/process.ts";
import { emitDeny, readHookEvent, toolInputString } from "../lib/hook-protocol.ts";

const event = await readHookEvent();
if (!event) process.exit(0);
const toolName = typeof event.tool_name === "string" ? event.tool_name : "";
const commandText = toolInputString(event, "command");
if (!commandText) process.exit(0);
if (/(\.\.[/\\]old([/\\]|$)|\.\.[/\\]app[/\\]graphify-out([/\\]|$)|[/\\]app[/\\]graphify-out([/\\]|$))/i.test(commandText)) {
  const legacy = ["..", "old"].join("/");
  const duplicate = ["..", "app", "graphify-out"].join("/");
  emitDeny(`Repository policy blocked this tool call: ${legacy}/ is legacy and ${duplicate}/ is not a valid Graphify location. Use harness/graphify-out/.`);
  process.exit(0);
}
if (toolName === "apply_patch") process.exit(0);
const destructive = [
  /\bgit\s+reset\s+--hard\b/i, /\bgit\s+clean(?:\s|$)/i, /\bgit\s+checkout\s+--\b/i,
  /\bgit\s+restore\s+--\b/i, /\bgit\s+push\b[^\r\n]*(--force|-f\b)/i, /\brm\s+-rf\b/i,
  /\bremove-item\b[^\r\n]*(?:-recurse|-force)/i, /\bdel\b[^\r\n]*\/s\b/i, /\bformat\s+[a-z]:\b/i,
];
if (destructive.some((pattern) => pattern.test(commandText))) {
  emitDeny("Repository policy blocked a destructive command. Inspect the exact target and use a recoverable operation or ask for explicit direction.");
  process.exit(0);
}
const branchResult = await runCommand("git", ["branch", "--show-current"], { quiet: true }).catch(() => null);
const branch = branchResult?.stdout.trim() ?? "";
if (/^(main|develop)$/.test(branch) && /\bgit\s+(commit|push|merge|rebase|cherry-pick|reset|restore)\b/i.test(commandText)) emitDeny(`Protected branch policy blocked this Git command on '${branch}'. Work on an existing feature/* branch.`);
