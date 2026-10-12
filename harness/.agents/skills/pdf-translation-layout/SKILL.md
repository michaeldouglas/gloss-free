---
name: pdf-translation-layout
description: Translate project PDFs while preserving the original page layout, images, graphics, and selectable text; use for repeated English-to-Brazilian-Portuguese PDF translation in this dissertation workspace.
---

# PDF translation with layout preservation

Use this skill when the user asks to translate PDFs from `materiais/en` or an equivalent source directory into `materiais/pt` without changing the originals.

## Required outcome

- Keep every source PDF unchanged.
- Write a translated PDF with the same basename into the requested output directory.
- Preserve page count, page geometry, images, figures, vector graphics, columns, and tables as far as the source PDF permits.
- Remove the original selectable text layer from translated blocks so copying text does not produce English-plus-Portuguese duplicates.
- Validate the output before handoff; do not claim completion if a block was dropped or an output PDF cannot be extracted.

## Workflow

1. Confirm the current branch is a `feature/*` branch and inspect the worktree. Do not commit on `main` or `develop`.
2. Discover only the requested source PDFs. Never treat existing PDFs already in `materiais/pt` as source inputs.
3. Tell the user if text is being sent to an external translation endpoint. Do not use this workflow for confidential PDFs without explicit authorization.
4. Run [scripts/translate_pdf_layout.py](scripts/translate_pdf_layout.py), normally with `--input-dir ..\materiais\en --output-dir ..\materiais\pt` from `harness`.
5. Use the script's cache only for resumability. Delete the cache after a successful run; never place it in the output folder.
6. Validate page counts and text extraction. Scan for known failure patterns such as concatenated headings (`3MÉTODO`), soft hyphens, non-breaking spaces, dropped fragments, `???`, and empty translated blocks.
7. Report the output directory, unchanged originals, validation results, branch, and whether a commit/PR was created. Do not create a commit or PR unless requested.

## Non-obvious implementation rules

- Use PyMuPDF redactions with images and graphics retained, then insert translated text in the original text boxes. Do not rebuild the PDF from plain extracted text; that loses layout and figures.
- Use built-in Helvetica/Helvetica-Bold for inserted Portuguese text so ordinary spaces and hyphens remain correct in the selectable layer. Windows TTF mappings can expose them as NBSP/soft-hyphen characters.
- Expand short heading boxes to the current column width before shrinking the font. Try smaller fonts as a fallback, but never leave a redacted block empty.
- Preserve source blocks that intersect images, contain CJK text, control characters, equations, or unsupported mathematical symbols. A readable original block is preferable to `?` glyphs or corrupted formulas.
- Handle page-boundary fragments explicitly. In the known source corpus, `vari-` at the end of one page and `ety of tasks` at the next page must become `variedade de tarefas`, not an independent translation of `ety`.
- The result is a layout-preserving automatic translation, not a publication-ready human copyedit. Flag any preserved English/math/CJK blocks and recommend manual review where appropriate.

The helper script uses the Google Translate web endpoint without an API key. Treat this as an external service and follow the user's authorization and privacy requirements.
