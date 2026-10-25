#!/usr/bin/env python3
"""Build the public showroom from derived project artifacts only."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SEVERITIES = ("CRITICAL", "ERROR", "WARNING", "INFO")


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def number(value: Any) -> str:
    if value is None or value == "":
        return "—"
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return esc(value)


def date(value: Any) -> str:
    if not value:
        return "Ainda não registrado"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone().strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        return esc(value)


def status_class(value: Any) -> str:
    return {"GO": "good", "PASS": "good", "PARTIAL": "warn", "NO-GO": "bad", "FAIL": "bad"}.get(str(value), "neutral")


def page(title: str, body: str, prefix: str = "") -> str:
    return f"""<!doctype html>
<html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Aprendizagem profunda de representações visuais para tradução de Libras em português escrito sem uso de glosas.">
<title>{esc(title)} · Libras Research Showroom</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body>
<header class="topbar"><a class="brand" href="{prefix}index.html"><span class="brand-mark">∿</span>Pesquisa em tradução de Libras</a>
<nav aria-label="Navegação principal"><a href="{prefix}architecture/index.html">Arquitetura</a><a href="{prefix}datasets/index.html">Datasets</a><a href="{prefix}validation/index.html">Validação</a><a href="{prefix}executions/index.html">Execuções</a></nav></header>
<main>{body}</main><footer class="footer">Artefato derivado do projeto · dados brutos não publicados</footer>
</body></html>"""


def eyebrow(text: str) -> str:
    return f'<p class="eyebrow">{esc(text)}</p>'


def metric(label: str, value: Any) -> str:
    return f'<div class="metric"><strong>{number(value)}</strong><span>{esc(label)}</span></div>'


def summaries(metadata_root: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(metadata_root.glob("*/reports/metadata_summary.json")):
        item = load_json(path, {})
        if item.get("dataset"):
            found[item["dataset"]] = item
    legacy = load_json(metadata_root / "reports" / "metadata_summary.json", {})
    if legacy.get("dataset") and legacy["dataset"] not in found:
        found[legacy["dataset"]] = legacy
    return found


def view(dataset: str, summary: dict[str, Any], latest: dict[str, Any]) -> dict[str, Any]:
    counts = summary.get("counts", {})
    key = summary.get("key_reconciliation", {})
    severity = counts.get("by_severity", {})
    technical = latest.get("technical_summary", {}) if latest.get("dataset") == dataset else {}
    return {
        "dataset": dataset,
        "decision": summary.get("decision", latest.get("decision", "UNKNOWN")),
        "generated_at": summary.get("generated_at_utc"),
        "videos": counts.get("physical_videos", technical.get("videos_seen")),
        "annotations": counts.get("annotations", key.get("csv_records")),
        "manifest_rows": counts.get("manifest_rows"),
        "issues": counts.get("issues"),
        "severity": {name: severity.get(name, 0) for name in SEVERITIES},
        "matched": key.get("matched"), "missing": key.get("missing"), "extra": key.get("extra"),
        "key_column": key.get("filesystem_key_column"),
        "fps": technical.get("dataset_fps_interpretation"),
    }


def severity_grid(values: dict[str, Any]) -> str:
    return "".join(f'<div class="severity severity-{key.lower()}"><strong>{number(values.get(key, 0))}</strong><span>{key}</span></div>' for key in SEVERITIES)


def dataset_card(item: dict[str, Any], validation_href: str = "../validation/index.html") -> str:
    return f"""<article class="dataset-card"><div class="card-top"><span class="tag">dataset</span><span class="status {status_class(item['decision'])}">{esc(item['decision'])}</span></div>
<h3>{esc(item['dataset'])}</h3><p class="muted">Última evidência: {date(item['generated_at'])}</p>
<div class="mini-metrics"><span><strong>{number(item['videos'])}</strong> vídeos</span><span><strong>{number(item['annotations'])}</strong> registros</span><span><strong>{number(item['issues'])}</strong> issues</span></div>
<a class="text-link" href="{validation_href}#{esc(item['dataset'])}">Ver validação</a></article>"""


def dataset_dashboard_card(item: dict[str, Any]) -> str:
    severity = item.get("severity", {})
    findings = "".join(
        f'<span class="finding finding-{name.lower()}">{number(value)} {name}</span>'
        for name in SEVERITIES
        if (value := severity.get(name, 0))
    ) or '<span class="finding">Sem issues registradas</span>'

    if item.get("matched") is not None:
        finding_text = (
            f"{number(item['matched'])} chaves correspondem aos arquivos físicos; "
            f"{number(item['missing'])} ausentes e {number(item['extra'])} extras."
        )
    elif item.get("manifest_rows") is not None and item.get("annotations") is not None:
        delta = int(item["manifest_rows"]) - int(item["annotations"])
        if delta:
            finding_text = (
                f"O manifest tem {number(abs(delta))} linhas "
                f"{'a mais' if delta > 0 else 'a menos'} que annotations.csv; "
                "a reconciliação permanece pendente."
            )
        else:
            finding_text = "O relatório não registra a reconciliação detalhada da chave física."
    else:
        finding_text = "Veja o relatório de validação para o detalhe desta auditoria."

    return f"""<article class="dataset-audit {status_class(item['decision'])}">
  <div class="card-top"><div><p class="section-kicker">{esc(item['dataset'])}</p><h3>{'MINDS-Libras' if item['dataset'] == 'minds-libras-raw' else 'V-LIBRASIL' if item['dataset'] == 'v-librasil-raw' else esc(item['dataset'])}</h3></div><span class="status {status_class(item['decision'])}">{esc(item['decision'])}</span></div>
  <div class="audit-metrics"><div class="audit-metric"><strong>{number(item['videos'])}</strong><span>vídeos físicos</span></div><div class="audit-metric"><strong>{number(item['annotations'])}</strong><span>registros CSV</span></div><div class="audit-metric"><strong>{number(item['manifest_rows'])}</strong><span>linhas no manifest</span></div></div>
  <div class="audit-severity">{findings}</div>
  <p class="audit-finding">{finding_text}</p>
  <div class="audit-meta"><span>Relatório de {date(item['generated_at'])}</span><a href="validation/index.html#{esc(item['dataset'])}">Abrir auditoria →</a></div>
</article>"""


def report_page(latest: dict[str, Any], report_text: str) -> str:
    technical = latest.get("technical_summary", {})
    quality = latest.get("quality_counts", {})
    decision = latest.get("decision", "—")
    fps_hypothesis = technical.get("dataset_fps_interpretation", "sem conclusão")
    return f"""<section class="report-hero"><div><p class="eyebrow">Relatório derivado</p><h1>Execução em foco</h1><p>Uma leitura organizada da última validação registrada pelo notebook, com a decisão primeiro e os detalhes técnicos logo depois.</p></div><div class="report-decision {status_class(decision)}"><span>Decisão registrada</span><strong>{esc(decision)}</strong><small>{esc(latest.get('dataset', 'dataset não informado'))}<br>{date(latest.get('executed_at'))}</small></div></section>
<section class="report-kpis">{metric('vídeos vistos', technical.get('videos_seen'))}{metric('vídeos aprovados', technical.get('videos_ok'))}{metric('erros de probe', technical.get('videos_with_probe_error'))}{metric('issues INFO', quality.get('INFO', 0))}</section>
<section class="section report-layout"><article class="report-section"><p class="section-kicker">Resultado técnico</p><h2>O que foi conferido</h2><dl class="report-list"><div><dt>Dimensões</dt><dd>{number(technical.get('width_matches'))} largura · {number(technical.get('height_matches'))} altura</dd></div><div><dt>FPS</dt><dd>{esc(fps_hypothesis)}</dd></div><div><dt>Comparação por frames</dt><dd>{number(technical.get('fps_frame_count_matches'))} correspondências</dd></div><div><dt>Comparação por taxa</dt><dd>{number(technical.get('fps_rate_matches'))} correspondências</dd></div></dl></article><article class="report-section"><p class="section-kicker">Qualidade</p><h2>Severidades encontradas</h2><div class="severity-grid">{severity_grid(quality)}</div><p class="muted">As contagens vêm de <code>metadata_summary.json</code> e permanecem auditáveis nos artefatos técnicos.</p></article></section>
<section class="section report-section report-conclusion"><p class="section-kicker">Leitura principal</p><h2>O campo <code>fps</code> foi interpretado como {esc(fps_hypothesis)}.</h2><p>Essa conclusão é específica do dataset desta execução. Ela não deve ser transferida automaticamente para outros datasets.</p></section>
<details class="section raw-report"><summary>Ver o texto original do relatório</summary><pre>{esc(report_text)}</pre></details>"""


def build(repo_root: Path) -> dict[str, Any]:
    harness = repo_root / "harness"
    artifacts = harness / "artifacts"
    metadata = repo_root / "app" / "data" / "processed" / "metadata-validation"
    docs = repo_root / "docs"
    latest = load_json(artifacts / "reports" / "latest.json", {})
    dataset_items = [view(name, item, latest) for name, item in sorted(summaries(metadata).items())]

    architecture_source = artifacts / "architecture" / "html"
    architecture_files = sorted(path for path in architecture_source.glob("*.html") if path.is_file())
    public_architecture = docs / "architecture"
    public_architecture.mkdir(parents=True, exist_ok=True)
    for old in public_architecture.glob("*.html"):
        old.unlink()
    for source in architecture_files:
        shutil.copy2(source, public_architecture / source.name)

    latest_report = artifacts / "reports" / "latest.md"
    report_text = latest_report.read_text(encoding="utf-8") if latest_report.is_file() else "Relatório ainda não gerado."
    site_data = {"schema_version": "showroom.v1", "generated_at": datetime.now(timezone.utc).isoformat(), "latest": latest, "datasets": dataset_items, "architecture": [p.name for p in architecture_files], "scope": "Etapa 1 — validação dos metadados existentes"}
    write_text(docs / "data" / "showroom.json", json.dumps(site_data, ensure_ascii=False, indent=2))

    current = latest.get("dataset") or (dataset_items[0]["dataset"] if dataset_items else "nenhum dataset")
    technical = latest.get("technical_summary", {})
    quality = latest.get("quality_counts", {})
    total_videos = sum(int(item["videos"] or 0) for item in dataset_items)
    total_manifest_rows = sum(int(item["manifest_rows"] or 0) for item in dataset_items)
    go_count = sum(item["decision"] == "GO" for item in dataset_items)
    no_go_count = sum(item["decision"] == "NO-GO" for item in dataset_items)
    severity_totals = {
        name: sum(int(item.get("severity", {}).get(name, 0) or 0) for item in dataset_items)
        for name in SEVERITIES
    }
    audit_cards = "".join(dataset_dashboard_card(item) for item in dataset_items) or '<p class="empty">Ainda não há relatórios de validação para exibir.</p>'
    cards = "".join(dataset_card(item, "validation/index.html") for item in dataset_items) or '<p class="empty">Nenhum resumo de dataset foi publicado ainda.</p>'

    decision_summary = f"{go_count} GO · {no_go_count} NO-GO"
    research_title = "Aprendizagem profunda de representações visuais para tradução de Libras em português escrito sem uso de glosas"
    research_summary = (
        "A pesquisa investiga como traduzir vídeos de Libras diretamente para português escrito, "
        "sem uma etapa intermediária de glosas. A proposta combina frames RGB e pontos-chave "
        "de mãos, corpo e face para aprender relações visuais e temporais."
    )
    home = f"""<section class="project-hero">
  <div class="project-copy"><p class="eyebrow">Projeto de dissertação · Libras → português escrito</p><h1>{esc(research_title)}</h1><p class="hero-lede">{research_summary}</p><div class="hero-actions"><a class="button button-primary" href="architecture/index.html">Explorar a arquitetura</a><a class="button button-quiet" href="datasets/index.html">Ver os datasets</a></div></div>
  <div class="research-path" aria-label="Fluxo de pesquisa proposto"><p class="path-heading">Tradução direta, sem glosas</p><div class="path-step"><span class="path-icon">◉</span><div><strong>Vídeo em Libras</strong><small>frames RGB e pontos-chave</small></div></div><span class="path-connector"></span><div class="path-step"><span class="path-icon path-icon-middle">⌁</span><div><strong>Representação visual</strong><small>espaço, movimento e contexto</small></div></div><span class="path-connector"></span><div class="path-step"><span class="path-icon path-icon-end">Aa</span><div><strong>Português escrito</strong><small>tradução gloss-free</small></div></div></div>
</section>
<section class="research-context"><div><p class="section-kicker">Por que esta pesquisa?</p><p>A produção manual de glosas exige tempo e limita a escala. A tradução direta pode reduzir essa dependência e apoiar tecnologias de acessibilidade para a comunidade surda.</p></div><div class="context-meta"><span>Design Science Research</span><span>BLEU · ROUGE</span></div></section>
<section class="dashboard section"><div class="section-heading"><div><p class="section-kicker">Retrato dos dados</p><h2>O que já temos</h2></div><a class="text-link" href="datasets/index.html">Detalhes dos datasets</a></div><div class="dashboard-metrics">{metric('datasets catalogados', len(dataset_items))}{metric('vídeos físicos registrados', total_videos)}{metric('linhas nos manifests', total_manifest_rows)}<div class="metric decision-metric"><strong>{go_count} GO <span>·</span> {no_go_count} NO-GO</strong><span>decisões dos relatórios disponíveis</span></div></div><div class="dashboard-note"><strong>{sum(severity_totals.values())} ocorrências</strong> registradas nos relatórios. As auditorias foram geradas em datas diferentes; cada cartão informa a data da própria evidência.</div></section>
<section class="section"><div class="section-heading"><div><p class="section-kicker">Auditorias disponíveis</p><h2>Um dataset por vez</h2></div><a class="text-link" href="validation/index.html">Abrir resultados completos</a></div><div class="audit-grid">{audit_cards}</div></section>
<section class="section"><div class="section-heading"><div><p class="section-kicker">O que estamos fazendo</p><h2>Da base de dados à avaliação</h2></div></div><div class="progress-rail"><article class="progress-item completed"><span class="progress-state">Concluído</span><h3>Aquisição e organização</h3><p>Downloads reproduzíveis e inventários para V-LIBRASIL e MINDS-Libras.</p></article><article class="progress-item active"><span class="progress-state">Etapa atual</span><h3>Validação dos metadados</h3><p>MINDS-Libras passou. A auditoria de V-LIBRASIL ainda tem inconsistências a revisar.</p></article><article class="progress-item planned"><span class="progress-state">Planejado</span><h3>Modelos e comparação</h3><p>Explorar representações multimodais e avaliar traduções com BLEU e ROUGE.</p></article></div></section>
<section class="section research-plan"><div><p class="section-kicker">Abordagem investigada</p><h2>Combinar o que o vídeo mostra e como o sinal se move.</h2><p>O plano considera Transformers espaço-temporais e pré-treinamento visual-linguagem para relacionar sinais visuais ao texto. Essa fase ainda não foi iniciada.</p></div><div class="method-list"><div><strong>Entradas</strong><span>RGB · mãos · corpo · face</span></div><div><strong>Aprendizado</strong><span>relações espaciais e temporais</span></div><div><strong>Avaliação</strong><span>BLEU · ROUGE · comparação entre estratégias</span></div></div></section>
<section class="section next-section"><div class="section-heading"><div><p class="section-kicker">Explore o projeto</p><h2>Entre pelos resultados ou pelo sistema.</h2></div></div><div class="next-grid"><a href="architecture/index.html"><strong>Arquitetura</strong><span>Como o pipeline de aquisição e validação se conecta.</span></a><a href="validation/index.html"><strong>Validação</strong><span>Chaves, vídeos, metadados técnicos e questões em aberto.</span></a><a href="executions/index.html"><strong>Execuções</strong><span>Relatórios e histórico das rodadas registradas.</span></a></div></section>"""
    write_text(docs / "index.html", page("Início", home))

    arch_links = "".join(f'<li><a href="{esc(p.name)}">{esc(p.stem.replace("-", " "))}</a><span>HTML Archify</span></li>' for p in architecture_files) or '<li class="empty">A arquitetura ainda não foi publicada.</li>'
    architecture = f"""<section class="page-intro"><p class="eyebrow">Mapa do sistema</p><h1>Arquitetura do pipeline</h1><p>O diagrama Archify mostra o caminho principal entre pesquisador, CLI, aquisição, processamento audiovisual, validações e artefatos derivados.</p></section><section class="section feature-panel"><div><p class="section-kicker">Diagrama interativo</p><h2>Escolha uma visão</h2><p>Os arquivos são gerados a partir dos candidatos versionados em <code>harness/artifacts/architecture/source/</code>.</p></div><ul class="artifact-list">{arch_links}</ul></section><section class="section note"><strong>Como ler:</strong> a arquitetura representa componentes e responsabilidades; ela não substitui os relatórios nem publica os vídeos originais.</section>"""
    write_text(docs / "architecture" / "index.html", page("Arquitetura", architecture, "../"))

    rows = "".join(f'<tr><th scope="row">{esc(i["dataset"])}</th><td>{number(i["videos"])}</td><td>{number(i["annotations"])}</td><td>{number(i["matched"])}</td><td>{number(i["missing"])}</td><td>{number(i["extra"])}</td><td><span class="status {status_class(i["decision"])}">{esc(i["decision"])}</span></td></tr>' for i in dataset_items) or '<tr><td colspan="7" class="empty">Nenhum dataset validado foi publicado.</td></tr>'
    dataset_cards = "".join(dataset_card(item) for item in dataset_items) or '<p class="empty">Sem dados para apresentar.</p>'
    datasets = f"""<section class="page-intro"><p class="eyebrow">Inventário público</p><h1>O que o projeto possui</h1><p>Esta página resume datasets com evidência derivada no projeto. Quantidade não significa qualidade: a validação detalhada vem a seguir.</p></section><section class="section table-section"><div class="table-wrap"><table><thead><tr><th>Dataset</th><th>Vídeos</th><th>CSV</th><th>Correspondentes</th><th>Ausentes</th><th>Extras</th><th>Decisão</th></tr></thead><tbody>{rows}</tbody></table></div></section><section class="section dataset-grid">{dataset_cards}</section>"""
    write_text(docs / "datasets" / "index.html", page("Datasets", datasets, "../"))

    validation_cards = "".join(f'<article class="validation-card" id="{esc(i["dataset"])}"><div class="card-top"><span class="tag">{esc(i["dataset"])}</span><span class="status {status_class(i["decision"])}">{esc(i["decision"])}</span></div><h2>Reconciliação e qualidade</h2><div class="severity-grid">{severity_grid(i["severity"])}</div><dl class="detail-list"><div><dt>Chave física</dt><dd>{esc(i["key_column"] or "não informada")}</dd></div><div><dt>Correspondentes</dt><dd>{number(i["matched"])}</dd></div><div><dt>Ausentes</dt><dd>{number(i["missing"])}</dd></div><div><dt>Extras</dt><dd>{number(i["extra"])}</dd></div><div><dt>Manifest</dt><dd>{number(i["manifest_rows"])}</dd></div><div><dt>FPS</dt><dd>{esc(i["fps"] or "não investigado")}</dd></div></dl><p class="muted">Evidência gerada em {date(i["generated_at"])}.</p></article>' for i in dataset_items) or '<p class="empty">Nenhum resultado de validação foi publicado.</p>'
    validation = f"""<section class="page-intro"><p class="eyebrow">Evidência antes da exploração</p><h1>Validação dos metadados</h1><p>A Etapa 1 verifica identidade dos arquivos, correspondência com o CSV e metadados técnicos. EDA, balanceamento e treinamento permanecem fora deste showroom.</p></section><section class="section latest-banner"><div><p class="section-kicker">Última execução</p><h2>{esc(current)}</h2><p>{date(latest.get('executed_at'))} · decisão <strong>{esc(latest.get('decision', '—'))}</strong></p></div><div class="severity-grid">{severity_grid(quality)}</div></section><section class="section validation-grid">{validation_cards}</section><section class="section note"><strong>FPS observado:</strong> {esc(technical.get('dataset_fps_interpretation', 'sem conclusão registrada'))}. Correspondências com contagem de frames: {number(technical.get('fps_frame_count_matches'))}; com taxa real: {number(technical.get('fps_rate_matches'))}.</section><section class="section"><a class="button button-primary" href="../reports/latest.html">Ler o resumo completo</a></section>"""
    write_text(docs / "validation" / "index.html", page("Validação", validation, "../"))

    execution_dir = artifacts / "reports" / "executions"
    execution_rows = "".join(f'<tr><th scope="row">{esc(p.stem)}</th><td>{number(p.stat().st_size)} bytes</td><td>Resumo local registrado</td></tr>' for p in sorted(execution_dir.glob("*.md"), reverse=True)) or '<tr><td colspan="3" class="empty">Nenhuma execução histórica publicada.</td></tr>'
    executions = f"""<section class="page-intro"><p class="eyebrow">Rastro de reprodução</p><h1>Execuções registradas</h1><p>O notebook registra cada execução como resumo humano e mantém um atalho para o estado mais recente.</p></section><section class="section latest-banner"><div><p class="section-kicker">Mais recente</p><h2>{esc(current)}</h2><p>{date(latest.get('executed_at'))} · {esc(latest.get('decision', 'sem decisão'))}</p></div><a class="button button-primary" href="../reports/latest.html">Abrir relatório</a></section><section class="section table-section"><div class="table-wrap"><table><thead><tr><th>Execução</th><th>Tamanho</th><th>Proveniência</th></tr></thead><tbody>{execution_rows}</tbody></table></div></section><section class="section note">Os vídeos e os arquivos originais não são copiados para o showroom.</section>"""
    write_text(docs / "executions" / "index.html", page("Execuções", executions, "../"))

    report = report_page(latest, report_text)
    write_text(docs / "reports" / "latest.html", page("Relatório", report, "../"))

    write_text(docs / "_config.yml", "title: Libras Research Showroom\ndescription: Showroom público do projeto de dissertação sobre dados de Libras.\nmarkdown: kramdown\nplugins: []\n")
    write_text(docs / "assets" / "style.css", CSS)
    return {"docs_root": str(docs), "datasets": len(dataset_items), "architecture_files": len(architecture_files)}


CSS = """@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
:root{--ink:#12252d;--soft:#49616a;--paper:#f4f6f3;--surface:#fff;--line:#d8e0dc;--mint:#9ee6d1;--green:#0b8573;--orange:#e87548;--yellow:#f3cb78;--red:#d55d52;--shadow:0 18px 45px #12252d17}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:1rem/1.55 'DM Sans',system-ui,sans-serif}a{color:inherit;text-decoration:none}a:focus-visible{outline:3px solid var(--orange);outline-offset:4px}.topbar{max-width:1180px;margin:auto;padding:24px 28px;display:flex;justify-content:space-between;align-items:center;gap:24px}.brand{font-weight:700;letter-spacing:-.03em;display:flex;align-items:center;gap:10px}.brand-mark{display:grid;place-items:center;width:30px;height:30px;background:var(--ink);color:var(--mint);border-radius:50%;font-size:22px}.topbar nav{display:flex;gap:22px;color:var(--soft);font-size:14px}.topbar nav a:hover,.text-link{color:var(--green)}main{max-width:1180px;margin:auto;padding:32px 28px 72px}.hero{min-height:480px;display:grid;grid-template-columns:1.45fr .65fr;gap:70px;align-items:center;padding:68px 0 52px;border-bottom:1px solid var(--line)}.eyebrow,.section-kicker,.panel-label{font:12px 'Space Mono',monospace;color:var(--green);margin:0 0 18px}.hero h1,.page-intro h1{font-size:clamp(42px,6vw,78px);line-height:.98;letter-spacing:-.07em;max-width:750px;margin:0 0 28px}.hero-lede{font-size:20px;color:var(--soft);max-width:660px;margin:0 0 30px}.hero-actions{display:flex;flex-wrap:wrap;gap:12px}.button{display:inline-flex;padding:12px 18px;border:1px solid var(--ink);font-weight:600;font-size:14px}.button-primary{background:var(--ink);color:var(--paper)}.button-primary:hover{background:var(--green);border-color:var(--green)}.button-quiet{border-color:var(--line);color:var(--soft);background:var(--surface)}.signal-panel{min-height:300px;background:var(--ink);color:var(--paper);padding:28px;display:flex;flex-direction:column;justify-content:flex-end;position:relative;overflow:hidden;box-shadow:var(--shadow)}.signal-panel:before{content:'';position:absolute;inset:0;background:linear-gradient(145deg,transparent 35%,#9ee6d126 36%,transparent 37%),linear-gradient(35deg,transparent 58%,#e8754830 59%,transparent 60%)}.signal-panel>*{position:relative}.signal-panel strong{font-size:54px;line-height:1;letter-spacing:-.07em}.signal-panel span:not(.signal-line){color:var(--mint);font-size:18px;margin-top:8px}.signal-panel small{color:#afc0c0;margin-top:28px}.signal-line{position:absolute;height:1px;background:var(--mint);left:28px;right:28px;transform:rotate(-18deg)}.signal-line:nth-child(1){top:74px}.signal-line:nth-child(2){top:126px;background:var(--orange)}.metrics-row{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);margin:34px 0 96px;border:1px solid var(--line)}.metric{background:var(--paper);padding:22px 20px;min-height:112px}.metric strong{display:block;font-size:30px;letter-spacing:-.06em;line-height:1.1;margin-bottom:8px;word-break:break-word}.metric span{color:var(--soft);font-size:13px}.section{margin-top:88px}.section h2{font-size:clamp(28px,4vw,48px);letter-spacing:-.06em;line-height:1.05;margin:0 0 14px}.section p{color:var(--soft);max-width:680px}.split-section{display:grid;grid-template-columns:1fr 1fr;gap:70px;align-items:end}.callout{border-left:4px solid var(--orange);padding:18px 0 18px 24px}.callout p{font-size:22px;line-height:1.3;color:var(--ink);margin:0}.callout-mark{font-size:34px;color:var(--orange)}.section-heading{display:flex;justify-content:space-between;align-items:end;margin-bottom:24px}.text-link{font-weight:700;border-bottom:1px solid currentColor;padding-bottom:2px}.dataset-grid,.validation-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}.dataset-card,.validation-card,.feature-panel,.latest-banner{background:var(--surface);border:1px solid var(--line);padding:24px;box-shadow:0 10px 28px #12252d0a}.card-top{display:flex;justify-content:space-between;gap:12px;align-items:center}.tag{font:11px 'Space Mono',monospace;color:var(--green)}.status{font:11px 'Space Mono',monospace;border:1px solid currentColor;padding:4px 7px}.status.good{color:var(--green)}.status.warn{color:#a56b0b}.status.bad{color:var(--red)}.status.neutral{color:var(--soft)}.dataset-card h3{font-size:22px;margin:32px 0 4px;letter-spacing:-.04em}.muted{color:var(--soft);font-size:13px}.mini-metrics{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0;color:var(--soft);font-size:13px}.mini-metrics strong{color:var(--ink);font-size:19px}.next-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}.next-grid a{background:var(--surface);padding:24px;display:flex;flex-direction:column;gap:10px;min-height:180px}.next-grid a:hover{background:var(--mint)}.next-grid .number{font:13px 'Space Mono',monospace;color:var(--orange)}.next-grid strong{font-size:22px}.next-grid span:last-child{color:var(--soft);font-size:14px}.page-intro{padding:76px 0 40px;border-bottom:1px solid var(--line)}.page-intro h1{font-size:clamp(42px,6vw,70px);max-width:820px}.page-intro p:not(.eyebrow){font-size:19px;color:var(--soft);max-width:690px}.feature-panel,.latest-banner{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:center}.artifact-list{list-style:none;padding:0;margin:0}.artifact-list li{display:flex;justify-content:space-between;padding:15px 0;border-bottom:1px solid var(--line)}.artifact-list a{color:var(--green);font-weight:700}.artifact-list span{color:var(--soft);font-size:13px}.note{border-top:1px solid var(--line);padding-top:20px;color:var(--soft)}code,pre{font-family:'Space Mono',monospace;font-size:.86em}.table-wrap{overflow-x:auto;background:var(--surface);border:1px solid var(--line)}table{border-collapse:collapse;width:100%;min-width:680px;text-align:left}th,td{padding:15px 17px;border-bottom:1px solid var(--line);font-size:14px}th{font-size:12px;color:var(--soft);font-weight:500}tbody th{color:var(--ink);font-weight:700}.severity-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.severity{padding:12px 10px;border-top:3px solid var(--line);background:var(--paper)}.severity strong{display:block;font-size:25px;line-height:1}.severity span{font:10px 'Space Mono',monospace;color:var(--soft)}.severity-critical{border-color:var(--red)}.severity-error{border-color:var(--orange)}.severity-warning{border-color:var(--yellow)}.severity-info{border-color:var(--green)}.detail-list{display:grid;grid-template-columns:1fr 1fr;gap:0 18px;margin:26px 0}.detail-list div{padding:11px 0;border-bottom:1px solid var(--line)}.detail-list dt{font:11px 'Space Mono',monospace;color:var(--soft)}.detail-list dd{margin:3px 0;font-weight:700}.report-block{background:var(--ink);padding:24px;overflow:auto}.report-block pre{color:var(--mint);white-space:pre-wrap;line-height:1.7;margin:0}.empty{color:var(--soft);padding:20px}.footer{max-width:1180px;margin:auto;padding:24px 28px 40px;color:var(--soft);font-size:12px;border-top:1px solid var(--line)}
@media(max-width:800px){.topbar{align-items:flex-start;flex-direction:column}.topbar nav{flex-wrap:wrap;gap:12px 18px}.hero,.split-section,.feature-panel,.latest-banner{grid-template-columns:1fr;gap:34px}.hero{padding-top:36px}.metrics-row{grid-template-columns:repeat(2,1fr);margin-bottom:62px}.next-grid{grid-template-columns:1fr}.section{margin-top:62px}.severity-grid{grid-template-columns:repeat(2,1fr)}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

CSS += """.report-hero{display:grid;grid-template-columns:1fr 300px;gap:54px;align-items:end;padding:70px 0 52px;border-bottom:1px solid var(--line)}.report-hero h1{font-size:clamp(42px,6vw,70px);line-height:.98;letter-spacing:-.07em;margin:0 0 20px}.report-hero p:not(.eyebrow){font-size:19px;color:var(--soft);max-width:660px}.report-decision{min-height:220px;padding:25px;background:var(--surface);border:1px solid currentColor;display:flex;flex-direction:column;justify-content:flex-end}.report-decision span{font:11px 'Space Mono',monospace;color:var(--soft)}.report-decision strong{font-size:64px;line-height:1;letter-spacing:-.08em;margin:12px 0}.report-decision small{color:var(--soft);font-size:13px}.report-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin:34px 0 0}.report-kpis .metric{background:var(--paper)}.report-layout{display:grid;grid-template-columns:1fr 1fr;gap:18px}.report-section{background:var(--surface);border:1px solid var(--line);padding:28px}.report-section h2{font-size:30px;margin-bottom:24px}.report-list{margin:0}.report-list div{display:flex;justify-content:space-between;gap:20px;padding:14px 0;border-bottom:1px solid var(--line)}.report-list dt{font:11px 'Space Mono',monospace;color:var(--soft)}.report-list dd{margin:0;text-align:right;font-weight:700}.report-conclusion{border-left:4px solid var(--orange)}.report-conclusion h2{max-width:760px}.raw-report{border:1px solid var(--line);background:var(--surface);padding:20px 24px}.raw-report summary{cursor:pointer;font-weight:700;color:var(--green)}.raw-report pre{margin:24px 0 0;background:var(--ink);color:var(--mint);padding:24px;white-space:pre-wrap;line-height:1.7;overflow:auto}@media(max-width:800px){.report-hero,.report-layout{grid-template-columns:1fr;gap:28px}.report-kpis{grid-template-columns:repeat(2,1fr)}.report-decision{min-height:180px}.report-list div{display:block}.report-list dd{text-align:left;margin-top:5px}}"""

CSS += """.project-hero{position:relative;display:grid;grid-template-columns:minmax(0,1.25fr) minmax(290px,.75fr);gap:clamp(36px,7vw,92px);align-items:center;padding:58px 0 68px;border-bottom:1px solid var(--line)}.project-copy h1{font-size:clamp(42px,5.4vw,70px);line-height:1.02;letter-spacing:-.065em;max-width:800px;margin:0 0 22px}.hero-lede{font-size:19px;line-height:1.6;color:var(--soft);max-width:690px;margin:0 0 28px}.research-path{position:relative;padding:25px 26px 21px;background:var(--ink);color:var(--paper);border-radius:4px;box-shadow:var(--shadow);overflow:hidden}.research-path:after{content:'';position:absolute;width:220px;height:220px;border:1px solid #9ee6d138;border-radius:50%;right:-112px;top:-116px;box-shadow:0 0 0 22px #9ee6d10c,0 0 0 46px #9ee6d108;pointer-events:none}.path-heading{position:relative;z-index:1;margin:0 0 20px;color:var(--mint);font:11px 'Space Mono',monospace;letter-spacing:.03em;text-transform:uppercase}.path-step{position:relative;z-index:1;display:flex;align-items:center;gap:14px;min-height:54px}.path-icon{display:grid;place-items:center;flex:0 0 36px;height:36px;border:1px solid #9ee6d164;border-radius:50%;color:var(--mint);font:16px 'Space Mono',monospace}.path-icon-middle{color:#ffd09a;border-color:#e8754877}.path-icon-end{border-radius:6px;color:var(--paper);border-color:#ffffff59;font-weight:700}.path-step strong,.path-step small{display:block}.path-step strong{font-size:14px}.path-step small{font-size:12px;color:#b7c8c5;margin-top:2px}.path-connector{display:block;width:1px;height:18px;margin:2px 0 2px 17px;background:linear-gradient(var(--mint),#e87548)}.research-context{display:grid;grid-template-columns:1fr auto;align-items:center;gap:30px;padding:25px 28px;margin-top:28px;background:#e7efea;border-left:3px solid var(--green)}.research-context .section-kicker{margin-bottom:5px}.research-context p:not(.section-kicker){max-width:780px;margin:0;color:var(--ink);font-size:15px}.context-meta{display:flex;flex-direction:column;gap:7px;text-align:right;color:var(--green);font:10px 'Space Mono',monospace;white-space:nowrap}.dashboard.section{margin-top:72px}.dashboard-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line)}.dashboard-metrics .metric{background:var(--surface);min-height:120px}.dashboard-metrics .metric strong{font-size:clamp(25px,3vw,38px)}.dashboard-metrics .decision-metric strong{font-size:24px}.decision-metric strong span{font:inherit;color:var(--orange)}.dashboard-note{padding:13px 16px;background:#edf1ec;color:var(--soft);font-size:12px}.dashboard-note strong{color:var(--ink)}.audit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.dataset-audit{position:relative;padding:23px 24px 20px;background:var(--surface);border:1px solid var(--line);box-shadow:0 10px 28px #12252d0a}.dataset-audit:before{content:'';position:absolute;left:-1px;top:-1px;bottom:-1px;width:3px;background:var(--green)}.dataset-audit.bad:before{background:var(--red)}.dataset-audit .card-top{margin-bottom:18px}.dataset-audit h3{font-size:23px;letter-spacing:-.04em;margin:0}.audit-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:15px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.audit-metric strong,.audit-metric span{display:block}.audit-metric strong{font-size:21px;letter-spacing:-.04em}.audit-metric span{font:9px 'Space Mono',monospace;color:var(--soft);text-transform:uppercase}.audit-severity{display:flex;flex-wrap:wrap;gap:7px;margin-top:14px}.audit-severity span{padding:4px 7px;background:var(--paper);font:10px 'Space Mono',monospace;color:var(--soft)}.audit-finding{font-size:13px;color:var(--soft);margin:16px 0 10px}.audit-meta{display:flex;justify-content:space-between;align-items:center;gap:10px;padding-top:12px;border-top:1px solid var(--line);font-size:11px;color:var(--soft)}.audit-meta a{font-weight:700;color:var(--green)}.progress-rail{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.progress-item{position:relative;padding:24px 24px 27px 0}.progress-item+.progress-item{padding-left:24px;border-left:1px solid var(--line)}.progress-state{display:inline-flex;margin-bottom:17px;color:var(--green);font:10px 'Space Mono',monospace;text-transform:uppercase}.progress-item.active .progress-state{color:#ad651e}.progress-item.planned .progress-state{color:var(--soft)}.progress-item h3{font-size:19px;line-height:1.2;letter-spacing:-.03em;margin:0 0 10px}.progress-item p{font-size:13px;margin:0;line-height:1.6}.research-plan{display:grid;grid-template-columns:1.1fr .9fr;align-items:center;gap:60px;padding:34px;background:#e7efea}.research-plan h2{max-width:640px}.research-plan p:not(.section-kicker){max-width:680px}.method-list{border-top:1px solid #cbd8d1}.method-list div{display:grid;grid-template-columns:100px 1fr;gap:18px;padding:13px 0;border-bottom:1px solid #cbd8d1;font-size:13px}.method-list strong{color:var(--green)}.method-list span{color:var(--soft)}.next-section .next-grid a{min-height:145px}@media(max-width:800px){.project-hero{grid-template-columns:1fr;gap:34px;padding:38px 0 44px}.project-copy h1{font-size:clamp(39px,10vw,58px)}.research-context{grid-template-columns:1fr;gap:14px;padding:20px}.context-meta{flex-direction:row;flex-wrap:wrap;text-align:left}.dashboard-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.audit-grid{grid-template-columns:1fr}.progress-rail{grid-template-columns:1fr}.progress-item,.progress-item+.progress-item{padding:20px 0;border-left:0;border-bottom:1px solid var(--line)}.progress-item:last-child{border-bottom:0}.research-plan{grid-template-columns:1fr;gap:22px;padding:24px}.section-heading{align-items:flex-start;gap:18px}.section-heading .text-link{font-size:12px;white-space:nowrap}}@media(max-width:430px){.dashboard-metrics{grid-template-columns:1fr 1fr}.dashboard-metrics .metric{padding:17px 14px;min-height:104px}.dashboard-metrics .metric strong{font-size:26px}.dashboard-metrics .decision-metric strong{font-size:19px}.audit-metrics{gap:4px}.audit-metric strong{font-size:18px}.method-list div{grid-template-columns:82px 1fr;gap:10px}}"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()
    repo_root = (args.repo_root or Path(__file__).resolve().parents[1]).resolve()
    print(json.dumps(build(repo_root), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
