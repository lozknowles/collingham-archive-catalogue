PRAGMA foreign_keys = ON;

INSERT INTO source_assets (
    asset_kind,
    source_label,
    source_path,
    checksum_sha256,
    notes
) VALUES (
    'pdf',
    'POC card.pdf from olmocr proof of concept',
    '/fast/olmocr-poc/card.pdf',
    NULL,
    'Original scan asset retained in the proof-of-concept workspace.'
);

INSERT INTO ocr_runs (
    source_asset_id,
    model_name,
    model_path,
    runtime_summary,
    pytorch_version,
    transformers_version,
    inference_dtype,
    attention_implementation,
    cpu_offload_enabled,
    max_gpu_memory_gib,
    max_cpu_memory_gib,
    notes
) VALUES (
    1,
    'Qwen2_5_VLForConditionalGeneration',
    '/fast/models/huggingface/olmOCR-2-7B-1025',
    'Working P5000 OCR proof of concept using float32 inference and CPU offload on Pascal hardware.',
    '2.4.1+cu121',
    NULL,
    'float32',
    'eager',
    1,
    14.0,
    48.0,
    'Baseline runtime preserved from /fast/olmocr-poc.'
);

INSERT INTO lexicon_entries (
    canonical_text,
    entry_type,
    status,
    notes,
    source_reference
) VALUES (
    'PIELICHATY',
    'surname',
    'manual_confirmed',
    'Confirmed by human correction from the David Johnson card sample.',
    'POC review note from /fast/olmocr-poc'
);

INSERT INTO lexicon_variants (
    lexicon_entry_id,
    variant_text,
    variant_type,
    confidence,
    source_reference,
    notes
) VALUES (
    1,
    'PIEU CHATY',
    'ocr_variant',
    1.0,
    'POC review note from /fast/olmocr-poc',
    'Observed OCR variant that should resolve to PIELICHATY.'
);

INSERT INTO catalogue_code_rules (
    rule_key,
    rule_name,
    rule_state,
    description,
    pattern,
    expected_parts_json,
    source_reference,
    notes
) VALUES (
    'structure_pending_authoritative_source',
    'Pending catalogue-code structure import',
    'pending_research',
    'Placeholder rule until the authoritative History Centre catalogue-code documentation is added to the project.',
    NULL,
    NULL,
    'Need source documentation from the History Centre archive code guidance',
    'No code semantics are inferred here.'
);

INSERT INTO catalogue_records (
    record_slug,
    source_asset_id,
    ocr_run_id,
    archive_reference_canonical,
    object_name,
    title,
    date_received,
    brief_description,
    donated_by,
    donation_date,
    copyright,
    associated_people_json,
    associated_places_json,
    home_location,
    home_location_date,
    current_location,
    current_location_date,
    physical_description,
    size,
    condition,
    notes,
    cross_references,
    public_access_summary,
    record_status,
    is_sample,
    provenance_note
) VALUES (
    'david-johnson-life-story',
    1,
    1,
    'EF/AA/JOH/7',
    'WORD DOCUMENT',
    'JOHNSON DAVID',
    'OCT 23',
    '''LIVING HISTORIES PROJECT'' LIFE STORY OF DAVID JOHNSON b 1934',
    'H PIELICHATY',
    'OCT 23',
    'H PIELICHATY',
    '["CROCKER","THOL WAITE","NEWSTEAD","NICHOLSON"]',
    '["79 HIGH ST","52 HIGH ST (CLEMATIS COTTAGE)","14 DYKES END","DYKES END COTTAGE","ST JOHN THE BAPTIST"]',
    'EF/AA/J-L',
    '12/2/2024',
    NULL,
    NULL,
    'ELEVEN PAGES OF A4. FRONT PAGE HAS PHOTO OF DAVID JOHNSON AND PHOTO OF 7A HIGH ST, COTTAGE WITH DRIVEWAY GATE IN FOREGROUND',
    'A4',
    'EXCELLENT',
    'POC sample record derived from the working olmOCR transcription.',
    'EF|AA|JOH|77 STORY OF THE JOHNSON FAMILY',
    'Archive reference EF/AA/JOH/7. Life story of David Johnson with Collingham place references including Dykes End Cottage.',
    'active',
    1,
    'Source scan preserved in /fast/olmocr-poc/card.pdf; raw OCR retained separately in history rows.'
);

INSERT INTO catalogue_record_history (
    record_id,
    event_type,
    field_name,
    raw_value,
    suggested_value,
    accepted_value,
    confidence,
    reason,
    reviewer_decision,
    reviewer_name,
    source_reference,
    notes
) VALUES (
    1,
    'ocr_import',
    'archive_reference_canonical',
    'EF/AA/JOH/8',
    'EF/AA/JOH/7',
    NULL,
    0.97,
    'OCR reading conflicts with the known human correction for the sample card.',
    'defer',
    NULL,
    '/fast/olmocr-poc/output/card/card.md',
    'Keep the raw OCR value and the suggested correction separate from the accepted canonical value.'
);

INSERT INTO catalogue_record_history (
    record_id,
    event_type,
    field_name,
    raw_value,
    suggested_value,
    accepted_value,
    confidence,
    reason,
    reviewer_decision,
    reviewer_name,
    source_reference,
    notes
) VALUES (
    1,
    'human_review',
    'donated_by',
    'H PIEU CHATY',
    'H PIELICHATY',
    'H PIELICHATY',
    1.0,
    'Confirmed canonical surname stored in the lexicon.',
    'accept',
    'POC reviewer',
    '/fast/olmocr-poc/output/card/card.md',
    'Known OCR variant PIEU CHATY is stored in the local lexicon.'
);

INSERT INTO catalogue_code_checks (
    record_id,
    raw_code,
    suggested_code,
    canonical_code,
    rule_id,
    result,
    confidence,
    reason,
    reviewer_name,
    source_reference
) VALUES (
    1,
    'EF/AA/JOH/8',
    'EF/AA/JOH/7',
    'EF/AA/JOH/7',
    1,
    'needs_review',
    0.97,
    'Sample code conflicts with the human-corrected archive reference; no rule semantics are assumed yet.',
    'POC reviewer',
    '/fast/olmocr-poc/output/card/card.md'
);

INSERT INTO public_exports (
    export_name,
    export_scope,
    export_format,
    source_reference,
    notes
) VALUES (
    'sample-david-johnson-public-export',
    'public',
    'json',
    'Derived from catalogue_records.record_id = 1',
    'Curated export only contains public-facing catalogue fields.'
);

