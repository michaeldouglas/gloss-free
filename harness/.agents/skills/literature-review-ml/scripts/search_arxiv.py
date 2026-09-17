#!/usr/bin/env python3
"""Search arXiv via its public Atom API. No API key required."""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

ARXIV_API = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def build_query(terms: str, categories: list, year_start: int, year_end: int) -> str:
    parts = []
    if terms:
        terms = terms.replace(" AND ", " AND ").replace(" OR ", " OR ")
        if " AND " in terms or " OR " in terms:
            parts.append(f"(all:{terms})")
        else:
            parts.append(f"all:{terms}")
    if categories:
        cat_q = " OR ".join(f"cat:{c.strip()}" for c in categories)
        parts.append(f"({cat_q})")
    return " AND ".join(parts)


def fetch_batch(query: str, start: int, batch: int) -> bytes:
    params = {
        "search_query": query,
        "start": start,
        "max_results": batch,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()


def parse_entry(entry) -> dict:
    arxiv_id_full = entry.findtext("atom:id", "", NS)
    arxiv_id = arxiv_id_full.rsplit("/", 1)[-1] if arxiv_id_full else ""
    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)
    version_match = re.search(r"v(\d+)$", arxiv_id_full)
    version = version_match.group(1) if version_match else ""

    title = re.sub(r"\s+", " ", entry.findtext("atom:title", "", NS).strip())
    summary = re.sub(r"\s+", " ", entry.findtext("atom:summary", "", NS).strip())
    published = entry.findtext("atom:published", "", NS)
    updated = entry.findtext("atom:updated", "", NS)
    year = published[:4] if published else ""

    authors = [a.findtext("atom:name", "", NS) for a in entry.findall("atom:author", NS)]
    cats = [c.attrib.get("term", "") for c in entry.findall("atom:category", NS)]
    primary_cat = entry.find("arxiv:primary_category", NS)
    primary = primary_cat.attrib.get("term", "") if primary_cat is not None else ""

    pdf_url = ""
    abs_url = ""
    for link in entry.findall("atom:link", NS):
        if link.attrib.get("title") == "pdf":
            pdf_url = link.attrib.get("href", "")
        elif link.attrib.get("rel") == "alternate":
            abs_url = link.attrib.get("href", "")

    doi = entry.findtext("arxiv:doi", "", NS)
    journal_ref = entry.findtext("arxiv:journal_ref", "", NS)
    comment = entry.findtext("arxiv:comment", "", NS)

    return {
        "source": "arxiv",
        "arxiv_id": arxiv_id,
        "arxiv_version": version,
        "title": title,
        "authors": authors,
        "abstract": summary,
        "year": year,
        "published": published,
        "updated": updated,
        "categories": cats,
        "primary_category": primary,
        "doi": doi,
        "journal_ref": journal_ref,
        "comment": comment,
        "abs_url": abs_url,
        "pdf_url": pdf_url,
    }


def filter_by_year(papers: list, year_start: int, year_end: int) -> list:
    out = []
    for p in papers:
        try:
            y = int(p.get("year", "0"))
        except ValueError:
            continue
        if year_start and y < year_start:
            continue
        if year_end and y > year_end:
            continue
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description="arXiv search.")
    ap.add_argument("query", help="Search terms (use 'A OR B' or 'A AND B').")
    ap.add_argument("--categories", default="", help="Comma-separated arXiv categories (cs.LG,stat.ML,...).")
    ap.add_argument("--year-start", type=int, default=0)
    ap.add_argument("--year-end", type=int, default=0)
    ap.add_argument("--max-results", type=int, default=100)
    ap.add_argument("--batch-size", type=int, default=100, help="API batch size (max 2000 per arXiv docs).")
    ap.add_argument("--output", "-o", default="-")
    args = ap.parse_args()

    cats = [c for c in args.categories.split(",") if c.strip()] if args.categories else []
    q = build_query(args.query, cats, args.year_start, args.year_end)

    print(f"Query: {q}", file=sys.stderr)
    print(f"Fetching up to {args.max_results} results from arXiv...", file=sys.stderr)

    papers = []
    start = 0
    while len(papers) < args.max_results:
        batch = min(args.batch_size, args.max_results - len(papers))
        try:
            raw = fetch_batch(q, start, batch)
        except Exception as e:
            print(f"Fetch failed at start={start}: {e}", file=sys.stderr)
            break

        root = ET.fromstring(raw)
        entries = root.findall("atom:entry", NS)
        if not entries:
            break

        for e in entries:
            papers.append(parse_entry(e))

        if len(entries) < batch:
            break
        start += batch
        time.sleep(3.0)  # arXiv asks for ≥3s between requests

    if args.year_start or args.year_end:
        before = len(papers)
        papers = filter_by_year(papers, args.year_start, args.year_end)
        print(f"Year filter: {before} -> {len(papers)}", file=sys.stderr)

    print(f"Total: {len(papers)} papers", file=sys.stderr)

    out = json.dumps(papers, indent=2, ensure_ascii=False)
    if args.output == "-":
        print(out)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
