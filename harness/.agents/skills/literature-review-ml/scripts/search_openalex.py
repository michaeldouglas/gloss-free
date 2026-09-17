#!/usr/bin/env python3
"""Search OpenAlex. Free, no key required; polite-pool email recommended."""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

OPENALEX_API = "https://api.openalex.org/works"


def fetch_page(query: str, per_page: int, cursor: str, year_start: int, year_end: int, mailto: str):
    filters = []
    if year_start:
        filters.append(f"from_publication_date:{year_start}-01-01")
    if year_end:
        filters.append(f"to_publication_date:{year_end}-12-31")
    filters.append("type:article|proceedings-article")

    params = {
        "search": query,
        "per-page": per_page,
        "cursor": cursor or "*",
        "filter": ",".join(filters),
    }
    if mailto:
        params["mailto"] = mailto

    url = f"{OPENALEX_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "literature-review-ml/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize(w: dict) -> dict:
    ids = w.get("ids") or {}
    doi = (ids.get("doi") or "").replace("https://doi.org/", "")

    arxiv_id = ""
    for loc in (w.get("locations") or []):
        landing = (loc.get("landing_page_url") or "")
        if "arxiv.org" in landing:
            m = landing.split("/abs/")[-1].split("v")[0]
            if m:
                arxiv_id = m
                break

    authors = []
    institutions = []
    for a in (w.get("authorships") or []):
        au = a.get("author") or {}
        if au.get("display_name"):
            authors.append(au["display_name"])
        for inst in (a.get("institutions") or []):
            if inst.get("display_name"):
                institutions.append(inst["display_name"])

    venue = ""
    primary = w.get("primary_location") or {}
    src = primary.get("source") or {}
    if src.get("display_name"):
        venue = src["display_name"]

    pdf_url = ""
    oa = w.get("open_access") or {}
    if oa.get("oa_url"):
        pdf_url = oa["oa_url"]

    return {
        "source": "openalex",
        "openalex_id": w.get("id", ""),
        "arxiv_id": arxiv_id,
        "doi": doi,
        "title": w.get("title", "") or "",
        "authors": authors,
        "institutions": list(dict.fromkeys(institutions)),
        "abstract": w.get("abstract", "") or "",
        "year": str(w.get("publication_year", "")) if w.get("publication_year") else "",
        "publication_date": w.get("publication_date", "") or "",
        "venue": venue,
        "type": w.get("type", ""),
        "citation_count": w.get("cited_by_count", 0) or 0,
        "open_access_pdf": pdf_url,
        "primary_topic": (w.get("primary_topic") or {}).get("display_name", ""),
    }


def main():
    ap = argparse.ArgumentParser(description="OpenAlex search.")
    ap.add_argument("query", help="Search query string.")
    ap.add_argument("--year-start", type=int, default=0)
    ap.add_argument("--year-end", type=int, default=0)
    ap.add_argument("--max-results", type=int, default=100)
    ap.add_argument("--mailto", default="", help="Email for polite pool (recommended).")
    ap.add_argument("--output", "-o", default="-")
    args = ap.parse_args()

    print(f"OpenAlex query: {args.query}", file=sys.stderr)
    papers = []
    cursor = "*"
    per_page = min(200, args.max_results)

    while len(papers) < args.max_results and cursor:
        try:
            data = fetch_page(args.query, per_page, cursor, args.year_start, args.year_end, args.mailto)
        except Exception as e:
            print(f"Fetch error: {e}", file=sys.stderr)
            break

        for w in (data.get("results") or []):
            papers.append(normalize(w))
            if len(papers) >= args.max_results:
                break

        meta = data.get("meta") or {}
        cursor = meta.get("next_cursor", "")
        time.sleep(0.2)

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
