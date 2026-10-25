param(
    [string]$Dataset = 'unknown'
)

$ErrorActionPreference = 'Stop'

$harnessRoot = Split-Path -Parent $PSScriptRoot
$repositoryRoot = (& git -C $harnessRoot rev-parse --show-toplevel).Trim()
if (-not $repositoryRoot) {
    throw 'Não foi possível localizar a raiz Git do repositório.'
}
$artifactRoot = Join-Path $harnessRoot 'artifacts'
$architectureRoot = Join-Path $artifactRoot 'architecture'
$sourceRoot = Join-Path $architectureRoot 'source'
$htmlRoot = Join-Path $architectureRoot 'html'
$statusPath = Join-Path $architectureRoot 'architecture-refresh.json'

New-Item -ItemType Directory -Force -Path $sourceRoot, $htmlRoot | Out-Null

$record = [ordered]@{
    schema_version = 'architecture-refresh.v1'
    dataset = $Dataset
    executed_at = (Get-Date).ToUniversalTime().ToString('o')
    status = 'pending'
    candidates = @()
    outputs = @()
}

function Save-Status {
    param([object]$Value)
    $Value | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statusPath -Encoding utf8
}

try {
    $candidates = @(Get-ChildItem -LiteralPath $sourceRoot -Filter '*.architecture.json' -File -ErrorAction SilentlyContinue)
    $record.candidates = @($candidates | ForEach-Object { $_.Name })

    if ($candidates.Count -eq 0) {
        $record.reason = 'Nenhum candidato Archify em artifacts/architecture/source.'
        Save-Status $record
        exit 0
    }

    $node = Get-Command node -ErrorAction SilentlyContinue
    $archifyCli = Join-Path $harnessRoot '.agents/skills/archify/bin/archify.mjs'
    if ($null -eq $node -or -not (Test-Path -LiteralPath $archifyCli)) {
        $record.reason = 'Node ou a CLI local do Archify não está disponível.'
        Save-Status $record
        exit 0
    }

    foreach ($candidate in $candidates) {
        $slug = $candidate.BaseName -replace '\.architecture$', ''
        $outputPath = Join-Path $htmlRoot "$slug.html"
        $arguments = @(
            $archifyCli, 'finalize', 'architecture', $candidate.FullName,
            $outputPath, '--repo-root', $repositoryRoot, '--quality', 'showcase', '--json'
        )
        $output = @(& $node.Source @arguments 2>&1)
        if ($LASTEXITCODE -ne 0) {
            throw "Archify falhou para $($candidate.Name) com código $LASTEXITCODE."
        }
        $record.outputs += [ordered]@{
            candidate = $candidate.Name
            html = $outputPath
            result_tail = @($output | Select-Object -Last 5)
        }
    }

    $record.status = 'completed'
    Save-Status $record
    exit 0
} catch {
    $record.status = 'failed'
    $record.reason = $_.Exception.Message
    Save-Status $record
    exit 1
}
