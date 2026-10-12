$ErrorActionPreference = 'Stop'

function Emit-PostMessage([string]$message, [string]$systemMessage) {
    @{
        systemMessage = $systemMessage
        hookSpecificOutput = @{
            hookEventName = 'PostToolUse'
            additionalContext = $message
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

$command = [string]$event.tool_input.command
if (-not $command) { exit 0 }

$relevant = $command -match '(?im)^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s+(?:\.\.[/\\]app[/\\]|specs[/\\]|\.specify[/\\]|\.agents[/\\]|\.codex[/\\]|AGENTS\.md)'
if (-not $relevant) { exit 0 }

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath $root

$graphPath = Join-Path $root 'graphify-out/graph.json'
if (-not (Test-Path -LiteralPath $graphPath)) {
    Emit-PostMessage 'Relevant files changed, but the canonical Graphify graph does not exist yet. Run graphify . before relying on graph queries.' 'Graphify refresh skipped: canonical graph is missing.'
}

$duplicate = Join-Path $root '../app/graphify-out'
if (Test-Path -LiteralPath $duplicate) {
    Emit-PostMessage "Relevant files changed, but ../app/graphify-out/ exists. The canonical graph remains harness/graphify-out/." 'Graphify layout warning: duplicate application graph detected.'
}

$previousErrorAction = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$null = @(& graphify update . 2>&1 | Out-String)
$exitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorAction
if ($exitCode -ne 0) {
    Emit-PostMessage "Graphify update failed after a relevant edit (exit $exitCode). Run graphify update . manually before answering graph-based questions." 'Graphify refresh failed after the edit.'
}

Emit-PostMessage 'Graphify was incrementally refreshed after the relevant edit. The canonical output remains harness/graphify-out/.' 'Canonical Graphify refreshed.'
