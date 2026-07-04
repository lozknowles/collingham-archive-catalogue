PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_assets (
    source_asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_kind TEXT NOT NULL CHECK (asset_kind IN ('pdf', 'image', 'scan_bundle', 'other')),
    source_label TEXT NOT NULL,
    source_path TEXT NOT NULL,
    checksum_sha256 TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ocr_runs (
    ocr_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_asset_id INTEGER,
    model_name TEXT NOT NULL,
    model_path TEXT NOT NULL,
    runtime_summary TEXT NOT NULL,
    pytorch_version TEXT,
    transformers_version TEXT,
    inference_dtype TEXT NOT NULL,
    attention_implementation TEXT NOT NULL,
    cpu_offload_enabled INTEGER NOT NULL DEFAULT 1 CHECK (cpu_offload_enabled IN (0, 1)),
    max_gpu_memory_gib REAL,
    max_cpu_memory_gib REAL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_asset_id) REFERENCES source_assets(source_asset_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS catalogue_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_slug TEXT NOT NULL UNIQUE,
    source_asset_id INTEGER,
    ocr_run_id INTEGER,
    archive_reference_canonical TEXT NOT NULL,
    object_name TEXT NOT NULL,
    title TEXT NOT NULL,
    date_received TEXT,
    brief_description TEXT,
    donated_by TEXT,
    donation_date TEXT,
    copyright TEXT,
    associated_people_json TEXT NOT NULL DEFAULT '[]',
    associated_places_json TEXT NOT NULL DEFAULT '[]',
    home_location TEXT,
    home_location_date TEXT,
    current_location TEXT,
    current_location_date TEXT,
    physical_description TEXT,
    size TEXT,
    condition TEXT,
    notes TEXT,
    cross_references TEXT,
    public_access_summary TEXT NOT NULL,
    record_status TEXT NOT NULL DEFAULT 'active' CHECK (record_status IN ('active', 'superseded', 'withdrawn')),
    is_sample INTEGER NOT NULL DEFAULT 0 CHECK (is_sample IN (0, 1)),
    provenance_note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_asset_id) REFERENCES source_assets(source_asset_id) ON DELETE SET NULL,
    FOREIGN KEY (ocr_run_id) REFERENCES ocr_runs(ocr_run_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS catalogue_record_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'ocr_import',
            'human_review',
            'manual_edit',
            'lexicon_update',
            'export_preparation',
            'validation',
            'correction'
        )
    ),
    field_name TEXT,
    raw_value TEXT,
    suggested_value TEXT,
    accepted_value TEXT,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    reason TEXT,
    reviewer_decision TEXT CHECK (
        reviewer_decision IN ('accept', 'correct', 'reject', 'defer', 'info') OR reviewer_decision IS NULL
    ),
    reviewer_name TEXT,
    source_reference TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (record_id) REFERENCES catalogue_records(record_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lexicon_entries (
    lexicon_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_text TEXT NOT NULL,
    entry_type TEXT NOT NULL CHECK (
        entry_type IN (
            'person',
            'surname',
            'place',
            'building',
            'street',
            'church',
            'organisation',
            'object_type',
            'catalogue_code_component',
            'other'
        )
    ),
    status TEXT NOT NULL DEFAULT 'manual_confirmed' CHECK (status IN ('manual_confirmed', 'provisional', 'retired')),
    notes TEXT,
    source_reference TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (canonical_text, entry_type)
);

CREATE TABLE IF NOT EXISTS lexicon_variants (
    variant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lexicon_entry_id INTEGER NOT NULL,
    variant_text TEXT NOT NULL,
    variant_type TEXT NOT NULL CHECK (
        variant_type IN ('ocr_variant', 'spelling_variant', 'historical_variant', 'alias')
    ),
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    source_reference TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (lexicon_entry_id) REFERENCES lexicon_entries(lexicon_entry_id) ON DELETE CASCADE,
    UNIQUE (lexicon_entry_id, variant_text)
);

CREATE TABLE IF NOT EXISTS catalogue_code_rules (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_key TEXT NOT NULL UNIQUE,
    rule_name TEXT NOT NULL,
    rule_state TEXT NOT NULL DEFAULT 'pending_research' CHECK (
        rule_state IN ('pending_research', 'active', 'retired')
    ),
    description TEXT NOT NULL,
    pattern TEXT,
    expected_parts_json TEXT,
    source_reference TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS catalogue_code_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER,
    raw_code TEXT NOT NULL,
    suggested_code TEXT,
    canonical_code TEXT,
    rule_id INTEGER,
    result TEXT NOT NULL CHECK (
        result IN ('match', 'suggested_correction', 'needs_review', 'rejected')
    ),
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    reason TEXT,
    reviewer_name TEXT,
    source_reference TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (record_id) REFERENCES catalogue_records(record_id) ON DELETE SET NULL,
    FOREIGN KEY (rule_id) REFERENCES catalogue_code_rules(rule_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public_exports (
    export_id INTEGER PRIMARY KEY AUTOINCREMENT,
    export_name TEXT NOT NULL,
    export_scope TEXT NOT NULL CHECK (export_scope IN ('public', 'internal')),
    export_format TEXT NOT NULL CHECK (export_format IN ('json', 'markdown', 'csv')),
    source_reference TEXT,
    generated_at TEXT NOT NULL DEFAULT (datetime('now')),
    notes TEXT
);

