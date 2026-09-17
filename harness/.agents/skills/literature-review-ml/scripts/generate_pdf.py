#!/usr/bin/env python3
"""Convert markdown to PDF via pandoc + xelatex."""

import argparse
import subprocess
import sys
from pathlib import Path


def check_deps():
    missing = []
    for tool in ["pandoc", "xelatex"]:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            print(f"OK  {tool}", file=sys.stderr)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"MISSING  {tool}", file=sys.stderr)
            missing.append(tool)
    if missing:
        print("\nInstall:", file=sys.stderr)
        print("  macOS:  brew install pandoc && brew install --cask mactex", file=sys.stderr)
        print("  Linux:  apt-get install pandoc texlive-xetex", file=sys.stderr)
        return False
    return True


def generate(md_path: Path, out_path: Path, citation_style: str, toc: bool, number: bool, template: Path):
    cmd = [
        "pandoc",
        str(md_path),
        "-o", str(out_path),
        "--pdf-engine=xelatex",
        "-V", "geometry:margin=1in",
        "-V", "fontsize=11pt",
        "-V", "colorlinks=true",
        "-V", "linkcolor=blue",
        "-V", "urlcolor=blue",
        "-V", "citecolor=teal",
        "-V", "mainfont=Times New Roman",
        "--highlight-style=tango",
    ]
    if toc:
        cmd += ["--toc", "--toc-depth=3"]
    if number:
        cmd.append("--number-sections")

    bib = md_path.with_suffix(".bib")
    if bib.exists():
        cmd += ["--citeproc", "--bibliography", str(bib)]
        csl = md_path.parent / f"{citation_style}.csl"
        if csl.exists():
            cmd += ["--csl", str(csl)]
    if template and template.exists():
        cmd += ["--template", str(template)]

    print("$ " + " ".join(cmd), file=sys.stderr)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr, file=sys.stderr)
        return False
    print(f"Wrote {out_path}", file=sys.stderr)
    return True


def main():
    ap = argparse.ArgumentParser(description="Markdown -> PDF via pandoc.")
    ap.add_argument("markdown", nargs="?")
    ap.add_argument("--output", "-o", default="")
    ap.add_argument("--citation-style", default="apa", choices=["apa", "nature", "ieee", "vancouver", "acm", "chicago"])
    ap.add_argument("--no-toc", dest="toc", action="store_false")
    ap.add_argument("--no-numbers", dest="number", action="store_false")
    ap.add_argument("--template", default="")
    ap.add_argument("--check-deps", action="store_true")
    args = ap.parse_args()

    if args.check_deps:
        sys.exit(0 if check_deps() else 1)

    if not args.markdown:
        ap.error("markdown file required (or pass --check-deps)")

    md = Path(args.markdown)
    if not md.exists():
        print(f"Not found: {md}", file=sys.stderr)
        sys.exit(1)

    out = Path(args.output) if args.output else md.with_suffix(".pdf")
    tpl = Path(args.template) if args.template else None
    ok = generate(md, out, args.citation_style, args.toc, args.number, tpl)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
