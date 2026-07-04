# Changelog

## Unreleased

- Added a minimal Flask-based local review app with list, detail, edit, queue, and lexicon screens.
- Added a repo-local run script and a route smoke checker.
- Created the initial provenance-first project foundation.
- Added SQLite schema tables for source assets, OCR runs, canonical records, append-only history, lexicon entries, lexicon variants, and catalogue-code checks.
- Added a lexicon audit table for append-only maintenance history.
- Added a sample David Johnson record based on the working OCR proof of concept.
- Added a confirmed lexicon entry for `PIELICHATY` with `PIEU CHATY` as a known OCR variant.
- Added a curated public export example that excludes raw OCR and internal review data.
- Documented the P5000 OCR runtime constraints and the `/fast/olmocr-poc` baseline.
