#!/usr/bin/env python3
"""Search Semantic Scholar Graph API. Free, no key required (rate-limited)."""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_FIELDS = (
    "paperId,externalIds,title,abstract,authors,year,venue,publicationVenue,"
    "publicationTypes,citationCount,influentialCitationCount,openAccessPdf,"
    "publicationDate,journal,fieldsOfStudy"
)


def fetch_page(query: str, offset: int, limit: int, year_start: int, year_end: int, min_citations: int):
    params = {
        "query": query,
        "offset": offset,
        "limit": limit,
        "fields": S2_FIELDS,
    }
    if year_start or year_end:
        ys = year_start or 1900
        ye = year_end or 2100
        params["year"] = f"{ys}-{ye}"
    if min_citations:
        params["minCitationCount"] = min_citations

    url = f"{S2_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "literature-review-ml/1.0"})

    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** attempt
                print(f"Rate limited; sleeping {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("Semantic Scholar rate limit exceeded")


def normalize(p: dict) -> dict:
    ext = p.get("externalIds") or {}
    authors = [a.get("name", "") for a in (p.get("authors") or [])]
    venue = p.get("venue") or ((p.get("publicationVenue") or {}).get("name", ""))
    open_pdf = (p.get("openAccessPdf") or {}).get("url", "")

    return {
        "source": "semantic_scholar",
        "s2_id": p.get("paperId", ""),
        "arxiv_id": ext.get("ArXiv", ""),
        "doi": ext.get("DOI", ""),
        "pubmed_id": ext.get("PubMed", ""),
        "title": p.get("title", "") or "",
        "authors": authors,
        "abstract": p.get("abstract", "") or "",
        "year": str(p.get("year", "")) if p.get("year") else "",
        "publication_date": p.get("publicationDate", "") or "",
        "venue": venue,
        "publication_types": p.get("publicationTypes") or [],
        "fields_of_study": p.get("fieldsOfStudy") or [],
        "citation_count": p.get("citationCount", 0) or 0,
        "influential_citations": p.get("influentialCitationCount", 0) or 0,
        "open_access_pdf": open_pdf,
        "url": f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}" if p.get("paperId") else "",
    }


def main():
    ap = argparse.ArgumentParser(description="Semantic Scholar search.")
    ap.add_argument("query", help="Search query string.")
    ap.add_argument("--year-start", type=int, default=0)
    ap.add_argument("--year-end", type=int, default=0)
    ap.add_argument("--min-citations", type=int, default=0)
    ap.add_argument("--max-results", type=int, default=100)
    ap.add_argument("--output", "-o", default="-")
    args = ap.parse_args()

    print(f"S2 query: {args.query}", file=sys.stderr)
    papers = []
    offset = 0
    limit = min(100, args.max_results)

    while len(papers) < args.max_results:
        page_limit = min(limit, args.max_results - len(papers))
        try:
            data = fetch_page(args.query, offset, page_limit, args.year_start, args.year_end, args.min_citations)
        except Exception as e:
            print(f"Fetch error at offset={offset}: {e}", file=sys.stderr)
            break

        batch = data.get("data") or []
        if not batch:
            break

        for p in batch:
            papers.append(normalize(p))

        total = data.get("total", 0)
        if offset + page_limit >= total:
            break
        offset += page_limit
        time.sleep(1.1)

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
