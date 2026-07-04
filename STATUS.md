# Status

Current stage: foundation
Current stage detail: minimal local review CRUD app added

## What exists now

- Repository cloned from `lozknowles/collingham-archive-catalogue`
- Initial SQLite schema for catalogue records, OCR runs, audit history, lexicon entries, and catalogue-code checks
- Sample David Johnson card record marked as POC/sample data
- Initial lexicon seed with `PIELICHATY` as a confirmed canonical surname and `PIEU CHATY` as a known OCR variant
- Public export example that only exposes curated catalogue fields
- Local bootstrap script for creating a SQLite database
- Copied proof-of-concept OCR working files into `poc/`
- Minimal Flask review app with list, detail, edit, queue, and lexicon screens
- Route smoke checker for local verification
- Repo-local virtualenv run script

## Source of truth

- Canonical catalogue store: SQLite
- OCR baseline: `/fast/olmocr-poc`
- Proven working model path: `/fast/models/huggingface/olmOCR-2-7B-1025`

## Runtime constraints

- Quadro P5000 16 GB
- Pascal GPU, so the stable path is float32 inference with CPU offload
- PyTorch 2.4.1+cu121
- `Qwen2_5_VLForConditionalGeneration`
- approximately 14 GiB GPU memory and 48 GiB CPU memory
- eager attention

## Design priorities

- preserve provenance
- keep append-only correction history
- keep append-only lexicon audit history
- keep public exports curated
- keep catalogue-code validation conservative until source documents are imported
