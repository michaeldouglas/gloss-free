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

$relevant = $command -match '(?im)^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s+(?:\.\.[/\\]app[/\\]|specs[/\\]|\.specify[/\\]|\.agents[/\\]|\.codex[/\\]|artifacts[/\\](?:architecture|reports)[/\\]|scripts[/\\]build_showroom\.py|AGENTS\.md)'
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

$architectureMessage = 'Archify refresh checked; no candidate diagram was published automatically.'
$architectureScript = Join-Path $root 'scripts/refresh_architecture.ps1'
if (Test-Path -LiteralPath $architectureScript) {
    $null = @(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $architectureScript -Dataset 'code-edit' 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) {
        $architectureMessage = 'Archify refresh failed; inspect artifacts/architecture/architecture-refresh.json.'
    } else {
        $architectureMessage = 'Archify refresh checked; generated diagrams remain under harness/artifacts/architecture/.'
    }
}

$showroomMessage = 'Showroom refresh skipped; the generator is unavailable.'
$showroomScript = Join-Path $root 'harness/scripts/build_showroom.py'
$uv = Get-Command uv -ErrorAction SilentlyContinue
if (Test-Path -LiteralPath $showroomScript -and $null -ne $uv) {
    $null = @(& $uv.Source run --project (Join-Path $root 'app') python $showroomScript --repo-root $root 2>&1 | Out-String)
    if ($LASTEXITCODE -eq 0) {
        $showroomMessage = 'Showroom atualizado em docs/ a partir dos artefatos derivados.'
    } else {
        $showroomMessage = 'Showroom refresh falhou; execute o notebook ou revise o gerador.'
    }
}

Emit-PostMessage "Graphify was incrementally refreshed after the relevant edit. The canonical output remains harness/graphify-out/. $architectureMessage $showroomMessage" 'Canonical Graphify, architecture and showroom state refreshed.'
