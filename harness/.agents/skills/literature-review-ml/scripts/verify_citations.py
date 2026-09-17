#!/usr/bin/env python3
"""Verify arXiv IDs and DOIs in a markdown document.

Extracts every arxiv ID and DOI, queries the relevant API, and reports:
- PASS: ID resolves and metadata is consistent with what the document claims
- WARN: ID resolves but document may misstate metadata
- FAIL: ID does not resolve (possible hallucination)
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query"
CROSSREF_API = "https://api.crossref.org/works"

ARXIV_PATTERN = re.compile(r"\barxiv[:/]\s*(\d{4}\.\d{4,5})(v\d+)?\b", re.IGNORECASE)
ARXIV_BARE = re.compile(r"\b(\d{4}\.\d{4,5})(v\d+)?\b")
DOI_PATTERN = re.compile(r"\b(10\.\d{4,9}/[^\s\]\)\}\"<>,;]+)", re.IGNORECASE)


def fetch_arxiv_meta(arxiv_id: str) -> dict:
    params = {"id_list": arxiv_id, "max_results": 1}
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            raw = r.read()
    except Exception as e:
        return {"_error": str(e)}

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    entry = root.find("atom:entry", ns)
    if entry is None:
        return {"_error": "no entry"}

    title_el = entry.find("atom:title", ns)
    title = re.sub(r"\s+", " ", title_el.text.strip()) if title_el is not None and title_el.text else ""
    if "Error" in title and "did not match" in title:
        return {"_error": "not found"}

    authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)]
    published = entry.findtext("atom:published", "", ns)
    year = published[:4] if published else ""
    return {"title": title, "authors": authors, "year": year}


def fetch_crossref_meta(doi: str) -> dict:
    url = f"{CROSSREF_API}/{urllib.parse.quote(doi, safe='')}"
    req = urllib.request.Request(url, headers={"User-Agent": "literature-review-ml/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"_error": "not found"}
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)}

    msg = data.get("message") or {}
    title = (msg.get("title") or [""])[0]
    authors = []
    for a in (msg.get("author") or []):
        family = a.get("family", "")
        given = a.get("given", "")
        if family:
            authors.append(f"{family}, {given}" if given else family)
    issued = (msg.get("issued") or {}).get("date-parts") or [[]]
    year = str(issued[0][0]) if issued and issued[0] else ""
    venue = (msg.get("container-title") or [""])[0]
    return {"title": title, "authors": authors, "year": year, "venue": venue}


def find_citations(text: str):
    """Yield (kind, id, line_no, context)."""
    lines = text.splitlines()

    seen = set()
    for ln_idx, line in enumerate(lines, 1):
        for m in ARXIV_PATTERN.finditer(line):
            aid = m.group(1)
            key = ("arxiv", aid)
            if key in seen:
                continue
            seen.add(key)
            yield "arxiv", aid, ln_idx, line.strip()
        for m in DOI_PATTERN.finditer(line):
            doi = m.group(1).rstrip(".,;)")
            key = ("doi", doi.lower())
            if key in seen:
                continue
            seen.add(key)
            yield "doi", doi, ln_idx, line.strip()


def consistency_check(claim_text: str, meta: dict) -> list:
    warnings = []
    ti = meta.get("title", "")
    if ti:
        title_words = re.findall(r"\w{4,}", ti.lower())
        if title_words:
            overlap = sum(1 for w in title_words if w in claim_text.lower())
            if overlap < min(3, len(title_words) // 2):
                warnings.append(f"title may not match: '{ti[:80]}'")

    year = meta.get("year", "")
    if year:
        years_in_context = re.findall(r"\b(19|20)\d{2}\b", claim_text)
        if years_in_context and year not in claim_text:
            warnings.append(f"year in context {years_in_context} differs from metadata {year}")

    authors = meta.get("authors") or []
    if authors:
        first_family = authors[0].split(",")[0].strip()
        if first_family and len(first_family) > 2 and first_family.lower() not in claim_text.lower():
            warnings.append(f"first author '{first_family}' not seen in context")

    return warnings


def main():
    ap = argparse.ArgumentParser(description="Verify arXiv IDs and DOIs in markdown.")
    ap.add_argument("file", help="Markdown file to verify.")
    ap.add_argument("--check-arxiv", action="store_true", default=True)
    ap.add_argument("--check-doi", action="store_true", default=True)
    ap.add_argument("--no-arxiv", dest="check_arxiv", action="store_false")
    ap.add_argument("--no-doi", dest="check_doi", action="store_false")
    ap.add_argument("--output", default="")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read()

    citations = list(find_citations(text))
    print(f"Found {len(citations)} unique citation IDs", file=sys.stderr)

    report = {"file": args.file, "total": 0, "pass": [], "warn": [], "fail": []}

    for kind, ident, line_no, context in citations:
        if kind == "arxiv" and not args.check_arxiv:
            continue
        if kind == "doi" and not args.check_doi:
            continue
        report["total"] += 1

        if kind == "arxiv":
            meta = fetch_arxiv_meta(ident)
            time.sleep(3.1)
        else:
            meta = fetch_crossref_meta(ident)
            time.sleep(0.3)

        entry = {"kind": kind, "id": ident, "line": line_no, "context": context, "meta": meta}

        if meta.get("_error"):
            report["fail"].append(entry)
            status = "FAIL"
        else:
            warnings = consistency_check(context, meta)
            entry["warnings"] = warnings
            if warnings:
                report["warn"].append(entry)
                status = "WARN"
            else:
                report["pass"].append(entry)
                status = "PASS"

        if not args.quiet:
            short_meta = meta.get("title", "")[:60] if not meta.get("_error") else meta.get("_error")
            print(f"[{status}] {kind}:{ident} (line {line_no}) — {short_meta}", file=sys.stderr)

    print("", file=sys.stderr)
    print(f"=== Citation Verification Summary ===", file=sys.stderr)
    print(f"Total:  {report['total']}", file=sys.stderr)
    print(f"PASS:   {len(report['pass'])}", file=sys.stderr)
    print(f"WARN:   {len(report['warn'])}", file=sys.stderr)
    print(f"FAIL:   {len(report['fail'])}", file=sys.stderr)

    if report["fail"]:
        print("\nFAIL citations (likely hallucinated or wrong ID):", file=sys.stderr)
        for e in report["fail"]:
            print(f"  - {e['kind']}:{e['id']} on line {e['line']}", file=sys.stderr)

    if report["warn"]:
        print("\nWARN citations (resolved but metadata may mismatch):", file=sys.stderr)
        for e in report["warn"]:
            print(f"  - {e['kind']}:{e['id']} on line {e['line']}", file=sys.stderr)
            for w in e["warnings"]:
                print(f"      {w}", file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport: {args.output}", file=sys.stderr)

    sys.exit(0 if not report["fail"] else 1)


if __name__ == "__main__":
    main()
