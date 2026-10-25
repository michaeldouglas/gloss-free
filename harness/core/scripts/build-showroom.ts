import path from "node:path";
import { mkdir, readdir, readFile, writeFile, rm, copyFile } from "node:fs/promises";
import { createHarnessPaths, getHarnessPaths } from "../lib/paths.ts";

type JsonObject = Record<string, any>;
type ShowroomProject = {
  schema_version: "showroom-project.v3";
  title: string;
  displayTitle: string;
  summary: string;
  problemContext: string;
  researchFocus: string;
  glossFreeExplanation: string;
  validationPurpose: string;
  interpretationLimit: string;
  plannedMethodology: Array<{ title: string; detail: string }>;
  proposalReference: { label: string; date: string; href: string };
  glossFreeReference: { label: string; href: string };
  nextStep: string;
  pipeline: Array<{ title: string; detail: string }>;
};
const severities = ["CRITICAL", "ERROR", "WARNING", "INFO"] as const;
const defaultPaths = getHarnessPaths();
const harnessRoot = defaultPaths.harnessRoot;

function esc(value: unknown): string {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#x27;");
}
function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
async function loadJson(file: string): Promise<JsonObject> {
  let value: unknown;
  try { value = JSON.parse(await readFile(file, "utf8")); }
  catch (error) { throw new Error(`Não foi possível ler JSON válido em ${file}: ${error instanceof Error ? error.message : String(error)}`); }
  if (!isObject(value)) throw new Error(`O JSON em ${file} precisa conter um objeto.`);
  return value;
}
function validateProjectMetadata(value: JsonObject): ShowroomProject {
  if (value.schema_version !== "showroom-project.v3") throw new Error("Metadado do showroom precisa usar schema_version showroom-project.v3.");
  const requiredStrings = ["title", "displayTitle", "summary", "problemContext", "researchFocus", "glossFreeExplanation", "validationPurpose", "interpretationLimit", "nextStep"];
  for (const key of requiredStrings) if (typeof value[key] !== "string" || !value[key].trim()) throw new Error(`Metadado do showroom inválido: '${key}' precisa ser texto não vazio.`);
  if (!Array.isArray(value.plannedMethodology) || !value.plannedMethodology.length || !value.plannedMethodology.every((item) => isObject(item) && typeof item.title === "string" && typeof item.detail === "string")) throw new Error("Metadado do showroom inválido: 'plannedMethodology' precisa conter etapas documentadas.");
  for (const key of ["proposalReference", "glossFreeReference"]) if (!isObject(value[key]) || typeof value[key].label !== "string" || typeof value[key].href !== "string") throw new Error(`Metadado do showroom inválido: '${key}' precisa informar label e href.`);
  if (!Array.isArray(value.pipeline) || value.pipeline.length === 0 || !value.pipeline.every((item) => isObject(item) && typeof item.title === "string" && typeof item.detail === "string")) throw new Error("Metadado do showroom inválido: 'pipeline' precisa conter etapas com title e detail.");
  return value as ShowroomProject;
}
function validateExecutionReport(latest: JsonObject): void {
  if (latest.schema_version !== undefined && latest.schema_version !== "execution-report.v1") throw new Error(`Schema de relatório não suportado: ${String(latest.schema_version)}.`);
  if (typeof latest.dataset !== "string" || !latest.dataset.trim()) throw new Error("artifacts/reports/latest.json precisa informar dataset.");
  if (typeof latest.decision !== "string" || !latest.decision.trim()) throw new Error("artifacts/reports/latest.json precisa informar decision.");
  if (!isObject(latest.technical_summary) || typeof latest.technical_summary.videos_seen !== "number") throw new Error("artifacts/reports/latest.json precisa conter technical_summary.videos_seen numérico.");
  if (!isObject(latest.quality_counts)) throw new Error("artifacts/reports/latest.json precisa conter quality_counts como objeto.");
}
function validateDatasetSummary(item: JsonObject, file: string): void {
  if (item.schema_version !== undefined && item.schema_version !== "dataset-validation-summary.v1") throw new Error(`${file} usa um schema não suportado: ${String(item.schema_version)}.`);
  if (typeof item.dataset !== "string" || !item.dataset.trim()) throw new Error(`${file} precisa informar dataset.`);
  if (typeof item.decision !== "string" || !item.decision.trim()) throw new Error(`${file} precisa informar decision.`);
  if (!isObject(item.counts) || !isObject(item.counts.by_severity)) throw new Error(`${file} precisa conter counts.by_severity.`);
}
async function writeText(file: string, content: string): Promise<void> {
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, `${content.trimEnd()}\n`, "utf8");
}
function number(value: unknown): string {
  if (value == null || value === "") return "—";
  const parsed = Number(value);
  return Number.isFinite(parsed) ? new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(Math.trunc(parsed)) : esc(value);
}
function countLabel(value: unknown, singular: string, plural: string): string {
  const parsed = Number(value);
  return `${number(value)} ${parsed === 1 ? singular : plural}`;
}
function date(value: unknown): string {
  if (!value) return "Ainda não registrado";
  const parsed = new Date(String(value));
  if (Number.isNaN(parsed.getTime())) return esc(value);
  const parts = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23", timeZone: "America/Sao_Paulo", timeZoneName: "short" }).formatToParts(parsed);
  const get = (type: Intl.DateTimeFormatPartTypes) => parts.find((part) => part.type === type)?.value ?? "";
  return `${get("day")}/${get("month")}/${get("year")} às ${get("hour")}:${get("minute")} ${get("timeZoneName")}`;
}
function timeElement(value: unknown): string {
  if (!value) return "Ainda não registrado";
  const raw = String(value);
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return esc(raw);
  return `<time datetime="${esc(raw)}">${date(raw)}</time>`;
}
function datasetLabel(dataset: unknown): string {
  const value = String(dataset ?? "");
  if (value === "minds-libras-raw") return "MINDS-Libras";
  if (value === "v-librasil-raw") return "V-LIBRASIL";
  return esc(value);
}
function statusClass(value: unknown): string {
  return ({ GO: "good", PASS: "good", PARTIAL: "warn", "NO-GO": "bad", FAIL: "bad" } as Record<string, string>)[String(value)] ?? "neutral";
}
function page(title: string, body: string, prefix = "", currentPage = ""): string {
  const technicalNavigation = [
    ["architecture", "Arquitetura", "architecture/index.html"],
    ["datasets", "Datasets", "datasets/index.html"],
    ["validation", "Validação", "validation/index.html"],
    ["executions", "Execuções", "executions/index.html"],
    ["reports", "Relatório", "reports/latest.html"],
    ["presentations", "Apresentações", "apresentacoes/index.html"],
  ] as const;
  const researchNavigation = [
    ["research", "A pesquisa", "#pesquisa"],
    ["methodology", "Metodologia", "#metodologia"],
    ["datasets", "Dados", "#datasets"],
    ["experiments", "Resultados", "#experimentos"],
    ["progress", "Evolução", "#andamento"],
    ["technical", "Acompanhamento técnico", "#tecnico"],
    ["presentations", "Apresentações", "apresentacoes/index.html"],
  ] as const;
  const navigation = currentPage === "home" ? researchNavigation : technicalNavigation;
  const navLinks = navigation.map(([key, label, href]) => `<a href="${prefix}${href}"${currentPage === key ? ' aria-current="page"' : ""}>${label}</a>`).join("");
  return `<!doctype html>
<html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Portal científico da dissertação sobre representações visuais para tradução de Libras em português escrito.">
<meta name="theme-color" content="#f5f6f2">
<title>${esc(title)} · Pesquisa de tradução de Libras</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=Space+Mono:wght@400;700&display=swap">
<link rel="stylesheet" href="${prefix}assets/style.css">
</head><body>
<a class="skip-link" href="#main-content">Pular para o conteúdo</a>
<header class="topbar"><a class="brand" href="${prefix}index.html"${currentPage === "home" ? ' aria-current="page"' : ""}><svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true"><path d="M4 20c5 0 5-9 11-9s6 10 13 10"/><circle cx="5" cy="20" r="2"/><circle cx="27" cy="21" r="2"/></svg><span>Pesquisa em tradução de Libras</span></a>
<nav aria-label="Navegação principal">${navLinks}</nav></header>
<main id="main-content" tabindex="-1">${body}</main><footer class="footer">Portal de pesquisa · os vídeos originais não são publicados aqui</footer>
</body></html>`;
}
function severityGrid(values: JsonObject): string {
  return severities.map((key) => `<div class="severity severity-${key.toLowerCase()}"><strong>${number(values[key] ?? 0)}</strong><span>${key}</span></div>`).join("");
}
async function collectSummaries(metadataRoot: string): Promise<Map<string, JsonObject>> {
  const found = new Map<string, JsonObject>();
  for (const entry of await readdir(metadataRoot, { withFileTypes: true }).catch(() => [])) {
    if (!entry.isDirectory()) continue;
    const file = path.join(metadataRoot, entry.name, "reports", "metadata_summary.json");
    if (!(await Bun.file(file).exists())) continue;
    const item = await loadJson(file);
    validateDatasetSummary(item, file);
    found.set(item.dataset, item);
  }
  const legacyPath = path.join(metadataRoot, "reports", "metadata_summary.json");
  if (await Bun.file(legacyPath).exists()) {
    const legacy = await loadJson(legacyPath);
    validateDatasetSummary(legacy, legacyPath);
    if (!found.has(legacy.dataset)) found.set(legacy.dataset, legacy);
  }
  if (!found.size) throw new Error(`Nenhum metadata_summary.json válido encontrado em ${metadataRoot}.`);
  return found;
}
async function collectPublishedSummaries(reportsRoot: string): Promise<Map<string, JsonObject> | null> {
  const publicationRoot = path.join(reportsRoot, "publications");
  const indexFile = path.join(publicationRoot, "index.json");
  if (!(await Bun.file(indexFile).exists())) return null;
  const index = await loadJson(indexFile);
  if (index.schema_version !== "research-presentation-index.v1" || typeof index.latest_release !== "string" || !Array.isArray(index.releases)) {
    throw new Error("artifacts/reports/publications/index.json tem schema inválido.");
  }
  const release = index.releases.find((item: JsonObject) => item.id === index.latest_release);
  if (!isObject(release) || typeof release.snapshot !== "string" || path.basename(release.snapshot) !== release.snapshot) {
    throw new Error("O release mais recente não aponta para um snapshot local válido.");
  }
  const snapshotFile = path.join(publicationRoot, release.snapshot);
  const snapshot = await loadJson(snapshotFile);
  if (snapshot.schema_version !== "research-presentation-evidence.v1" || snapshot.release_id !== release.id || !Array.isArray(snapshot.datasets)) {
    throw new Error(`${snapshotFile} não é um snapshot de evidências compatível.`);
  }
  const summaries = new Map<string, JsonObject>();
  for (const item of snapshot.datasets) {
    if (!isObject(item)) throw new Error(`${snapshotFile} contém um registro de dataset inválido.`);
    validateDatasetSummary(item, snapshotFile);
    if (summaries.has(item.dataset)) throw new Error(`${snapshotFile} repete o dataset '${item.dataset}'.`);
    summaries.set(item.dataset, item);
  }
  if (summaries.size === 0) throw new Error(`${snapshotFile} não contém datasets.`);
  return summaries;
}
function makeView(dataset: string, summary: JsonObject, latest: JsonObject): JsonObject {
  const counts = summary.counts ?? {};
  const key = summary.key_reconciliation ?? {};
  const severity = counts.by_severity ?? {};
  const technical = latest.dataset === dataset ? latest.technical_summary ?? {} : {};
  return {
    dataset,
    decision: summary.decision ?? latest.decision ?? "UNKNOWN",
    generated_at: summary.generated_at_utc,
    videos: counts.physical_videos ?? technical.videos_seen,
    annotations: counts.annotations ?? key.csv_records,
    manifest_rows: counts.manifest_rows,
    issues: counts.issues,
    severity: Object.fromEntries(severities.map((name) => [name, severity[name] ?? 0])),
    matched: key.matched, missing: key.missing, extra: key.extra,
    key_column: key.filesystem_key_column,
    fps: technical.dataset_fps_interpretation,
  };
}
function datasetDashboardCard(item: JsonObject): string {
  const severity = item.severity ?? {};
  const findings = severities.filter((name) => severity[name]).map((name) => `<span class="finding finding-${name.toLowerCase()}">${number(severity[name])} ${name}</span>`).join("") || '<span class="finding">Sem issues registradas</span>';
  let findingText: string;
  if (item.matched != null) findingText = `${number(item.matched)} chaves correspondem aos arquivos físicos; ${number(item.missing)} ausentes e ${number(item.extra)} extras.`;
  else if (item.manifest_rows != null && item.annotations != null) {
    const delta = Number(item.manifest_rows) - Number(item.annotations);
    findingText = delta ? `O manifest tem ${number(Math.abs(delta))} linhas ${delta > 0 ? "a mais" : "a menos"} que annotations.csv; a reconciliação permanece pendente.` : "O relatório não registra a reconciliação detalhada da chave física.";
  } else findingText = "Veja o relatório de validação para o detalhe desta auditoria.";
  const title = datasetLabel(item.dataset);
  return `<article class="dataset-audit ${statusClass(item.decision)}">
  <div class="card-top"><div><h3>${title}</h3><code class="dataset-id">${esc(item.dataset)}</code></div><span class="status ${statusClass(item.decision)}">${esc(item.decision)}</span></div>
  <div class="audit-metrics"><div class="audit-metric"><strong>${number(item.videos)}</strong><span>vídeos físicos registrados</span></div><div class="audit-metric"><strong>${number(item.annotations)}</strong><span>registros CSV</span></div><div class="audit-metric"><strong>${number(item.manifest_rows)}</strong><span>linhas no manifest</span></div></div>
  <div class="audit-severity">${findings}</div><p class="audit-finding">${findingText}</p>
  <div class="audit-meta"><span>Relatório de ${timeElement(item.generated_at)}</span><a href="validation/index.html#${esc(item.dataset)}">Abrir auditoria →</a></div></article>`;
}
function reportPage(latest: JsonObject, reportText: string, project: ShowroomProject): string {
  const technical = latest.technical_summary ?? {};
  const quality = latest.quality_counts ?? {};
  const decision = latest.decision ?? "—";
  const fps = technical.dataset_fps_interpretation ?? "sem conclusão";
  return `<section class="report-hero"><div><h1>O que esta validação permite concluir</h1><p><strong>Foco do projeto:</strong> ${esc(project.researchFocus)}</p><p>${esc(project.validationPurpose)}</p></div><div class="report-decision ${statusClass(decision)}"><span>Decisão de integridade</span><strong>${esc(decision)}</strong><small>${esc(latest.dataset ?? "dataset não informado")}<br>${timeElement(latest.executed_at)}</small></div></section>
<section class="section report-summary" aria-labelledby="report-summary-title"><h2 id="report-summary-title">Esta execução em números</h2><dl><div><dt>Vídeos examinados</dt><dd>${number(technical.videos_seen)}</dd></div><div><dt>Vídeos com leitura técnica OK</dt><dd>${number(technical.videos_ok)}</dd></div><div><dt>Erros de leitura</dt><dd>${number(technical.videos_with_probe_error)}</dd></div></dl></section>
<section class="section report-layout"><article class="report-section"><h2>O que foi conferido</h2><dl class="report-list"><div><dt>Dimensões</dt><dd>${number(technical.width_matches)} largura · ${number(technical.height_matches)} altura</dd></div><div><dt>FPS</dt><dd>${esc(fps)}</dd></div><div><dt>Comparação por frames</dt><dd>${number(technical.fps_frame_count_matches)} correspondências</dd></div><div><dt>Comparação por taxa</dt><dd>${number(technical.fps_rate_matches)} correspondências</dd></div></dl></article><article class="report-section"><h2>Severidades encontradas</h2><div class="severity-grid">${severityGrid(quality)}</div><p class="muted">As contagens vêm de <code>metadata_summary.json</code> e permanecem auditáveis nos artefatos técnicos.</p></article></section>
<section class="section report-section report-conclusion"><h2>No dataset desta execução, o campo <code>fps</code> foi interpretado como ${esc(fps)}.</h2><p>O resultado é evidência sobre os metadados deste dataset, não sobre outros conjuntos nem sobre o desempenho de tradução.</p><p>${esc(project.interpretationLimit)}</p><a class="text-link" href="../validation/index.html">Consultar auditorias e achados por dataset →</a></section>
<details class="section raw-report"><summary>Ver o texto original do relatório</summary><pre>${esc(reportText)}</pre></details>`;
}

function assertShowroomNarrative(homeHtml: string, reportHtml: string, project: ShowroomProject, latest: JsonObject, reportText: string): void {
  const checks: Array<[string, string, string]> = [
    ["homepage", homeHtml, '<nav aria-label="Navegação principal">'],
    ["homepage", homeHtml, 'href="#metodologia"'],
    ["homepage", homeHtml, 'href="#datasets"'],
    ["homepage", homeHtml, 'href="#tecnico"'],
    ["homepage", homeHtml, `<h1 id="page-title">${esc(project.displayTitle)}</h1>`],
    ["homepage", homeHtml, esc(project.problemContext)],
    ["homepage", homeHtml, esc(project.researchFocus)],
    ["homepage", homeHtml, esc(project.glossFreeExplanation)],
    ["homepage", homeHtml, esc(project.validationPurpose)],
    ["homepage", homeHtml, esc(project.interpretationLimit)],
    ["homepage", homeHtml, "não aparecem formalizadas"],
    ["homepage", homeHtml, 'id="metodologia"'],
    ["homepage", homeHtml, esc(project.plannedMethodology[0].title)],
    ["homepage", homeHtml, esc(project.proposalReference.href)],
    ["homepage", homeHtml, esc(project.glossFreeReference.href)],
    ["homepage", homeHtml, "Implementado e evidenciado"],
    ["homepage", homeHtml, 'id="datasets"'],
    ["homepage", homeHtml, "Como interpretar GO, NO-GO e manifest"],
    ["homepage", homeHtml, 'id="experimentos"'],
    ["homepage", homeHtml, "não apresentam baselines"],
    ["homepage", homeHtml, 'id="andamento"'],
    ["homepage", homeHtml, esc(project.nextStep)],
    ["homepage", homeHtml, 'id="tecnico"'],
    ["homepage", homeHtml, 'href="validation/index.html"'],
    ["homepage", homeHtml, 'href="reports/latest.html"'],
    ["relatório detalhado", reportHtml, "O que esta validação permite concluir"],
    ["relatório detalhado", reportHtml, esc(project.researchFocus)],
    ["relatório detalhado", reportHtml, esc(project.validationPurpose)],
    ["relatório detalhado", reportHtml, esc(project.interpretationLimit)],
    ["relatório detalhado", reportHtml, esc(latest.dataset)],
    ["relatório detalhado", reportHtml, esc(latest.decision)],
    ["relatório detalhado", reportHtml, `<dt>Vídeos examinados</dt><dd>${number(latest.technical_summary?.videos_seen)}</dd>`],
    ["relatório detalhado", reportHtml, `<dt>Vídeos com leitura técnica OK</dt><dd>${number(latest.technical_summary?.videos_ok)}</dd>`],
    ["relatório detalhado", reportHtml, `<dt>Erros de leitura</dt><dd>${number(latest.technical_summary?.videos_with_probe_error)}</dd>`],
    ["relatório detalhado", reportHtml, esc(latest.technical_summary?.dataset_fps_interpretation ?? "sem conclusão")],
    ["relatório detalhado", reportHtml, 'href="../validation/index.html"'],
    ["relatório detalhado", reportHtml, "Ver o texto original do relatório"],
    ["relatório detalhado", reportHtml, esc(reportText)],
  ];
  const missing = checks.filter(([, html, expected]) => !html.includes(expected)).map(([pageName, , expected]) => pageName + ": " + expected);
  if (missing.length) throw new Error("O showroom não atende ao contrato científico e de evidências: " + missing.join("; "));
}

export async function buildShowroom(repoRoot: string): Promise<JsonObject> {
  const paths = createHarnessPaths(path.join(repoRoot, "harness"));
  const artifacts = paths.artifactsRoot;
  const metadata = paths.metadataValidationRoot;
  const docs = paths.docsRoot;
  const project = validateProjectMetadata(await loadJson(path.join(paths.assetsRoot, "showroom-project.json")));
  const latest = await loadJson(path.join(paths.reportsRoot, "latest.json"));
  validateExecutionReport(latest);
  const reportText = await readFile(path.join(paths.reportsRoot, "latest.md"), "utf8");
  if (!reportText.trim()) throw new Error("artifacts/reports/latest.md está vazio.");
  const summaries = await collectPublishedSummaries(paths.reportsRoot) ?? await collectSummaries(metadata);
  const datasetItems = [...summaries.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([name, item]) => makeView(name, item, latest));
  if (!datasetItems.some((item) => item.dataset === latest.dataset)) throw new Error(`O dataset '${latest.dataset}' de latest.json não possui metadata_summary correspondente.`);
  const architectureSource = paths.architectureHtmlRoot;
  const architectureFiles = (await readdir(architectureSource, { withFileTypes: true }).catch(() => []))
    .filter((entry) => entry.isFile() && entry.name.endsWith(".html")).map((entry) => entry.name).sort();
  const publicArchitecture = path.join(docs, "architecture");
  await mkdir(publicArchitecture, { recursive: true });
  for (const old of await readdir(publicArchitecture).catch(() => [])) if (old.endsWith(".html")) await rm(path.join(publicArchitecture, old));
  for (const name of architectureFiles) await copyFile(path.join(architectureSource, name), path.join(publicArchitecture, name));

  const siteData = { schema_version: "showroom.v1", generated_at: new Date().toISOString(), latest, datasets: datasetItems, architecture: architectureFiles, scope: "Pesquisa, validação dos datasets e evidências disponíveis no projeto" };
  await writeText(path.join(docs, "data", "showroom.json"), JSON.stringify(siteData, null, 2));
  const current = latest.dataset ?? datasetItems[0]?.dataset ?? "nenhum dataset";
  const technical = latest.technical_summary ?? {};
  const quality = latest.quality_counts ?? {};
  const totalVideos = datasetItems.reduce((sum, item) => sum + Number(item.videos || 0), 0);
  const totalManifestRows = datasetItems.reduce((sum, item) => sum + Number(item.manifest_rows || 0), 0);
  const goCount = datasetItems.filter((item) => item.decision === "GO").length;
  const noGoCount = datasetItems.filter((item) => item.decision === "NO-GO").length;
  const auditCards = datasetItems.map(datasetDashboardCard).join("") || '<p class="empty">Ainda não há relatórios de validação para exibir.</p>';
  const totalIssues = datasetItems.reduce((sum, item) => sum + Number(item.issues || 0), 0);
  const pipeline = project.pipeline.map((step) => `<li class="path-step"><strong>${esc(step.title)}</strong><p>${esc(step.detail)}</p></li>`).join("");
  const plannedMethodology = project.plannedMethodology.map((step) => `<li><span class="stage-status">Previsto na proposta</span><h3>${esc(step.title)}</h3><p>${esc(step.detail)}</p></li>`).join("");
  const validationSummary = `${number(datasetItems.length)} datasets têm resumos de auditoria publicados: ${goCount} GO e ${noGoCount} NO-GO, com evidências geradas em datas diferentes.`;
  const auditHistory = [...datasetItems].sort((left, right) => Date.parse(String(right.generated_at ?? "")) - Date.parse(String(left.generated_at ?? ""))).map((item) => `<li><div class="milestone-meta">${timeElement(item.generated_at)}<span class="status ${statusClass(item.decision)}">${esc(item.decision)}</span></div><div><h3>${datasetLabel(item.dataset)}</h3><p>${number(item.videos)} arquivos de vídeo registrados · ${countLabel(item.issues, "apontamento", "apontamentos")} na auditoria</p></div><a href="validation/index.html#${esc(item.dataset)}">Ver evidência</a></li>`).join("") || '<li class="empty">Nenhuma auditoria publicada.</li>';
  const technicalLinks = [
    ["architecture/index.html", "Fluxo de dados", "Diagrama Archify da aquisição e da validação; não descreve a arquitetura de um modelo de tradução."],
    ["datasets/index.html", "Inventário de datasets", "Contagens e reconciliação resumidas por conjunto."],
    ["validation/index.html", "Auditorias", "Achados de integridade, severidade e proveniência."],
    ["executions/index.html", "Execuções", "Registros de execução disponíveis no showroom."],
    ["reports/latest.html", "Relatório mais recente", "Detalhes da última validação e seus limites."],
    ["apresentacoes/index.html", "Apresentações", "Versões de acompanhamento da pesquisa."],
  ].map(([href, label, detail]) => `<li><a href="${href}">${label}</a><span>${detail}</span></li>`).join("");
  const home = `<section class="project-hero" id="pesquisa" aria-labelledby="page-title"><div class="project-copy"><h1 id="page-title">${esc(project.displayTitle)}</h1><p class="project-subtitle">${esc(project.title)}</p><p class="hero-lede">${esc(project.summary)}</p><div class="hero-actions"><a class="button button-primary" href="#metodologia">Conhecer o método</a><a class="button button-quiet" href="#datasets">Ver evidências dos dados</a></div></div>
  <div class="research-path"><h2 id="research-flow-title">Do vídeo ao texto</h2><ol aria-labelledby="research-flow-title">${pipeline}</ol><p class="muted">Fluxo conceitual da tarefa; a etapa de tradução ainda não tem resultados publicados neste portal.</p></div></section>
<section class="research-context" id="problema" aria-labelledby="problem-title"><div class="research-overview"><h2 id="problem-title">O problema e o objetivo científico</h2><p>${esc(project.problemContext)}</p><p><strong>Objetivo da dissertação:</strong> ${esc(project.researchFocus)}</p><div class="gloss-definition"><h3>O que significa “sem glosas”?</h3><p>${esc(project.glossFreeExplanation)}</p><p class="source-note">Referência para o conceito: <a href="${esc(project.glossFreeReference.href)}">${esc(project.glossFreeReference.label)}</a>. Este trabalho é citado como referência conceitual, não como resultado da dissertação.</p></div><p class="research-note"><strong>Questões e hipóteses:</strong> não aparecem formalizadas na proposta e nas especificações consultadas.</p></div><aside class="context-meta"><h3>O que a etapa atual mede</h3><p>${esc(project.validationPurpose)}</p><p>${esc(project.interpretationLimit)}</p></aside></section>
<section class="section methodology-section" id="metodologia" aria-labelledby="methodology-title"><div class="section-heading"><div><h2 id="methodology-title">Metodologia proposta e estágio atual</h2><p class="section-intro">A proposta descreve linhas a investigar. Elas ainda não representam uma arquitetura de modelo escolhida ou implementada.</p></div></div><ol class="methodology-list">${plannedMethodology}</ol><p class="source-note">Frentes previstas na <a href="${esc(project.proposalReference.href)}">${esc(project.proposalReference.label)}</a>, documento de ${esc(project.proposalReference.date)}. A pesquisa considera pistas visuais do movimento, métodos de aprendizado espacial e temporal e relações multimodais entre vídeo e texto.</p><p class="method-status"><strong>Implementado e evidenciado:</strong> aquisição e validação técnica/de proveniência dos datasets. A execução mais recente foi registrada em ${timeElement(latest.executed_at)} para <code>${esc(latest.dataset)}</code>; os estados por dataset aparecem abaixo.</p><p class="method-architecture"><a class="text-link" href="architecture/index.html">Consultar o fluxo de aquisição e validação no Archify</a><span>O diagrama documenta o pipeline de dados existente, não a arquitetura de tradução proposta.</span></p></section>
<section class="section dataset-section" id="datasets" aria-labelledby="datasets-title"><div class="section-heading"><div><h2 id="datasets-title">Datasets e evidências disponíveis</h2><p class="section-intro">${esc(validationSummary)} Há ${number(totalVideos)} arquivos de vídeo registrados nos resumos; essa contagem não significa aprovação para experimentos.</p></div><a class="text-link" href="validation/index.html">Abrir todas as auditorias</a></div><details class="definition-note"><summary>Como interpretar GO, NO-GO e manifest</summary><dl><div><dt>GO</dt><dd>O relatório não encontrou ocorrências CRITICAL ou ERROR segundo os critérios configurados. Não mede qualidade de tradução.</dd></div><div><dt>NO-GO</dt><dd>O relatório encontrou ocorrências CRITICAL ou ERROR que precisam ser revistas.</dd></div><div><dt>Manifest</dt><dd>Inventário derivado de registros e arquivos validados; não substitui os dados originais.</dd></div></dl></details><div class="audit-grid">${auditCards}</div></section>
<section class="section experiment-status" id="experimentos" aria-labelledby="experiments-title"><h2 id="experiments-title">Experimentos e resultados de tradução</h2><p>Os relatórios atualmente publicados documentam qualidade e proveniência dos dados. Eles não apresentam baselines, comparação entre modelos nem métricas de tradução. Por isso, GO e NO-GO não são apresentados como resultados científicos do modelo.</p><p>O relatório da execução mais recente está disponível para consulta, com os parâmetros e os limites da evidência.</p><a class="text-link" href="reports/latest.html">Ler o relatório técnico mais recente</a></section>
<section class="section progress-section" id="andamento" aria-labelledby="progress-title"><div class="section-heading"><div><h2 id="progress-title">Evolução documentada</h2><p class="section-intro">Histórico das auditorias publicadas, ordenado pela data de cada evidência.</p></div><a class="text-link" href="executions/index.html">Ver execuções</a></div><ol class="milestone-list">${auditHistory}</ol><p class="next-step"><strong>Próxima frente registrada no README:</strong> ${esc(project.nextStep)}</p></section>
<section class="section technical-section" id="tecnico" aria-labelledby="technical-title"><h2 id="technical-title">Acompanhamento técnico</h2><p>Relatórios, auditorias e diagramas detalhados ficam nesta área; os dados originais permanecem fora do showroom.</p><ul class="artifact-list">${technicalLinks}</ul></section>`;
  const latestReportPage = page("Relatório", reportPage(latest, reportText, project), "../", "reports");
  assertShowroomNarrative(page("Início", home, "", "home"), latestReportPage, project, latest, reportText);
  await writeText(path.join(docs, "index.html"), page("Início", home, "", "home"));

  const archLinks = architectureFiles.map((name) => `<li><a href="${esc(name)}">${esc(path.parse(name).name.replaceAll("-", " "))}</a><span>HTML Archify</span></li>`).join("") || '<li class="empty">A arquitetura ainda não foi publicada.</li>';
  const architecture = `<section class="page-intro"><h1>Arquitetura do pipeline</h1><p>O diagrama Archify mostra o caminho principal entre pesquisador, CLI, aquisição, processamento audiovisual, validações e artefatos derivados.</p></section><section class="section feature-panel"><div><h2>Diagramas disponíveis</h2><p>Os arquivos são gerados a partir dos candidatos versionados em <code>harness/artifacts/architecture/source/</code>.</p></div><ul class="artifact-list">${archLinks}</ul></section><section class="section note"><strong>Como ler:</strong> a arquitetura representa componentes e responsabilidades; ela não substitui os relatórios nem publica os vídeos originais.</section>`;
  await writeText(path.join(docs, "architecture", "index.html"), page("Arquitetura", architecture, "../", "architecture"));

  const rows = datasetItems.map((item) => `<tr><th scope="row">${esc(item.dataset)}</th><td>${number(item.videos)}</td><td>${number(item.annotations)}</td><td>${number(item.matched)}</td><td>${number(item.missing)}</td><td>${number(item.extra)}</td><td><span class="status ${statusClass(item.decision)}">${esc(item.decision)}</span></td></tr>`).join("") || '<tr><td colspan="7" class="empty">Nenhum dataset validado foi publicado.</td></tr>';
  const datasets = `<section class="page-intro"><h1>Datasets e evidências disponíveis</h1><p>Esta página resume datasets com evidência derivada no projeto. Quantidade não significa qualidade; a reconciliação e os critérios da validação estão detalhados em cada resultado.</p></section><section class="section table-section"><div class="table-wrap" role="region" aria-label="Tabela de datasets e reconciliação" tabindex="0"><table><caption>Inventário de datasets com resumos técnicos publicados</caption><thead><tr><th scope="col">Dataset</th><th scope="col">Vídeos</th><th scope="col">CSV</th><th scope="col">Correspondentes</th><th scope="col">Ausentes</th><th scope="col">Extras</th><th scope="col">Decisão</th></tr></thead><tbody>${rows}</tbody></table></div></section>`;
  await writeText(path.join(docs, "datasets", "index.html"), page("Datasets", datasets, "../", "datasets"));

  const validationCards = datasetItems.map((item) => `<article class="validation-card" id="${esc(item.dataset)}"><div class="card-top"><code class="dataset-id">${esc(item.dataset)}</code><span class="status ${statusClass(item.decision)}">${esc(item.decision)}</span></div><h2>Reconciliação e qualidade</h2><div class="severity-grid">${severityGrid(item.severity)}</div><dl class="detail-list"><div><dt>Chave física</dt><dd>${esc(item.key_column || "não informada")}</dd></div><div><dt>Correspondentes</dt><dd>${number(item.matched)}</dd></div><div><dt>Ausentes</dt><dd>${number(item.missing)}</dd></div><div><dt>Extras</dt><dd>${number(item.extra)}</dd></div><div><dt>Manifest</dt><dd>${number(item.manifest_rows)}</dd></div><div><dt>FPS</dt><dd>${esc(item.fps || "não investigado")}</dd></div></dl><p class="muted">Evidência gerada em ${date(item.generated_at)}.</p></article>`).join("") || '<p class="empty">Nenhum resultado de validação foi publicado.</p>';
  const validation = `<section class="page-intro"><h1>Validação dos metadados</h1><p>A Etapa 1 verifica identidade dos arquivos, correspondência com o CSV e metadados técnicos. EDA, balanceamento e treinamento permanecem fora deste showroom.</p></section><section class="section latest-banner"><div><h2>Execução mais recente</h2><p>${esc(current)} · ${timeElement(latest.executed_at)} · decisão <strong>${esc(latest.decision ?? "—")}</strong></p></div><div class="severity-grid" aria-label="Issues por severidade">${severityGrid(quality)}</div></section><section class="section validation-grid">${validationCards}</section><section class="section note"><strong>FPS observado:</strong> ${esc(technical.dataset_fps_interpretation ?? "sem conclusão registrada")}. Correspondências com contagem de frames: ${number(technical.fps_frame_count_matches)}; com taxa real: ${number(technical.fps_rate_matches)}.</section><section class="section"><a class="button button-primary" href="../reports/latest.html">Ler o resumo completo</a></section>`;
  await writeText(path.join(docs, "validation", "index.html"), page("Validação", validation, "../", "validation"));

  const executionDir = path.join(artifacts, "reports", "executions");
  const executionFiles = (await readdir(executionDir, { withFileTypes: true }).catch(() => [])).filter((entry) => entry.isFile() && entry.name.endsWith(".md")).map((entry) => entry.name).sort().reverse();
  const executionRows = executionFiles.map((name) => `<tr><th scope="row"><code>${esc(path.parse(name).name)}</code></th><td>Resumo local mantido no harness; conteúdo não publicado nesta página.</td></tr>`).join("") || '<tr><td colspan="2" class="empty">Nenhuma execução histórica registrada.</td></tr>';
  const executions = `<section class="page-intro"><h1>Histórico de execuções</h1><p>O harness preserva resumos por execução. Esta página lista os registros locais e destaca o estado mais recente; os arquivos originais e o histórico bruto não são publicados aqui.</p></section><section class="section latest-banner"><div><h2>Estado mais recente</h2><p>${esc(current)} · ${timeElement(latest.executed_at)} · ${esc(latest.decision ?? "sem decisão")}</p></div><a class="button button-primary" href="../reports/latest.html">Abrir relatório atual</a></section><section class="section table-section"><h2>Registros locais</h2><div class="table-wrap" role="region" aria-label="Registros locais de execução" tabindex="0"><table><caption>Arquivos de histórico registrados no harness</caption><thead><tr><th scope="col">Execução</th><th scope="col">Disponibilidade</th></tr></thead><tbody>${executionRows}</tbody></table></div></section><section class="section note">Os vídeos e os arquivos originais permanecem fora do showroom.</section>`;
  await writeText(path.join(docs, "executions", "index.html"), page("Execuções", executions, "../", "executions"));
  await writeText(path.join(docs, "reports", "latest.html"), latestReportPage);
  await writeText(path.join(docs, "_config.yml"), "title: Pesquisa de tradução de Libras\ndescription: Portal científico da dissertação sobre representações visuais para tradução de Libras em português escrito.\nmarkdown: kramdown\nplugins: []\n");
  await writeText(path.join(docs, "assets", "style.css"), await readFile(path.join(paths.assetsRoot, "showroom.css"), "utf8"));
  return { docs_root: docs, datasets: datasetItems.length, architecture_files: architectureFiles.length };
}

if (import.meta.main) {
  let repoRoot = path.resolve(harnessRoot, "..");
  for (let index = 2; index < process.argv.length; index += 1) {
    if (process.argv[index] === "--repo-root") repoRoot = path.resolve(process.argv[++index] ?? repoRoot);
    else if (process.argv[index] === "--help" || process.argv[index] === "-h") {
      process.stdout.write("Usage: bun run core/scripts/build-showroom.ts [--repo-root <project-root>]\n");
      process.exit(0);
    } else throw new Error(`Unknown option: ${process.argv[index]}`);
  }
  try {
    process.stdout.write(`${JSON.stringify(await buildShowroom(repoRoot))}\n`);
  } catch (error) {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
  }
}
