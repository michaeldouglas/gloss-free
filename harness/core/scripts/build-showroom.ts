import path from "node:path";
import { mkdir, readdir, readFile, stat, writeFile, rm, copyFile } from "node:fs/promises";
import { createHarnessPaths, getHarnessPaths } from "../lib/paths.ts";

type JsonObject = Record<string, any>;
type ShowroomProject = {
  schema_version: "showroom-project.v1";
  title: string;
  summary: string;
  motivation: string;
  pipeline: Array<{ title: string; detail: string }>;
  methodology: string;
  evaluationMetrics: string[];
  approachTitle: string;
  approachSummary: string;
  inputs: string[];
  learning: string;
  evaluation: string;
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
  if (value.schema_version !== "showroom-project.v1") throw new Error("Metadado do showroom precisa usar schema_version showroom-project.v1.");
  const requiredStrings = ["title", "summary", "motivation", "methodology", "approachTitle", "approachSummary", "learning", "evaluation"];
  for (const key of requiredStrings) if (typeof value[key] !== "string" || !value[key].trim()) throw new Error(`Metadado do showroom inválido: '${key}' precisa ser texto não vazio.`);
  if (!Array.isArray(value.pipeline) || value.pipeline.length === 0 || !value.pipeline.every((item) => isObject(item) && typeof item.title === "string" && typeof item.detail === "string")) throw new Error("Metadado do showroom inválido: 'pipeline' precisa conter etapas com title e detail.");
  if (!Array.isArray(value.evaluationMetrics) || value.evaluationMetrics.length === 0 || !value.evaluationMetrics.every((item) => typeof item === "string" && item.trim())) throw new Error("Metadado do showroom inválido: 'evaluationMetrics' precisa conter métricas textuais.");
  if (!Array.isArray(value.inputs) || value.inputs.length === 0 || !value.inputs.every((item) => typeof item === "string" && item.trim())) throw new Error("Metadado do showroom inválido: 'inputs' precisa conter entradas textuais.");
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
function date(value: unknown): string {
  if (!value) return "Ainda não registrado";
  const parsed = new Date(String(value));
  if (Number.isNaN(parsed.getTime())) return esc(value);
  const parts = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }).formatToParts(parsed);
  const get = (type: Intl.DateTimeFormatPartTypes) => parts.find((part) => part.type === type)?.value ?? "";
  return `${get("day")}/${get("month")}/${get("year")} às ${get("hour")}:${get("minute")}`;
}
function statusClass(value: unknown): string {
  return ({ GO: "good", PASS: "good", PARTIAL: "warn", "NO-GO": "bad", FAIL: "bad" } as Record<string, string>)[String(value)] ?? "neutral";
}
function page(title: string, body: string, prefix = ""): string {
  return `<!doctype html>
<html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Showroom do projeto de dissertação sobre Libras.">
<title>${esc(title)} · Libras Research Showroom</title>
<link rel="stylesheet" href="${prefix}assets/style.css">
</head><body>
<header class="topbar"><a class="brand" href="${prefix}index.html"><span class="brand-mark">∿</span>Pesquisa em tradução de Libras</a>
<nav aria-label="Navegação principal"><a href="${prefix}architecture/index.html">Arquitetura</a><a href="${prefix}datasets/index.html">Datasets</a><a href="${prefix}validation/index.html">Validação</a><a href="${prefix}executions/index.html">Execuções</a></nav></header>
<main>${body}</main><footer class="footer">Artefato derivado do projeto · dados brutos não publicados</footer>
</body></html>`;
}
function metric(label: string, value: unknown): string { return `<div class="metric"><strong>${number(value)}</strong><span>${esc(label)}</span></div>`; }
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
function datasetCard(item: JsonObject, validationHref = "../validation/index.html"): string {
  return `<article class="dataset-card"><div class="card-top"><span class="tag">dataset</span><span class="status ${statusClass(item.decision)}">${esc(item.decision)}</span></div>
<h3>${esc(item.dataset)}</h3><p class="muted">Última evidência: ${date(item.generated_at)}</p>
<div class="mini-metrics"><span><strong>${number(item.videos)}</strong> vídeos</span><span><strong>${number(item.annotations)}</strong> registros</span><span><strong>${number(item.issues)}</strong> issues</span></div>
<a class="text-link" href="${validationHref}#${esc(item.dataset)}">Ver validação</a></article>`;
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
  const title = item.dataset === "minds-libras-raw" ? "MINDS-Libras" : item.dataset === "v-librasil-raw" ? "V-LIBRASIL" : esc(item.dataset);
  return `<article class="dataset-audit ${statusClass(item.decision)}">
  <div class="card-top"><div><p class="section-kicker">${esc(item.dataset)}</p><h3>${title}</h3></div><span class="status ${statusClass(item.decision)}">${esc(item.decision)}</span></div>
  <div class="audit-metrics"><div class="audit-metric"><strong>${number(item.videos)}</strong><span>vídeos físicos</span></div><div class="audit-metric"><strong>${number(item.annotations)}</strong><span>registros CSV</span></div><div class="audit-metric"><strong>${number(item.manifest_rows)}</strong><span>linhas no manifest</span></div></div>
  <div class="audit-severity">${findings}</div><p class="audit-finding">${findingText}</p>
  <div class="audit-meta"><span>Relatório de ${date(item.generated_at)}</span><a href="validation/index.html#${esc(item.dataset)}">Abrir auditoria →</a></div></article>`;
}
function reportPage(latest: JsonObject, reportText: string): string {
  const technical = latest.technical_summary ?? {};
  const quality = latest.quality_counts ?? {};
  const decision = latest.decision ?? "—";
  const fps = technical.dataset_fps_interpretation ?? "sem conclusão";
  return `<section class="report-hero"><div><p class="eyebrow">Relatório derivado</p><h1>Execução em foco</h1><p>Uma leitura organizada da última validação registrada pelo notebook, com a decisão primeiro e os detalhes técnicos logo depois.</p></div><div class="report-decision ${statusClass(decision)}"><span>Decisão registrada</span><strong>${esc(decision)}</strong><small>${esc(latest.dataset ?? "dataset não informado")}<br>${date(latest.executed_at)}</small></div></section>
<section class="report-kpis">${metric("vídeos vistos", technical.videos_seen)}${metric("vídeos aprovados", technical.videos_ok)}${metric("erros de probe", technical.videos_with_probe_error)}${metric("issues INFO", quality.INFO ?? 0)}</section>
<section class="section report-layout"><article class="report-section"><p class="section-kicker">Resultado técnico</p><h2>O que foi conferido</h2><dl class="report-list"><div><dt>Dimensões</dt><dd>${number(technical.width_matches)} largura · ${number(technical.height_matches)} altura</dd></div><div><dt>FPS</dt><dd>${esc(fps)}</dd></div><div><dt>Comparação por frames</dt><dd>${number(technical.fps_frame_count_matches)} correspondências</dd></div><div><dt>Comparação por taxa</dt><dd>${number(technical.fps_rate_matches)} correspondências</dd></div></dl></article><article class="report-section"><p class="section-kicker">Qualidade</p><h2>Severidades encontradas</h2><div class="severity-grid">${severityGrid(quality)}</div><p class="muted">As contagens vêm de <code>metadata_summary.json</code> e permanecem auditáveis nos artefatos técnicos.</p></article></section>
<section class="section report-section report-conclusion"><p class="section-kicker">Leitura principal</p><h2>O campo <code>fps</code> foi interpretado como ${esc(fps)}.</h2><p>Essa conclusão é específica do dataset desta execução. Ela não deve ser transferida automaticamente para outros datasets.</p></section>
<details class="section raw-report"><summary>Ver o texto original do relatório</summary><pre>${esc(reportText)}</pre></details>`;
}

export async function buildShowroom(repoRoot: string): Promise<JsonObject> {
  const paths = createHarnessPaths(path.join(repoRoot, "harness"));
  const harness = paths.harnessRoot;
  const artifacts = paths.artifactsRoot;
  const metadata = paths.metadataValidationRoot;
  const docs = paths.docsRoot;
  const project = validateProjectMetadata(await loadJson(path.join(paths.assetsRoot, "showroom-project.json")));
  const latest = await loadJson(path.join(paths.reportsRoot, "latest.json"));
  validateExecutionReport(latest);
  const reportText = await readFile(path.join(paths.reportsRoot, "latest.md"), "utf8");
  if (!reportText.trim()) throw new Error("artifacts/reports/latest.md está vazio.");
  const summaries = await collectSummaries(metadata);
  const datasetItems = [...summaries.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([name, item]) => makeView(name, item, latest));
  if (!datasetItems.some((item) => item.dataset === latest.dataset)) throw new Error(`O dataset '${latest.dataset}' de latest.json não possui metadata_summary correspondente.`);
  const architectureSource = paths.architectureHtmlRoot;
  const architectureFiles = (await readdir(architectureSource, { withFileTypes: true }).catch(() => []))
    .filter((entry) => entry.isFile() && entry.name.endsWith(".html")).map((entry) => entry.name).sort();
  const publicArchitecture = path.join(docs, "architecture");
  await mkdir(publicArchitecture, { recursive: true });
  for (const old of await readdir(publicArchitecture).catch(() => [])) if (old.endsWith(".html")) await rm(path.join(publicArchitecture, old));
  for (const name of architectureFiles) await copyFile(path.join(architectureSource, name), path.join(publicArchitecture, name));

  const siteData = { schema_version: "showroom.v1", generated_at: new Date().toISOString(), latest, datasets: datasetItems, architecture: architectureFiles, scope: "Validação dos datasets e evidências disponíveis no projeto" };
  await writeText(path.join(docs, "data", "showroom.json"), JSON.stringify(siteData, null, 2));
  const current = latest.dataset ?? datasetItems[0]?.dataset ?? "nenhum dataset";
  const technical = latest.technical_summary ?? {};
  const quality = latest.quality_counts ?? {};
  const totalVideos = datasetItems.reduce((sum, item) => sum + Number(item.videos || 0), 0);
  const totalManifestRows = datasetItems.reduce((sum, item) => sum + Number(item.manifest_rows || 0), 0);
  const goCount = datasetItems.filter((item) => item.decision === "GO").length;
  const noGoCount = datasetItems.filter((item) => item.decision === "NO-GO").length;
  const severityTotals = Object.fromEntries(severities.map((name) => [name, datasetItems.reduce((sum, item) => sum + Number(item.severity?.[name] || 0), 0)]));
  const auditCards = datasetItems.map(datasetDashboardCard).join("") || '<p class="empty">Ainda não há relatórios de validação para exibir.</p>';
  const flowIcons = ["◉", "⌁", "Aa"];
  const pipeline = project.pipeline.map((step, index) => `<div class="path-step"><span class="path-icon ${index === 1 ? "path-icon-middle" : index === project.pipeline.length - 1 ? "path-icon-end" : ""}">${esc(flowIcons[index] ?? "•")}</span><div><strong>${esc(step.title)}</strong><small>${esc(step.detail)}</small></div></div>`).join('<span class="path-connector"></span>');
  const validationSummary = `Resultados derivados: ${goCount} GO e ${noGoCount} NO-GO, conforme os metadata_summary.json publicados.`;
  const home = `<section class="project-hero"><div class="project-copy"><p class="eyebrow">Projeto de dissertação · Libras → português escrito</p><h1>${esc(project.title)}</h1><p class="hero-lede">${esc(project.summary)}</p><div class="hero-actions"><a class="button button-primary" href="architecture/index.html">Explorar a arquitetura</a><a class="button button-quiet" href="datasets/index.html">Ver os datasets</a></div></div>
  <div class="research-path" aria-label="Fluxo de pesquisa proposto"><p class="path-heading">Fluxo de pesquisa</p>${pipeline}</div></section>
<section class="research-context"><div><p class="section-kicker">Contexto da pesquisa</p><p>${esc(project.motivation)}</p></div><div class="context-meta"><span>${esc(project.methodology)}</span><span>${project.evaluationMetrics.map(esc).join(" · ")}</span></div></section>
<section class="dashboard section"><div class="section-heading"><div><p class="section-kicker">Retrato dos dados</p><h2>O que já temos</h2></div><a class="text-link" href="datasets/index.html">Detalhes dos datasets</a></div><div class="dashboard-metrics">${metric("datasets catalogados", datasetItems.length)}${metric("vídeos físicos registrados", totalVideos)}${metric("linhas nos manifests", totalManifestRows)}<div class="metric decision-metric"><strong>${goCount} GO <span>·</span> ${noGoCount} NO-GO</strong><span>decisões dos relatórios disponíveis</span></div></div><div class="dashboard-note"><strong>${Object.values(severityTotals).reduce((a, b) => a + Number(b), 0)} ocorrências</strong> registradas nos relatórios. ${esc(validationSummary)} As auditorias foram geradas em datas diferentes; cada cartão informa a data da própria evidência.</div></section>
<section class="section"><div class="section-heading"><div><p class="section-kicker">Auditorias disponíveis</p><h2>Um dataset por vez</h2></div><a class="text-link" href="validation/index.html">Abrir resultados completos</a></div><div class="audit-grid">${auditCards}</div></section>
<section class="section research-plan"><div><p class="section-kicker">Abordagem investigada</p><h2>${esc(project.approachTitle)}</h2><p>${esc(project.approachSummary)}</p></div><div class="method-list"><div><strong>Entradas</strong><span>${project.inputs.map(esc).join(" · ")}</span></div><div><strong>Aprendizado</strong><span>${esc(project.learning)}</span></div><div><strong>Avaliação</strong><span>${esc(project.evaluation)}</span></div></div></section>
<section class="section next-section"><div class="section-heading"><div><p class="section-kicker">Explore o projeto</p><h2>Entre pelos resultados ou pelo sistema.</h2></div></div><div class="next-grid"><a href="architecture/index.html"><strong>Arquitetura</strong><span>Como o pipeline de aquisição e validação se conecta.</span></a><a href="validation/index.html"><strong>Validação</strong><span>Chaves, vídeos, metadados técnicos e questões em aberto.</span></a><a href="executions/index.html"><strong>Execuções</strong><span>Relatórios e histórico das rodadas registradas.</span></a></div></section>`;
  await writeText(path.join(docs, "index.html"), page("Início", home));

  const archLinks = architectureFiles.map((name) => `<li><a href="${esc(name)}">${esc(path.parse(name).name.replaceAll("-", " "))}</a><span>HTML Archify</span></li>`).join("") || '<li class="empty">A arquitetura ainda não foi publicada.</li>';
  const architecture = `<section class="page-intro"><p class="eyebrow">Mapa do sistema</p><h1>Arquitetura do pipeline</h1><p>O diagrama Archify mostra o caminho principal entre pesquisador, CLI, aquisição, processamento audiovisual, validações e artefatos derivados.</p></section><section class="section feature-panel"><div><p class="section-kicker">Diagrama interativo</p><h2>Escolha uma visão</h2><p>Os arquivos são gerados a partir dos candidatos versionados em <code>harness/artifacts/architecture/source/</code>.</p></div><ul class="artifact-list">${archLinks}</ul></section><section class="section note"><strong>Como ler:</strong> a arquitetura representa componentes e responsabilidades; ela não substitui os relatórios nem publica os vídeos originais.</section>`;
  await writeText(path.join(docs, "architecture", "index.html"), page("Arquitetura", architecture, "../"));

  const rows = datasetItems.map((item) => `<tr><th scope="row">${esc(item.dataset)}</th><td>${number(item.videos)}</td><td>${number(item.annotations)}</td><td>${number(item.matched)}</td><td>${number(item.missing)}</td><td>${number(item.extra)}</td><td><span class="status ${statusClass(item.decision)}">${esc(item.decision)}</span></td></tr>`).join("") || '<tr><td colspan="7" class="empty">Nenhum dataset validado foi publicado.</td></tr>';
  const datasetCards = datasetItems.map((item) => datasetCard(item)).join("") || '<p class="empty">Sem dados para apresentar.</p>';
  const datasets = `<section class="page-intro"><p class="eyebrow">Inventário público</p><h1>O que o projeto possui</h1><p>Esta página resume datasets com evidência derivada no projeto. Quantidade não significa qualidade: a validação detalhada vem a seguir.</p></section><section class="section table-section"><div class="table-wrap"><table><thead><tr><th>Dataset</th><th>Vídeos</th><th>CSV</th><th>Correspondentes</th><th>Ausentes</th><th>Extras</th><th>Decisão</th></tr></thead><tbody>${rows}</tbody></table></div></section><section class="section dataset-grid">${datasetCards}</section>`;
  await writeText(path.join(docs, "datasets", "index.html"), page("Datasets", datasets, "../"));

  const validationCards = datasetItems.map((item) => `<article class="validation-card" id="${esc(item.dataset)}"><div class="card-top"><span class="tag">${esc(item.dataset)}</span><span class="status ${statusClass(item.decision)}">${esc(item.decision)}</span></div><h2>Reconciliação e qualidade</h2><div class="severity-grid">${severityGrid(item.severity)}</div><dl class="detail-list"><div><dt>Chave física</dt><dd>${esc(item.key_column || "não informada")}</dd></div><div><dt>Correspondentes</dt><dd>${number(item.matched)}</dd></div><div><dt>Ausentes</dt><dd>${number(item.missing)}</dd></div><div><dt>Extras</dt><dd>${number(item.extra)}</dd></div><div><dt>Manifest</dt><dd>${number(item.manifest_rows)}</dd></div><div><dt>FPS</dt><dd>${esc(item.fps || "não investigado")}</dd></div></dl><p class="muted">Evidência gerada em ${date(item.generated_at)}.</p></article>`).join("") || '<p class="empty">Nenhum resultado de validação foi publicado.</p>';
  const validation = `<section class="page-intro"><p class="eyebrow">Evidência antes da exploração</p><h1>Validação dos metadados</h1><p>A Etapa 1 verifica identidade dos arquivos, correspondência com o CSV e metadados técnicos. EDA, balanceamento e treinamento permanecem fora deste showroom.</p></section><section class="section latest-banner"><div><p class="section-kicker">Última execução</p><h2>${esc(current)}</h2><p>${date(latest.executed_at)} · decisão <strong>${esc(latest.decision ?? "—")}</strong></p></div><div class="severity-grid">${severityGrid(quality)}</div></section><section class="section validation-grid">${validationCards}</section><section class="section note"><strong>FPS observado:</strong> ${esc(technical.dataset_fps_interpretation ?? "sem conclusão registrada")}. Correspondências com contagem de frames: ${number(technical.fps_frame_count_matches)}; com taxa real: ${number(technical.fps_rate_matches)}.</section><section class="section"><a class="button button-primary" href="../reports/latest.html">Ler o resumo completo</a></section>`;
  await writeText(path.join(docs, "validation", "index.html"), page("Validação", validation, "../"));

  const executionDir = path.join(artifacts, "reports", "executions");
  const executionFiles = (await readdir(executionDir, { withFileTypes: true }).catch(() => [])).filter((entry) => entry.isFile() && entry.name.endsWith(".md")).map((entry) => entry.name).sort().reverse();
  const executionRows = (await Promise.all(executionFiles.map(async (name) => `<tr><th scope="row">${esc(path.parse(name).name)}</th><td>${number((await stat(path.join(executionDir, name))).size)} bytes</td><td>Resumo local registrado</td></tr>`))).join("") || '<tr><td colspan="3" class="empty">Nenhuma execução histórica publicada.</td></tr>';
  const executions = `<section class="page-intro"><p class="eyebrow">Rastro de reprodução</p><h1>Execuções registradas</h1><p>O notebook registra cada execução como resumo humano e mantém um atalho para o estado mais recente.</p></section><section class="section latest-banner"><div><p class="section-kicker">Mais recente</p><h2>${esc(current)}</h2><p>${date(latest.executed_at)} · ${esc(latest.decision ?? "sem decisão")}</p></div><a class="button button-primary" href="../reports/latest.html">Abrir relatório</a></section><section class="section table-section"><div class="table-wrap"><table><thead><tr><th>Execução</th><th>Tamanho</th><th>Proveniência</th></tr></thead><tbody>${executionRows}</tbody></table></div></section><section class="section note">Os vídeos e os arquivos originais não são copiados para o showroom.</section>`;
  await writeText(path.join(docs, "executions", "index.html"), page("Execuções", executions, "../"));
  await writeText(path.join(docs, "reports", "latest.html"), page("Relatório", reportPage(latest, reportText), "../"));
  await writeText(path.join(docs, "_config.yml"), "title: Libras Research Showroom\ndescription: Showroom público do projeto de dissertação sobre dados de Libras.\nmarkdown: kramdown\nplugins: []\n");
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
