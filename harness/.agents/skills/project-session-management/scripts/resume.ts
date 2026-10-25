import { readFile } from "node:fs/promises";
import { runCommand } from "../../../../lib/process.ts";

const sessionPath = "SESSION.md";
let session: string;
try {
  session = await readFile(sessionPath, "utf8");
} catch {
  process.stderr.write("⚠️  SESSION.md not found in project root\nRun this script from your project root directory\nOr create SESSION.md first using the project-session-management skill\n");
  process.exit(1);
}
const colorEnabled = Boolean(process.stdout.isTTY && !process.env.NO_COLOR);
const color = (code: string, text: string) => colorEnabled ? `\u001b[${code}m${text}\u001b[0m` : text;
const lines = session.split(/\r?\n/);
const phaseIndex = lines.findIndex((line) => /^## .*🔄/.test(line));
const phase = phaseIndex < 0 ? "No phase currently in progress" : lines.slice(phaseIndex, phaseIndex + 16).join("\n");
const checkpoint = await runCommand("git", ["log", "--oneline", "--grep=checkpoint:", "-1", "--format=%H %s%n%b"], { quiet: true }).catch(() => null);
const checkpointText = checkpoint?.stdout.trim() || "No checkpoint commits found";
const nextAction = [...lines].reverse().find((line) => line.includes("**Next Action**"))?.replace("**Next Action**: ", "") ?? "No next action defined";
const count = (emoji: string) => (session.match(new RegExp(emoji, "gu")) ?? []).length;
const planningDocs = [...lines].find((line) => line.includes("**Planning Docs**"))?.replace("**Planning Docs**: ", "") ?? "Not specified";
process.stdout.write(`${color("34", "=== Current Project State ===")}\n\n`);
process.stdout.write(`${color("32", "Current Phase:")}\n${phase}\n\n`);
process.stdout.write(`${color("32", "Last Checkpoint:")}\n${checkpointText}\n\n`);
process.stdout.write(`${color("32", "Next Action:")}\n${nextAction}\n\n`);
process.stdout.write(`${color("32", "Status Summary:")}\n✅ Completed: ${count("✅")}\n🔄 In Progress: ${count("🔄")}\n⏸️  Pending: ${count("⏸️")}\n🚫 Blocked: ${count("🚫")}\n\n`);
process.stdout.write(`${color("32", "Planning Docs:")}\n${planningDocs}\n\n`);
process.stdout.write(`${color("34", "=== End of Summary ===")}\n\n💡 Tip: Read SESSION.md for full details\n💡 Tip: Use 'git log --grep="checkpoint:"' to see checkpoint history\n`);
