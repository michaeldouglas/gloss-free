export interface HookEvent {
  hook_event_name?: string;
  session_id?: string;
  prompt?: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  [key: string]: unknown;
}

export async function readHookEvent(): Promise<HookEvent | null> {
  try {
    const raw = await Bun.stdin.text();
    return raw.trim() ? JSON.parse(raw) as HookEvent : null;
  } catch {
    return null;
  }
}

export function emitHook(payload: Record<string, unknown>): void {
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

export function emitContext(eventName: string, additionalContext: string): void {
  emitHook({ hookSpecificOutput: { hookEventName: eventName, additionalContext } });
}

export function emitDeny(reason: string): void {
  emitHook({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: reason } });
}

export function eventString(event: HookEvent, key: string): string {
  const value = event[key];
  return typeof value === "string" ? value : "";
}

export function toolInputString(event: HookEvent, key: string): string {
  const value = event.tool_input?.[key];
  return typeof value === "string" ? value : "";
}
