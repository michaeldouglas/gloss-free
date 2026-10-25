export function normalizeOption(value: string): string {
  return value.replace(/^-+/, "").replaceAll("-", "").toLowerCase();
}

export function printJson(value: unknown): void {
  process.stdout.write(`${JSON.stringify(value)}\n`);
}

export function fail(message: string, code = 1): never {
  process.stderr.write(`${message}\n`);
  process.exit(code);
}
