#!/usr/bin/env python3
"""Aggregate, deduplicate, rank, and format search results from multiple sources."""

import argparse
import json
import re
import sys
from datetime import datetime


def normalize_arxiv_id(aid: str) -> str:
    if not aid:
        return ""
    aid = aid.strip()
    aid = re.sub(r"^arxiv:", "", aid, flags=re.IGNORECASE)
    aid = re.sub(r"v\d+$", "", aid)
    return aid


def normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:", "", doi)
    return doi


def normalize_title(t: str) -> str:
    if not t:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", t.lower())).strip()


def load_papers(paths: list) -> list:
    papers = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            papers.extend(data)
        elif isinstance(data, dict) and "results" in data:
            papers.extend(data["results"])
        else:
            print(f"Warning: {p} is not a list; skipping", file=sys.stderr)
    return papers


def merge_records(a: dict, b: dict) -> dict:
    """Merge two records about the same paper, preferring richer metadata."""
    out = dict(a)
    for k, v in b.items():
        if k not in out or not out[k]:
            out[k] = v
        elif isinstance(out[k], list) and isinstance(v, list):
            seen = set(str(x).lower() for x in out[k])
            for x in v:
                if str(x).lower() not in seen:
                    out[k].append(x)
                    seen.add(str(x).lower())
        elif isinstance(out[k], (int, float)) and isinstance(v, (int, float)):
            out[k] = max(out[k], v)
    src_a = a.get("source", "")
    src_b = b.get("source", "")
    out["source"] = ", ".join(sorted({s for s in [src_a, src_b] if s}))
    return out


def deduplicate(papers: list) -> list:
    by_arxiv = {}
    by_doi = {}
    by_title = {}
    keep = []

    for p in papers:
        aid = normalize_arxiv_id(p.get("arxiv_id", ""))
        doi = normalize_doi(p.get("doi", ""))
        ti = normalize_title(p.get("title", ""))

        target_idx = None
        if aid and aid in by_arxiv:
            target_idx = by_arxiv[aid]
        elif doi and doi in by_doi:
            target_idx = by_doi[doi]
        elif ti and ti in by_title:
            target_idx = by_title[ti]

        if target_idx is not None:
            keep[target_idx] = merge_records(keep[target_idx], p)
            if aid and aid not in by_arxiv:
                by_arxiv[aid] = target_idx
            if doi and doi not in by_doi:
                by_doi[doi] = target_idx
            if ti and ti not in by_title:
                by_title[ti] = target_idx
        else:
            keep.append(p)
            idx = len(keep) - 1
            if aid:
                by_arxiv[aid] = idx
            if doi:
                by_doi[doi] = idx
            if ti:
                by_title[ti] = idx

    return keep


def rank(papers: list, criteria: str) -> list:
    key_map = {
        "citations": lambda p: p.get("citation_count", 0) or 0,
        "influential_citations": lambda p: p.get("influential_citations", 0) or 0,
        "year": lambda p: int(p.get("year") or 0),
    }
    key = key_map.get(criteria)
    if not key:
        return papers
    return sorted(papers, key=key, reverse=True)


def filter_year(papers: list, ys: int, ye: int) -> list:
    out = []
    for p in papers:
        try:
            y = int(p.get("year") or 0)
        except ValueError:
            y = 0
        if not y:
            out.append(p)
            continue
        if ys and y < ys:
            continue
        if ye and y > ye:
            continue
        out.append(p)
    return out


def filter_min_citations(papers: list, n: int) -> list:
    return [p for p in papers if (p.get("citation_count", 0) or 0) >= n]


def format_markdown(papers: list, header: str = "") -> str:
    lines = []
    if header:
        lines.append(header)
    lines.append(f"# Aggregated Literature Search\n")
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_  ")
    lines.append(f"_Total papers: {len(papers)}_\n")

    for i, p in enumerate(papers, 1):
        title = p.get("title", "(no title)")
        authors = ", ".join((p.get("authors") or [])[:6])
        if p.get("authors") and len(p["authors"]) > 6:
            authors += ", et al."
        year = p.get("year", "")
        venue = p.get("venue", "") or p.get("journal", "")
        cites = p.get("citation_count", 0) or 0
        inf = p.get("influential_citations", "")
        aid = p.get("arxiv_id", "")
        doi = p.get("doi", "")
        pdf = p.get("open_access_pdf", "") or p.get("pdf_url", "")
        source = p.get("source", "")

        lines.append(f"## {i}. {title}\n")
        lines.append(f"**Authors**: {authors}  ")
        lines.append(f"**Year**: {year} | **Venue**: {venue}  ")
        meta = f"**Citations**: {cites}"
        if inf != "" and inf is not None:
            meta += f" | **Influential**: {inf}"
        lines.append(meta + "  ")
        ids = []
        if aid:
            ids.append(f"[arXiv:{aid}](https://arxiv.org/abs/{aid})")
        if doi:
            ids.append(f"[doi:{doi}](https://doi.org/{doi})")
        if pdf:
            ids.append(f"[PDF]({pdf})")
        if ids:
            lines.append(" | ".join(ids) + "  ")
        lines.append(f"_source: {source}_\n")

        ab = p.get("abstract", "")
        if ab:
            ab = re.sub(r"\s+", " ", ab).strip()
            if len(ab) > 800:
                ab = ab[:800] + "…"
            lines.append(f"> {ab}\n")
        lines.append("**Decision**: [ ] include  [ ] exclude  [ ] maybe  \n")
        lines.append("**Reason**:\n\n---\n")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Aggregate search results from multiple sources.")
    ap.add_argument("inputs", nargs="+", help="JSON files from search scripts.")
    ap.add_argument("--deduplicate", action="store_true")
    ap.add_argument("--rank", choices=["citations", "influential_citations", "year"], default=None)
    ap.add_argument("--year-start", type=int, default=0)
    ap.add_argument("--year-end", type=int, default=0)
    ap.add_argument("--min-citations", type=int, default=0)
    ap.add_argument("--format", choices=["json", "markdown"], default="json")
    ap.add_argument("--output", "-o", default="-")
    args = ap.parse_args()

    papers = load_papers(args.inputs)
    print(f"Loaded {len(papers)} papers from {len(args.inputs)} files", file=sys.stderr)

    if args.deduplicate:
        before = len(papers)
        papers = deduplicate(papers)
        print(f"After dedup: {before} -> {len(papers)}", file=sys.stderr)

    if args.year_start or args.year_end:
        before = len(papers)
        papers = filter_year(papers, args.year_start, args.year_end)
        print(f"After year filter: {before} -> {len(papers)}", file=sys.stderr)

    if args.min_citations:
        before = len(papers)
        papers = filter_min_citations(papers, args.min_citations)
        print(f"After min-citations filter: {before} -> {len(papers)}", file=sys.stderr)

    if args.rank:
        papers = rank(papers, args.rank)
        print(f"Ranked by: {args.rank}", file=sys.stderr)

    if args.format == "json":
        out = json.dumps(papers, indent=2, ensure_ascii=False)
    else:
        out = format_markdown(papers)

    if args.output == "-":
        sys.stdout.write(out + ("\n" if not out.endswith("\n") else ""))
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
