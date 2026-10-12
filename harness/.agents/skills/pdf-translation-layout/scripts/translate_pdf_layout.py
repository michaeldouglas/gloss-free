"""Translate PDFs in place while preserving page geometry and visual assets.

This helper is intentionally conservative: unsupported math/CJK/image blocks
remain from the source PDF instead of being rendered as question marks.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import pymupdf


def clean_source(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00ad", "-").replace("\u2011", "-").replace("\u00a0", " ")
    text = re.sub(r"(?<=[A-Za-zÀ-ÿ])-\s+(?=[a-zà-ÿ])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{2,}", "\n", text).strip()


def clean_translation(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00ad", "-").replace("\u2011", "-").replace("\u00a0", " ").replace("\u200b", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"^(\d+(?:\.\d+)*)(?=[A-Za-zÀ-ÿ])", r"\1 ", text)
    text = re.sub(r"(?<=[A-Za-zÀ-ÿ])et al\.", " et al.", text)
    text = re.sub(r"(?<=[a-záàâãéêíóôõúç])(?=(?:Transformer|Encoder|LLaVA))", " ", text)
    text = re.sub(r"(linguagem|language)\.LLaVA", r"\1. LLaVA", text)
    text = text.replace("En-coder", "Encoder")
    text = re.sub(r"\bBritish SignLanguage\b", "British Sign Language", text)
    return text.strip()


def translate(text: str) -> str:
    source = clean_source(text)
    if not source or not re.search(r"[A-Za-z]{3}", source):
        return source
    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=pt&dt=t&q=" + quote(source, safe="")
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result = "".join(part[0] for part in (payload[0] or []) if part and part[0])
            if result:
                return clean_translation(result)
            raise RuntimeError("empty translation response")
        except Exception as exc:  # transient network/service failure
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(last_error)


def load_cache(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_cache(path: Path, cache: dict[str, str]) -> None:
    path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def get_blocks(page: pymupdf.Page) -> list[dict]:
    result = []
    for raw in page.get_text("dict", sort=True)["blocks"]:
        if raw.get("type") != 0:
            continue
        text = clean_source("".join(s.get("text", "") for line in raw.get("lines", []) for s in line.get("spans", [])))
        if not text:
            continue
        spans = [s for line in raw.get("lines", []) for s in line.get("spans", [])]
        result.append({
            "rect": pymupdf.Rect(raw["bbox"]),
            "text": text,
            "size": max((float(s.get("size", 9)) for s in spans), default=9),
            "bold": any(int(s.get("flags", 0)) & 16 for s in spans),
        })
    return result


def image_rects(page: pymupdf.Page) -> list[pymupdf.Rect]:
    return [rect for image in page.get_images(full=True) for rect in page.get_image_rects(image[0])]


def skip_block(block: dict, images: list[pymupdf.Rect]) -> bool:
    rect = block["rect"]
    text = block["text"]
    unusual = re.findall(r"[^A-Za-z0-9À-ÿ\s.,;:!?()\[\]{}%/+=\-_'\"’–—]", text)
    return (
        rect.width < 40
        or rect.height > rect.width * 3
        or any(rect.intersects(image) for image in images)
        or bool(re.search(r"[\u3400-\u9fff\ufffd]", text))
        or any(ord(char) < 32 and char not in "\n\t" for char in text)
        or len(unusual) >= 2
    )


def is_heading(text: str) -> bool:
    text = re.sub(r"\s+", " ", text).strip()
    return len(text) <= 120 and (
        re.match(r"^(?:[A-Z]{1,3}|[ivx]+)[.)]?\s+", text, re.I)
        or text.isupper()
        or text.lower().startswith(("abstract", "data processing"))
    )


def insertion_rect(page: pymupdf.Page, block: dict) -> pymupdf.Rect:
    rect = block["rect"]
    if not is_heading(block["text"]):
        return rect
    midpoint = page.rect.width / 2
    right = midpoint - 9 if rect.x0 < midpoint else page.rect.width - 54
    return pymupdf.Rect(rect.x0, rect.y0, max(rect.x1, right), min(page.rect.y1, rect.y1 + 5))


def insert_fitted(page: pymupdf.Page, rect: pymupdf.Rect, text: str, size: float, bold: bool) -> bool:
    font = "hebo" if bold else "helv"
    base = max(4.2, min(float(size), 12))
    for fontsize in [base, base * .9, base * .8, base * .7, base * .6, 4.2, 3.5, 3.0, 2.5]:
        result = page.insert_textbox(rect, text, fontsize=fontsize, fontname=font, color=(0, 0, 0), overlay=True)
        if result >= 0:
            return True
    return False


def correct_fragment(source: str, translated: str) -> str:
    source = clean_source(source)
    if source.startswith("ety of tasks"):
        translated = re.sub(r"^.*?(?=de tarefas)", "", translated, count=1)
    if "Additionally, YouTube-SL-25" in source and "al., 2023a) também coletaram" in translated:
        translated = translated.replace(
            "al., 2023a) também coletaram",
            "Além disso, o YouTube-SL-25 (Tanzer & Zhang, 2024) e o JWSign (Gueuwou et al., 2023a) também coletaram",
            1,
        )
    return clean_translation(translated)


def translate_document(source: Path, output: Path, cache: dict[str, str], cache_path: Path, workers: int) -> dict[str, int]:
    document = pymupdf.open(source)
    stats = {"translated": 0, "preserved": 0, "failed": 0}
    for page_number, page in enumerate(document):
        all_blocks = get_blocks(page)
        images = image_rects(page)
        eligible = [block for block in all_blocks if not skip_block(block, images)]
        missing = list(dict.fromkeys(block["text"] for block in eligible if block["text"] not in cache))
        if missing:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(translate, text): text for text in missing}
                for future in as_completed(futures):
                    cache[futures[future]] = future.result()
            save_cache(cache_path, cache)
        stats["preserved"] += len(all_blocks) - len(eligible)
        for block in eligible:
            page.add_redact_annot(block["rect"], fill=(1, 1, 1))
        if eligible:
            page.apply_redactions(images=0, graphics=0, text=0)
        for block in eligible:
            translated = correct_fragment(block["text"], cache[block["text"]])
            if insert_fitted(page, insertion_rect(page, block), translated, block["size"], block["bold"]):
                stats["translated"] += 1
            else:
                stats["failed"] += 1
        print(f"  page {page_number + 1}/{document.page_count}: {len(eligible)} translated blocks", flush=True)
    document.set_metadata({"title": f"Tradução pt-BR — {source.stem}", "author": "Projeto"})
    temporary = output.with_suffix(".translation.tmp.pdf")
    document.save(temporary, deflate=True)
    document.close()
    temporary.replace(output)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path(".pdf_translation_cache.json"))
    parser.add_argument("--only", default="", help="Exact PDF basename to process")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    sources = sorted(args.input_dir.glob("*.pdf"))
    if args.only:
        sources = [source for source in sources if source.name == args.only]
    if not sources:
        raise SystemExit("No source PDFs found")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cache = load_cache(args.cache)
    for source in sources:
        print(f"Translating {source.name}", flush=True)
        stats = translate_document(source, args.output_dir / source.name, cache, args.cache, max(1, args.workers))
        print(f"  done: {stats}", flush=True)


if __name__ == "__main__":
    main()
