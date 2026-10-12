$ErrorActionPreference = 'Stop'

function Write-Context([string]$message) {
    @{ 
        hookSpecificOutput = @{
            hookEventName = 'SessionStart'
            additionalContext = $message
        }
    } | ConvertTo-Json -Depth 5 -Compress
}

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

$harnessRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$appRoot = [IO.Path]::GetFullPath((Join-Path $harnessRoot '..\app'))
$venvPython = Join-Path $appRoot '.venv\Scripts\python.exe'
$venvActivate = Join-Path $appRoot '.venv\Scripts\Activate.ps1'

$hookEvent = [string]$event.hook_event_name
if ($hookEvent -eq 'SessionStart' -or $event.session_id -and -not $event.tool_input) {
    if (Test-Path -LiteralPath $venvPython) {
        Write-Context "Application Python environment detected at app/.venv. For app commands, use workdir app with 'uv run ...' or 'uv add ...'. Bare python, pip, and pytest commands are blocked unless they explicitly use app/.venv or Activate.ps1."
    } else {
        Write-Context "Application Python environment is missing at app/.venv. Run 'uv sync' from app before using Python, pytest, or the libras CLI. Prefer 'uv run ...' so the project environment is selected explicitly."
    }
    exit 0
}

$command = [string]$event.tool_input.command
if (-not $command) { exit 0 }

$projectCommand = $command -match '(?i)(\buv\s+(add|remove|sync|lock|run|pip)\b|\b(?:python|python3|pip|pytest|libras)(?:\.exe)?\b)'
if (-not $projectCommand) { exit 0 }

$workdir = [string]$event.tool_input.workdir
if (-not $workdir) { $workdir = (Get-Location).Path }
try {
    if (-not [IO.Path]::IsPathRooted($workdir)) {
        $workdir = Join-Path $harnessRoot $workdir
    }
    $workdir = [IO.Path]::GetFullPath($workdir)
} catch {
    exit 0
}

$appPrefix = $appRoot.TrimEnd('\') + '\'
$inApp = $workdir.Equals($appRoot, [StringComparison]::OrdinalIgnoreCase) -or
    $workdir.StartsWith($appPrefix, [StringComparison]::OrdinalIgnoreCase)
if (-not $inApp) { exit 0 }

$uvProjectCommand = $command -match '(?i)\buv\s+(add|remove|sync|lock)\b'
if ($uvProjectCommand) { exit 0 }

$usesProjectEnvironment = $command -match '(?i)(\buv\s+run\b|\.venv[/\\]Scripts[/\\](python|python3|pip|pytest)(?:\.exe)?\b|Activate\.ps1)'
if ($usesProjectEnvironment) { exit 0 }

if (-not (Test-Path -LiteralPath $venvPython)) {
    Deny "Application environment not found at '$venvPython'. Run 'uv sync' with workdir set to app, then use 'uv run ...'."
}

Deny "Use the application's virtual environment for this command. Prefer 'uv run ...' from app, or explicitly invoke '$venvPython'. A bare global python/pip/pytest command is blocked."
