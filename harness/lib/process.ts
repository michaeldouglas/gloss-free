export interface CommandResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

export async function runCommand(
  command: string,
  args: string[] = [],
  options: { cwd?: string; env?: Record<string, string | undefined>; quiet?: boolean } = {},
): Promise<CommandResult> {
  const child = Bun.spawn([command, ...args], {
    cwd: options.cwd,
    env: options.env,
    stdout: "pipe",
    stderr: "pipe",
    stdin: "ignore",
    windowsHide: true,
  });
  const [stdout, stderr, exitCode] = await Promise.all([
    new Response(child.stdout).text(),
    new Response(child.stderr).text(),
    child.exited,
  ]);
  if (!options.quiet && stderr) process.stderr.write(stderr);
  return { exitCode, stdout, stderr };
}

export async function commandExists(command: string): Promise<boolean> {
  const result = await runCommand(process.platform === "win32" ? "where.exe" : "which", [command], { quiet: true }).catch(() => null);
  return result?.exitCode === 0;
}
