$ErrorActionPreference = 'Stop'

try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw.Trim()) { exit 0 }
    $event = $raw | ConvertFrom-Json
} catch {
    exit 0
}

$prompt = [string]$event.prompt
if (-not $prompt) { exit 0 }

$codebaseQuestion = $prompt -match '(?i)(c[oó]digo|arquivo|arquitetura|estrutura|projeto|repo|reposit[oó]rio|fun[cç][aã]o|m[oó]dulo|onde fica|como funciona|quem chama|grafo|graphify|speckit|spec kit)'
if (-not $codebaseQuestion) { exit 0 }

@{
    hookSpecificOutput = @{
        hookEventName = 'UserPromptSubmit'
        additionalContext = "This prompt appears to concern the repository. Follow AGENTS.md: when graphify-out/graph.json exists, run a scoped 'graphify query' first; use graphify path/explain for relationship or concept questions."
    }
} | ConvertTo-Json -Depth 5 -Compress
