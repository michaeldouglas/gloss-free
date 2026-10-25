import path from "node:path";
import { mkdir, readFile, writeFile, rm, copyFile } from "node:fs/promises";
import { createHarnessPaths } from "../lib/paths.ts";

type JsonObject = Record<string, any>;
const defaultPaths = createHarnessPaths(path.resolve(import.meta.dir, "../.."));

function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

async function readJson(file: string): Promise<JsonObject> {
  const value: unknown = JSON.parse(await readFile(file, "utf8"));
  if (!isObject(value)) throw new Error(`${file} precisa conter um objeto JSON.`);
  return value;
}

function escapeHtml(value: unknown): string {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function slideEntry(id: string, title: string): string {
  return `---\ntheme: default\ntitle: ${JSON.stringify(title)}\nauthor: Pesquisa em tradução de Libras\naspectRatio: 16/9\ncolorSchema: light\nfonts:\n  sans: Atkinson Hyperlegible\n  serif: Crimson Pro\n  mono: Fira Code\n  provider: none\ntransition: fade\nselectable: true\ntwoslash: false\nrouterMode: hash\nhtmlAttrs:\n  lang: pt-BR\nsrc: ./decks/${id}/slides.md\n---\n`;
}

function parseArgs(argv: string[]): { repoRoot: string; siteBase: string; preview: boolean; releaseId?: string } {
  let repoRoot = defaultPaths.repositoryRoot;
  let siteBase = "/docs/";
  let preview = false;
  let releaseId: string | undefined;
  for (let index = 2; index < argv.length; index += 1) {
    if (argv[index] === "--") continue;
    if (argv[index] === "--repo-root") repoRoot = path.resolve(argv[++index] ?? repoRoot);
    else if (argv[index] === "--site-base") siteBase = argv[++index] ?? siteBase;
    else if (argv[index] === "--preview") preview = true;
    else if (argv[index] === "--id") releaseId = argv[++index];
    else if (argv[index] === "--help" || argv[index] === "-h") {
      process.stdout.write("Usage: bun run core/scripts/build-presentations.ts [--repo-root <project-root>] [--site-base /docs/] [--preview [--id <release-id>]]\n");
      process.exit(0);
    } else throw new Error(`Opção desconhecida: ${argv[index]}`);
  }
  if (!siteBase.startsWith("/") || !siteBase.endsWith("/")) throw new Error("--site-base precisa começar e terminar com '/'.");
  if (releaseId && !preview) throw new Error("--id só pode ser usado junto com --preview.");
  if (releaseId && !/^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$/.test(releaseId)) throw new Error(`Identificador de release inválido: ${releaseId}`);
  return { repoRoot, siteBase, preview, releaseId };
}

async function runSlidev(args: string[], cwd: string): Promise<void> {
  const proc = Bun.spawn([process.execPath, "run", "slidev", ...args], {
    cwd,
    stdin: "inherit",
    stdout: "inherit",
    stderr: "inherit",
  });
  const exitCode = await proc.exited;
  if (exitCode !== 0) throw new Error(`Slidev falhou com código ${exitCode}: ${args.join(" ")}`);
}

function catalogHtml(latest: JsonObject, releases: JsonObject[]): string {
  const previous = releases.filter((release) => release.id !== latest.id);
  const archive = previous.map((release) => `
    <li class="release-card">
      <div class="release-copy">
        <time datetime="${escapeHtml(release.release_date)}">${escapeHtml(new Intl.DateTimeFormat("pt-BR", { dateStyle: "long", timeZone: "UTC" }).format(new Date(`${release.release_date}T12:00:00Z`)))}</time>
        <h3>${escapeHtml(release.title)}</h3>
        <p>${escapeHtml(release.summary)}</p>
      </div>
      <div class="release-actions">
        <a href="${escapeHtml(release.id)}/presentation.pdf" download aria-label="Baixar PDF da versão ${escapeHtml(release.release_date)}">PDF</a>
        <a href="${escapeHtml(release.id)}/index.html" aria-label="Abrir apresentação HTML da versão ${escapeHtml(release.release_date)}">HTML</a>
      </div>
    </li>`).join("");
  return `<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Apresentações datadas sobre o progresso e as evidências da pesquisa em tradução de Libras.">
  <title>Apresentações da pesquisa · Libras</title>
  <link rel="stylesheet" href="../assets/style.css">
  <style>
    :root { color-scheme: light; --navy:#12304a; --blue:#2563eb; --teal:#0f8f8a; --purple:#6b5bb8; --ink:#183248; --muted:#526a7d; --paper:#f7f9fc; --line:#d8e2ec; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--paper); color:var(--ink); font:1rem/1.6 system-ui,-apple-system,"Segoe UI",sans-serif; }
    a { color:#174db8; text-underline-offset:.18em; }
    a:focus-visible { outline:3px solid var(--purple); outline-offset:3px; border-radius:.2rem; }
    .skip { position:absolute; left:-9999px; top:auto; }
    .skip:focus { left:1rem; top:1rem; z-index:10; background:white; padding:.75rem 1rem; }
    main { width:min(72rem,calc(100% - 2.5rem)); margin:clamp(2rem,7vw,6rem) auto; }
    .eyebrow { color:var(--teal); font-size:.85rem; font-weight:750; letter-spacing:.12em; text-transform:uppercase; }
    h1,h2,h3 { color:var(--navy); font-family:Georgia,"Times New Roman",serif; line-height:1.12; }
    h1 { max-width:15ch; margin:.35rem 0 1rem; font-size:clamp(2.5rem,6vw,4.7rem); }
    .intro { max-width:56rem; color:var(--muted); font-size:1.15rem; }
    .current { margin:2.5rem 0 4rem; padding:clamp(1.5rem,4vw,3rem); border:1px solid var(--line); border-top:5px solid var(--teal); border-radius:1.25rem; background:white; box-shadow:0 1rem 3rem rgba(18,48,74,.08); }
    .current h2 { margin:.25rem 0 .5rem; font-size:clamp(1.6rem,3vw,2.4rem); }
    .current p { max-width:52rem; color:var(--muted); }
    .primary { display:inline-flex; min-height:3rem; align-items:center; justify-content:center; gap:.5rem; margin-top:.75rem; padding:.75rem 1.1rem; border-radius:.65rem; background:var(--navy); color:white; font-weight:750; text-decoration:none; }
    .primary:hover { background:#1d4667; }
    .secondary { margin-left:1rem; font-weight:650; }
    .history-heading { display:flex; align-items:end; justify-content:space-between; gap:1rem; margin-bottom:1rem; }
    .history-heading h2 { margin:0; font-size:2rem; }
    .history-heading p { margin:0; color:var(--muted); }
    .release-list { display:grid; gap:1rem; margin:0; padding:0; list-style:none; }
    .release-card { display:flex; justify-content:space-between; gap:2rem; align-items:center; padding:1.35rem 1.5rem; border:1px solid var(--line); border-radius:.9rem; background:#fff; }
    .release-copy time { color:var(--purple); font-size:.9rem; font-weight:750; }
    .release-copy h3 { margin:.2rem 0; font-size:1.4rem; }
    .release-copy p { margin:0; color:var(--muted); }
    .release-actions { display:flex; flex-wrap:wrap; gap:.75rem; flex:0 0 auto; }
    .release-actions a { min-width:3.3rem; min-height:2.75rem; display:inline-flex; align-items:center; justify-content:center; padding:.5rem .75rem; border:1px solid var(--line); border-radius:.55rem; font-weight:700; text-decoration:none; }
    .release-actions a:hover { border-color:var(--teal); background:#eef9f8; }
    .footer-note { margin-top:2.5rem; padding-top:1rem; border-top:1px solid var(--line); color:var(--muted); font-size:.9rem; }
    @media (max-width:700px) { .release-card,.history-heading { align-items:flex-start; flex-direction:column; } .release-actions { width:100%; } .secondary { display:block; margin:1rem 0 0; } }
    @media (prefers-reduced-motion:reduce) { *,*::before,*::after { scroll-behavior:auto !important; transition:none !important; animation:none !important; } }
  </style>
</head>
<body>
  <a class="skip" href="#conteudo">Pular para o conteúdo</a>
  <main id="conteudo">
    <p class="eyebrow">Pesquisa em tradução de Libras</p>
    <h1>Progresso da pesquisa</h1>
    <p class="intro">Versões datadas para compartilhar o que foi realizado, quais evidências estão disponíveis e quais questões seguem abertas. Cada apresentação identifica a data dos dados usados.</p>
    <section class="current" aria-labelledby="current-title">
      <p class="eyebrow">Apresentação mais recente · ${escapeHtml(latest.release_date)}</p>
      <h2 id="current-title">${escapeHtml(latest.title)}</h2>
      <p>${escapeHtml(latest.summary)}</p>
      <a class="primary" href="${escapeHtml(latest.id)}/index.html">Abrir a apresentação mais recente</a>
      <a class="secondary" href="latest.pdf" download>Baixar PDF</a>
    </section>
    <section aria-labelledby="history-title">
      <div class="history-heading"><h2 id="history-title">Versões anteriores</h2><p>Selecione pela data do checkpoint.</p></div>
      <ol class="release-list">${archive || '<li class="release-card"><p>Esta é a primeira versão arquivada. Novos checkpoints aparecerão aqui.</p></li>'}</ol>
    </section>
    <p class="footer-note">As apresentações são sínteses derivadas. Consulte os relatórios e a seção de validação para detalhes metodológicos e evidências completas.</p>
  </main>
</body>
</html>`;
}

async function build(): Promise<void> {
  const { repoRoot, siteBase, preview, releaseId } = parseArgs(process.argv);
  const projectPaths = createHarnessPaths(path.join(repoRoot, "harness"));
  const presentationsRoot = path.join(projectPaths.harnessRoot, "presentations");
  const decksRoot = path.join(presentationsRoot, "decks");
  const publicRoot = path.join(projectPaths.docsRoot, "apresentacoes");
  const publicationRoot = path.join(projectPaths.reportsRoot, "publications");
  const publicationIndex = await readJson(path.join(publicationRoot, "index.json"));
  if (publicationIndex.schema_version !== "research-presentation-index.v1" || !Array.isArray(publicationIndex.releases) || publicationIndex.releases.length === 0) {
    throw new Error("O catálogo de versões de apresentações está ausente ou inválido.");
  }

  const releases = [...publicationIndex.releases].sort((a: JsonObject, b: JsonObject) => b.release_date.localeCompare(a.release_date) || b.id.localeCompare(a.id));
  if (publicationIndex.latest_release !== releases[0].id) throw new Error("latest_release precisa apontar para a versão mais recente do catálogo.");

  if (preview) {
    const entry = releaseId ? releases.find((item: JsonObject) => item.id === releaseId) : releases[0];
    if (!entry) throw new Error(`Release não encontrado no catálogo: ${releaseId}`);
    const releaseDir = path.join(decksRoot, entry.id);
    const release = await readJson(path.join(releaseDir, "release.json"));
    if (release.schema_version !== "presentation-release.v1" || release.id !== entry.id || release.title !== entry.title) throw new Error(`Manifesto inválido para ${entry.id}.`);
    const snapshotPath = path.resolve(projectPaths.repositoryRoot, release.snapshot_path);
    if (path.dirname(snapshotPath) !== path.resolve(publicationRoot) || entry.snapshot !== path.basename(snapshotPath)) throw new Error(`Snapshot inválido para ${entry.id}.`);
    const snapshot = await readJson(snapshotPath);
    if (snapshot.schema_version !== "research-presentation-evidence.v1" || snapshot.release_id !== entry.id) throw new Error(`Snapshot incompatível com ${entry.id}.`);
    const entryFile = path.join(presentationsRoot, `.entry-${entry.id}.md`);
    const evidenceFile = path.join(presentationsRoot, "evidence.generated.json");
    try {
      await writeFile(evidenceFile, `${JSON.stringify(snapshot, null, 2)}\n`, "utf8");
      await writeFile(entryFile, slideEntry(entry.id, entry.title), "utf8");
      await runSlidev([path.basename(entryFile), "--open"], presentationsRoot);
    } finally {
      await rm(entryFile, { force: true });
      await rm(evidenceFile, { force: true });
    }
    return;
  }

  await mkdir(publicRoot, { recursive: true });
  const built: Array<{ id: string; output: string }> = [];

  for (const entry of releases) {
    if (!/^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$/.test(entry.id)) throw new Error(`Identificador de release inválido: ${entry.id}`);
    const releaseDir = path.join(decksRoot, entry.id);
    const release = await readJson(path.join(releaseDir, "release.json"));
    if (release.schema_version !== "presentation-release.v1" || release.id !== entry.id) throw new Error(`Manifesto inválido para ${entry.id}.`);
    if (release.title !== entry.title || release.release_date !== entry.release_date || release.summary !== entry.summary) throw new Error(`O manifesto e o índice divergem para ${entry.id}.`);
    const snapshotPath = path.resolve(projectPaths.repositoryRoot, release.snapshot_path);
    const snapshotRelative = path.relative(projectPaths.repositoryRoot, snapshotPath);
    if (snapshotRelative.startsWith(`..${path.sep}`) || path.isAbsolute(snapshotRelative)) throw new Error(`Snapshot fora do repositório: ${release.snapshot_path}`);
    if (entry.snapshot !== path.basename(snapshotPath) || path.dirname(snapshotPath) !== path.resolve(publicationRoot)) throw new Error(`O índice aponta para um snapshot diferente do manifesto de ${entry.id}.`);
    const snapshot = await readJson(snapshotPath);
    if (snapshot.schema_version !== "research-presentation-evidence.v1" || snapshot.release_id !== entry.id) throw new Error(`Snapshot incompatível com ${entry.id}.`);
    const slideFile = path.join(releaseDir, "slides.md");
    if (!(await Bun.file(slideFile).exists())) throw new Error(`Falta ${slideFile}.`);

    const outputDir = path.join(publicRoot, entry.id);
    const entryFile = path.join(presentationsRoot, `.entry-${entry.id}.md`);
    const generatedEvidenceFile = path.join(presentationsRoot, "evidence.generated.json");
    const relativeEntry = path.basename(entryFile);
    try {
      await writeFile(generatedEvidenceFile, `${JSON.stringify(snapshot, null, 2)}\n`, "utf8");
      await writeFile(entryFile, slideEntry(entry.id, entry.title), "utf8");
      await rm(outputDir, { recursive: true, force: true });
      await mkdir(outputDir, { recursive: true });
      const slideBase = `${siteBase}apresentacoes/${entry.id}/`;
      const exportBase = path.join(outputDir, "presentation");
      const browserPath = process.env.SLIDEV_CHROMIUM_PATH ? ["--executable-path", process.env.SLIDEV_CHROMIUM_PATH] : [];
      await runSlidev(["build", relativeEntry, "--out", outputDir, "--base", slideBase, "--without-notes"], presentationsRoot);
      await runSlidev(["export", relativeEntry, "--format", "pdf", "--output", exportBase, "--with-clicks", "false", "--with-toc", ...browserPath], presentationsRoot);
      for (const required of ["index.html", "presentation.pdf"]) {
        if (!(await Bun.file(path.join(outputDir, required)).exists())) throw new Error(`A exportação ${entry.id} não produziu ${required}.`);
      }
      built.push({ id: entry.id, output: outputDir });
    } finally {
      await rm(entryFile, { force: true });
      await rm(generatedEvidenceFile, { force: true });
      await rm(path.join(releaseDir, "evidence.generated.json"), { force: true });
    }
  }

  const latest = releases[0];
  const latestOutput = path.join(publicRoot, latest.id, "presentation.pdf");
  await copyFile(latestOutput, path.join(publicRoot, "latest.pdf"));
  await writeFile(path.join(publicRoot, "index.html"), catalogHtml(latest, releases), "utf8");
  const buildSummary = { catalog: path.join(publicRoot, "index.html"), latest_html: path.join(publicRoot, latest.id, "index.html"), latest_pdf: path.join(publicRoot, "latest.pdf"), releases: built.map(({ id }) => id) };
  process.stdout.write(`${JSON.stringify(buildSummary)}\n`);
}

if (import.meta.main) {
  build().catch((error) => {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
  });
}
