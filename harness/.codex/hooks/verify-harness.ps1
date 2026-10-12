param(
    [ValidateSet('prepare', 'verify', 'converge')]
    [string]$Mode = 'verify'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath $root

$failures = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()

$branch = (git branch --show-current 2>$null).Trim()
if ($branch -notmatch '^feature/.+') {
    $failures.Add("Current branch '$branch' is not a feature/* branch.")
}

$constitution = Join-Path $root '.specify/memory/constitution.md'
if (-not (Test-Path -LiteralPath $constitution -PathType Leaf)) {
    $failures.Add('Missing .specify/memory/constitution.md.')
}

$featureDir = $null
$featureFile = Join-Path $root '.specify/feature.json'
if (Test-Path -LiteralPath $featureFile -PathType Leaf) {
    try { $featureDir = (Get-Content -LiteralPath $featureFile -Raw | ConvertFrom-Json).feature_directory } catch { $failures.Add('Could not parse .specify/feature.json.') }
}
if (-not $featureDir) {
    $candidate = Get-ChildItem -LiteralPath (Join-Path $root 'specs') -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($candidate) { $featureDir = $candidate.FullName.Substring($root.Length + 1) }
}
if (-not $featureDir) {
    $failures.Add('Could not resolve the active Spec Kit feature directory.')
} else {
    $featurePath = Join-Path $root $featureDir
    foreach ($name in @('spec.md', 'plan.md', 'tasks.md')) {
        if (-not (Test-Path -LiteralPath (Join-Path $featurePath $name) -PathType Leaf)) {
            $failures.Add("Missing $featureDir/$name.")
        }
    }

    $artifactText = Get-ChildItem -LiteralPath $featurePath -File -Recurse -Include *.md -ErrorAction SilentlyContinue | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }
    if (($artifactText -join "`n") -match '(?i)(NEEDS CLARIFICATION|\[FEATURE NAME\]|\[TITLE\]|TODO:?)') {
        $failures.Add("Unresolved Spec Kit placeholder detected under $featureDir.")
    }

    $tasksPath = Join-Path $featurePath 'tasks.md'
    if (Test-Path -LiteralPath $tasksPath -PathType Leaf) {
        $taskLines = Get-Content -LiteralPath $tasksPath
        $done = @($taskLines | Where-Object { $_ -match '^\s*[-*]\s+\[[xX]\]\s+' }).Count
        $open = @($taskLines | Where-Object { $_ -match '^\s*[-*]\s+\[\s\]\s+' }).Count
        if (($done + $open) -eq 0) { $failures.Add("No executable task checkboxes found in $featureDir/tasks.md.") }
        if ($open -gt 0) { $warnings.Add("$open open task(s) remain in $featureDir/tasks.md.") }
        if ($Mode -eq 'verify' -and $open -gt 0) { $failures.Add("Implementation verification requires all tasks to be checked; $open remain open.") }
        Write-Output "Spec Kit tasks: $done done, $open open ($featureDir)."
    }
}

$graph = Join-Path $root 'graphify-out/graph.json'
if (-not (Test-Path -LiteralPath $graph -PathType Leaf)) {
    $failures.Add('Missing canonical graphify-out/graph.json.')
}
if (Test-Path -LiteralPath (Join-Path $root '../app/graphify-out')) {
    $failures.Add('Duplicate ../app/graphify-out/ detected; use harness/graphify-out/.')
}

if ($Mode -ne 'prepare' -and (Test-Path -LiteralPath (Join-Path $root '../app/pyproject.toml'))) {
    Push-Location -LiteralPath (Join-Path $root '../app')
    try {
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $null = @(& uv run python -m unittest discover -s dataset/tests -v 2>&1 | Out-String)
        $testExitCode = $LASTEXITCODE
        $ErrorActionPreference = $previousErrorAction
        if ($testExitCode -ne 0) {
            $failures.Add('Application test suite failed: uv run python -m unittest discover -s dataset/tests -v')
        } else {
            Write-Output 'Application tests: passed.'
        }
    } finally {
        Pop-Location
    }
}

if ($Mode -eq 'converge' -and $failures.Count -eq 0) {
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $null = @(& graphify update . 2>&1 | Out-String)
    $graphifyExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction
    if ($graphifyExitCode -ne 0) {
        $failures.Add('Graphify update failed during convergence.')
    } else {
        Write-Output 'Graphify: canonical graph refreshed.'
    }
}

foreach ($warning in $warnings) { Write-Warning $warning }
if ($failures.Count -gt 0) {
    Write-Error (($failures | ForEach-Object { "- $_" }) -join "`n")
    exit 1
}

Write-Output "Harness verification passed ($Mode)."
exit 0
