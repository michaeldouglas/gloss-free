$ErrorActionPreference = 'Stop'

function Deny([string]$reason) {
    @{
        hookSpecificOutput = @{
            hookEventName = 'PreToolUse'
            permissionDecision = 'deny'
            permissionDecisionReason = $reason
        }
    } | ConvertTo-Json -Depth 5 -Compress
    exit 0
}

try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw.Trim()) { exit 0 }
    $event = $raw | ConvertFrom-Json
} catch {
    exit 0
}

$toolName = [string]$event.tool_name
$commandText = [string]$event.tool_input.command
if (-not $commandText) { exit 0 }

$protectedPath = '(?i)(\.\.[/\\]old([/\\]|$)|\.\.[/\\]app[/\\]graphify-out([/\\]|$)|[/\\]app[/\\]graphify-out([/\\]|$))'
if ($commandText -match $protectedPath) {
    Deny "Repository policy blocked this tool call: ../old/ is legacy and ../app/graphify-out/ is not a valid Graphify location. Use harness/graphify-out/."
}

if ($toolName -eq 'apply_patch') { exit 0 }

$destructive = @(
    '(?i)\bgit\s+reset\s+--hard\b',
    '(?i)\bgit\s+clean(?:\s|$)',
    '(?i)\bgit\s+checkout\s+--\b',
    '(?i)\bgit\s+restore\s+--\b',
    '(?i)\bgit\s+push\b[^\r\n]*(--force|-f\b)',
    '(?i)\brm\s+-rf\b',
    '(?i)\bremove-item\b[^\r\n]*(?:-recurse|-force)',
    '(?i)\bdel\b[^\r\n]*/s\b',
    '(?i)\bformat\s+[a-z]:\b'
)
foreach ($pattern in $destructive) {
    if ($commandText -match $pattern) {
        Deny "Repository policy blocked a destructive command. Inspect the exact target and use a recoverable operation or ask for explicit direction."
    }
}

$branch = (git branch --show-current 2>$null).Trim()
if ($branch -match '^(main|develop)$' -and $commandText -match '(?i)\bgit\s+(commit|push|merge|rebase|cherry-pick|reset|restore)\b') {
    Deny "Protected branch policy blocked this Git command on '$branch'. Work on an existing feature/* branch."
}

exit 0
