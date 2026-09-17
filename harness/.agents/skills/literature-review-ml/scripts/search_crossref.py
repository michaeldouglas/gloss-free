#!/usr/bin/env python3
"""Search CrossRef for journal articles. Free, no key (polite email recommended)."""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

CROSSREF_API = "https://api.crossref.org/works"


def fetch_page(query: str, rows: int, offset: int, year_start: int, year_end: int, mailto: str):
    filters = ["type:journal-article"]
    if year_start:
        filters.append(f"from-pub-date:{year_start}")
    if year_end:
        filters.append(f"until-pub-date:{year_end}")

    params = {
        "query": query,
        "rows": rows,
        "offset": offset,
        "filter": ",".join(filters),
        "sort": "is-referenced-by-count",
        "order": "desc",
    }
    if mailto:
        params["mailto"] = mailto

    url = f"{CROSSREF_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": f"literature-review-ml/1.0 ({mailto or 'noemail'})"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize(item: dict) -> dict:
    authors = []
    for a in (item.get("author") or []):
        given = a.get("given", "")
        family = a.get("family", "")
        if family:
            authors.append(f"{family}, {given}" if given else family)

    title = (item.get("title") or [""])[0]
    journal = (item.get("container-title") or [""])[0]

    issued = item.get("issued") or {}
    parts = (issued.get("date-parts") or [[]])[0]
    year = str(parts[0]) if parts and parts[0] else ""

    return {
        "source": "crossref",
        "doi": item.get("DOI", "") or "",
        "title": title,
        "authors": authors,
        "year": year,
        "venue": journal,
        "volume": item.get("volume", "") or "",
        "issue": item.get("issue", "") or "",
        "pages": item.get("page", "") or "",
        "publisher": item.get("publisher", "") or "",
        "citation_count": item.get("is-referenced-by-count", 0) or 0,
        "type": item.get("type", ""),
        "url": item.get("URL", "") or "",
        "abstract": item.get("abstract", "") or "",
    }


def main():
    ap = argparse.ArgumentParser(description="CrossRef search (journal articles).")
    ap.add_argument("query", help="Search query string.")
    ap.add_argument("--year-start", type=int, default=0)
    ap.add_argument("--year-end", type=int, default=0)
    ap.add_argument("--max-results", type=int, default=100)
    ap.add_argument("--mailto", default="", help="Email for polite pool.")
    ap.add_argument("--output", "-o", default="-")
    args = ap.parse_args()

    print(f"CrossRef query: {args.query}", file=sys.stderr)
    papers = []
    offset = 0
    rows = min(100, args.max_results)

    while len(papers) < args.max_results:
        page_rows = min(rows, args.max_results - len(papers))
        try:
            data = fetch_page(args.query, page_rows, offset, args.year_start, args.year_end, args.mailto)
        except Exception as e:
            print(f"Fetch error: {e}", file=sys.stderr)
            break

        items = (data.get("message") or {}).get("items") or []
        if not items:
            break

        for it in items:
            papers.append(normalize(it))

        if len(items) < page_rows:
            break
        offset += page_rows
        time.sleep(0.5)

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
