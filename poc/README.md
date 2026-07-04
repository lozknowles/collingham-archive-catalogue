# OCR Proof of Concept

This directory contains the working files copied from `/fast/olmocr-poc` so the proven OCR baseline is preserved alongside the catalogue project.

## Included artifacts

- `olmocr-p5000.py` - working local OCR script for the Quadro P5000 setup
- `test_olmocr_direct.py` - direct model test script
- `card.pdf` - two-page sample catalogue card PDF
- `card-pages/` - rendered page images from the proof of concept
- `card-pages-small/` - smaller rendered page images from the proof of concept
- `output/card/` - OCR output markdown, JSON, and page images
- `test-pdfs/smoke.pdf` - smoke test PDF
- `smoke.png` - smoke test image
- `olmocr-pipeline-debug.log` - pipeline debug log
- `work/` - work index artifact used during the proof of concept

The goal is preservation, not refactoring. The catalogue project should refer back to these files as the baseline OCR evidence trail until a dedicated ingestion pipeline is built.

