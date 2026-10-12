$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath $root

$branch = (git branch --show-current 2>$null).Trim()
$graph = Test-Path -LiteralPath (Join-Path $root 'graphify-out/graph.json')
$duplicateGraph = Test-Path -LiteralPath (Join-Path $root '../app/graphify-out')
$constitution = Test-Path -LiteralPath (Join-Path $root '.specify/memory/constitution.md')
$feature = $null
$featureFile = Join-Path $root '.specify/feature.json'
if (Test-Path -LiteralPath $featureFile) {
    try { $feature = (Get-Content -LiteralPath $featureFile -Raw | ConvertFrom-Json).feature_directory } catch { $feature = $null }
}

$lines = @(
    "Harness context: repository root is '$root'.",
    "Architecture: application is '../app/'; canonical Graphify output is 'graphify-out/'; never create '../app/graphify-out/'.",
    "Codebase questions: run 'graphify query <question>' before browsing broadly; after relevant code or artifact edits, keep the canonical graph current with 'graphify update .'.",
    "Spec Kit artifacts live under 'specs/<feature>/'; use the constitution and the feature's spec, plan, and tasks as the workflow source of truth.",
    "Protected branches: make changes only on an existing 'feature/*' branch; do not commit directly to main or develop."
)
if ($branch) { $lines += "Current branch: $branch." }
if ($feature) { $lines += "Current Spec Kit feature: $feature." }
if (-not $graph) { $lines += "Graphify status: graphify-out/graph.json is missing; do not assume graph queries are available." }
if ($duplicateGraph) { $lines += "WARNING: '../app/graphify-out/' exists and violates the canonical graph layout." }
if (-not $constitution) { $lines += "WARNING: .specify/memory/constitution.md is missing." }

$context = ($lines -join "`n")
@{
    hookSpecificOutput = @{
        hookEventName = 'SessionStart'
        additionalContext = $context
    }
} | ConvertTo-Json -Depth 5 -Compress
