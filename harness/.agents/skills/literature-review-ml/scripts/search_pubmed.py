#!/usr/bin/env python3
"""Search PubMed via NCBI E-utilities. Free, no key required (rate-limited to 3 req/s).

Note: PubMed does not expose citation counts. Use Semantic Scholar to enrich
citation data after retrieval (match by DOI or PMID via S2 externalIds).
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
BATCH_SIZE = 100


def esearch(query: str, max_results: int, year_start: int, year_end: int) -> list:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }
    if year_start or year_end:
        params["datetype"] = "pdat"
        if year_start:
            params["mindate"] = f"{year_start}/01/01"
        if year_end:
            params["maxdate"] = f"{year_end}/12/31"

    url = f"{ESEARCH_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "literature-review-ml/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("esearchresult", {}).get("idlist", [])


def efetch_batch(pmids: list) -> str:
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    }
    url = f"{EFETCH_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "literature-review-ml/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def _text(el, path, default=""):
    node = el.find(path)
    return (node.text or default) if node is not None else default


def parse_xml(xml_data: str) -> list:
    root = ET.fromstring(xml_data)
    papers = []
    for article in root.findall(".//PubmedArticle"):
        mc = article.find("MedlineCitation")
        if mc is None:
            continue
        pmid = _text(mc, "PMID")
        art = mc.find("Article")
        if art is None:
            continue

        title = _text(art, "ArticleTitle")

        abstract_parts = []
        for at in art.findall(".//AbstractText"):
            label = at.get("Label", "")
            text = at.text or ""
            abstract_parts.append(f"{label}: {text}" if label else text)
        abstract = " ".join(abstract_parts).strip()

        authors = []
        for au in art.findall(".//Author"):
            cn = au.find("CollectiveName")
            if cn is not None and cn.text:
                authors.append(cn.text)
                continue
            last = _text(au, "LastName")
            fore = _text(au, "ForeName")
            initials = _text(au, "Initials")
            name = f"{last}, {fore}" if fore else (f"{last}, {initials}" if initials else last)
            if name.strip():
                authors.append(name.strip())

        journal = _text(art, "Journal/Title")
        year = _text(art, "Journal/JournalIssue/PubDate/Year")
        if not year:
            medline_date = _text(art, "Journal/JournalIssue/PubDate/MedlineDate")
            year = medline_date[:4] if medline_date else ""

        doi = ""
        arxiv_id = ""
        pd = article.find("PubmedData")
        if pd is not None:
            for aid in pd.findall(".//ArticleId"):
                id_type = aid.get("IdType", "")
                val = aid.text or ""
                if id_type == "doi":
                    doi = val
                elif id_type == "arxiv":
                    arxiv_id = val

        papers.append({
            "source": "pubmed",
            "pmid": pmid,
            "arxiv_id": arxiv_id,
            "doi": doi,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "year": year,
            "venue": journal,
            "citation_count": 0,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return papers


def main():
    ap = argparse.ArgumentParser(description="PubMed search via NCBI E-utilities.")
    ap.add_argument("query", help="Search query (supports PubMed field tags, e.g. 'lasso[Title] AND statistics[MeSH]').")
    ap.add_argument("--year-start", type=int, default=0)
    ap.add_argument("--year-end", type=int, default=0)
    ap.add_argument("--max-results", type=int, default=100)
    ap.add_argument("--output", "-o", default="-")
    args = ap.parse_args()

    print(f"PubMed query: {args.query}", file=sys.stderr)
    pmids = esearch(args.query, args.max_results, args.year_start, args.year_end)
    print(f"Found {len(pmids)} PMIDs", file=sys.stderr)

    papers = []
    for i in range(0, len(pmids), BATCH_SIZE):
        batch = pmids[i:i + BATCH_SIZE]
        try:
            papers.extend(parse_xml(efetch_batch(batch)))
        except Exception as e:
            print(f"Fetch error for batch {i}–{i + len(batch)}: {e}", file=sys.stderr)
        if i + BATCH_SIZE < len(pmids):
            time.sleep(0.35)

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
