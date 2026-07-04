from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

from .db import connect, fetch_all, fetch_one, from_text_list, to_json_list


RECORD_FIELDS = [
    "archive_reference_canonical",
    "object_name",
    "title",
    "date_received",
    "brief_description",
    "donated_by",
    "donation_date",
    "copyright",
    "home_location",
    "home_location_date",
    "current_location",
    "current_location_date",
    "physical_description",
    "size",
    "condition",
    "notes",
    "cross_references",
    "public_access_summary",
    "record_status",
    "provenance_note",
]


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = os.environ.get(
        "COLLINGHAM_DB",
        str((Path(__file__).resolve().parent.parent / "data" / "collingham-archive-catalogue.sqlite")),
    )

    @app.template_filter("nl2br")
    def nl2br(value: str | None) -> str:
        return (value or "").replace("\n", "<br>")

    @app.get("/")
    def index():
        return redirect(url_for("record_list"))

    @app.get("/records")
    def record_list():
        search = request.args.get("search", "").strip()
        query = """
            SELECT r.*,
                   (
                       SELECT COUNT(*)
                       FROM catalogue_record_history h
                       WHERE h.record_id = r.record_id
                         AND (h.reviewer_decision IS NULL OR h.reviewer_decision = 'defer')
                   ) AS pending_count
            FROM catalogue_records r
        """
        params: tuple[object, ...] = ()
        if search:
            query += """
                WHERE
                    r.archive_reference_canonical LIKE ?
                    OR r.title LIKE ?
                    OR r.object_name LIKE ?
                    OR r.brief_description LIKE ?
                    OR r.public_access_summary LIKE ?
                    OR r.associated_people_json LIKE ?
                    OR r.associated_places_json LIKE ?
            """
            like = f"%{search}%"
            params = (like, like, like, like, like, like, like)
        query += " ORDER BY r.updated_at DESC, r.record_id DESC"
        with connect(app.config["DATABASE_PATH"]) as conn:
            records = fetch_all(conn, query, params)
            queue_count = fetch_one(
                conn,
                """
                SELECT COUNT(*)
                FROM catalogue_record_history
                WHERE reviewer_decision IS NULL OR reviewer_decision = 'defer'
                """,
            )[0]
            lexicon_count = fetch_one(conn, "SELECT COUNT(*) FROM lexicon_entries")[0]
        return render_template(
            "record_list.html",
            records=records,
            search=search,
            queue_count=queue_count,
            lexicon_count=lexicon_count,
        )

    @app.get("/records/<int:record_id>")
    def record_detail(record_id: int):
        with connect(app.config["DATABASE_PATH"]) as conn:
            record = fetch_one(conn, "SELECT * FROM catalogue_records WHERE record_id = ?", (record_id,))
            if record is None:
                abort(404)
            history = fetch_all(
                conn,
                """
                SELECT *
                FROM catalogue_record_history
                WHERE record_id = ?
                ORDER BY created_at DESC, history_id DESC
                """,
                (record_id,),
            )
            code_checks = fetch_all(
                conn,
                """
                SELECT c.*, r.rule_name
                FROM catalogue_code_checks c
                LEFT JOIN catalogue_code_rules r ON r.rule_id = c.rule_id
                WHERE c.record_id = ?
                ORDER BY c.created_at DESC, c.check_id DESC
                """,
                (record_id,),
            )
        return render_template(
            "record_detail.html",
            record=record,
            history=history,
            code_checks=code_checks,
            people=to_json_list(record["associated_people_json"]),
            places=to_json_list(record["associated_places_json"]),
        )

    @app.post("/records/<int:record_id>/edit")
    def record_edit(record_id: int):
        reviewer_name = request.form.get("reviewer_name", "").strip() or "anonymous"
        reason = request.form.get("reason", "").strip() or "Manual review edit"
        with connect(app.config["DATABASE_PATH"]) as conn:
            record = fetch_one(conn, "SELECT * FROM catalogue_records WHERE record_id = ?", (record_id,))
            if record is None:
                abort(404)

            updates: dict[str, object] = {}
            history_rows: list[dict[str, object | None]] = []
            for field in RECORD_FIELDS:
                if field in {"public_access_summary", "notes", "brief_description", "provenance_note", "cross_references"}:
                    new_value = request.form.get(field, "").strip()
                elif field in {"associated_people_json", "associated_places_json"}:
                    continue
                else:
                    new_value = request.form.get(field, "").strip()
                if field == "record_status" and not new_value:
                    new_value = "active"
                old_value = record[field]
                if old_value is None:
                    old_value = ""
                if str(old_value) != new_value:
                    updates[field] = new_value
                    history_rows.append(
                        {
                            "event_type": "manual_edit",
                            "field_name": field,
                            "raw_value": str(old_value),
                            "suggested_value": new_value,
                            "accepted_value": new_value,
                            "confidence": 1.0,
                            "reason": reason,
                            "reviewer_decision": "accept",
                            "reviewer_name": reviewer_name,
                            "source_reference": request.path,
                            "notes": "Updated from archivist review form.",
                        }
                    )

            people_text = request.form.get("associated_people_text", "").strip()
            places_text = request.form.get("associated_places_text", "").strip()
            people_json = from_text_list(people_text) if people_text else "[]"
            places_json = from_text_list(places_text) if places_text else "[]"
            if people_json != record["associated_people_json"]:
                updates["associated_people_json"] = people_json
                history_rows.append(
                    {
                        "event_type": "manual_edit",
                        "field_name": "associated_people_json",
                        "raw_value": record["associated_people_json"],
                        "suggested_value": people_json,
                        "accepted_value": people_json,
                        "confidence": 1.0,
                        "reason": reason,
                        "reviewer_decision": "accept",
                        "reviewer_name": reviewer_name,
                        "source_reference": request.path,
                        "notes": "Updated from archivist review form.",
                    }
                )
            if places_json != record["associated_places_json"]:
                updates["associated_places_json"] = places_json
                history_rows.append(
                    {
                        "event_type": "manual_edit",
                        "field_name": "associated_places_json",
                        "raw_value": record["associated_places_json"],
                        "suggested_value": places_json,
                        "accepted_value": places_json,
                        "confidence": 1.0,
                        "reason": reason,
                        "reviewer_decision": "accept",
                        "reviewer_name": reviewer_name,
                        "source_reference": request.path,
                        "notes": "Updated from archivist review form.",
                    }
                )

            if updates:
                updates["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                assignments = ", ".join(f"{key} = :{key}" for key in updates)
                updates["record_id"] = record_id
                conn.execute(f"UPDATE catalogue_records SET {assignments} WHERE record_id = :record_id", updates)
                for row in history_rows:
                    conn.execute(
                        """
                        INSERT INTO catalogue_record_history (
                            record_id, event_type, field_name, raw_value, suggested_value,
                            accepted_value, confidence, reason, reviewer_decision, reviewer_name,
                            source_reference, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record_id,
                            row["event_type"],
                            row["field_name"],
                            row["raw_value"],
                            row["suggested_value"],
                            row["accepted_value"],
                            row["confidence"],
                            row["reason"],
                            row["reviewer_decision"],
                            row["reviewer_name"],
                            row["source_reference"],
                            row["notes"],
                        ),
                    )
                conn.commit()
        return redirect(url_for("record_detail", record_id=record_id))

    def _apply_history_decision(conn, history_id: int, decision: str, reviewed_value: str | None, reviewer_name: str, reason: str) -> int:
        target = fetch_one(
            conn,
            """
            SELECT h.*, r.record_slug
            FROM catalogue_record_history h
            JOIN catalogue_records r ON r.record_id = h.record_id
            WHERE h.history_id = ?
            """,
            (history_id,),
        )
        if target is None:
            abort(404)
        record_id = int(target["record_id"])
        field_name = target["field_name"]
        accepted_value = reviewed_value if reviewed_value is not None else (target["suggested_value"] or target["raw_value"])
        if accepted_value is None:
            accepted_value = ""

        resulting_history_id = None
        if decision in {"accept", "correct"} and field_name:
            updated_value = accepted_value
            conn.execute(
                f"UPDATE catalogue_records SET {field_name} = ?, updated_at = ? WHERE record_id = ?",
                (updated_value, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), record_id),
            )
            result_cur = conn.execute(
                """
                INSERT INTO catalogue_record_history (
                    record_id, event_type, field_name, raw_value, suggested_value, accepted_value,
                    confidence, reason, reviewer_decision, reviewer_name, source_reference, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    "human_review",
                    field_name,
                    target["raw_value"],
                    target["suggested_value"],
                    accepted_value,
                    target["confidence"],
                    reason,
                    decision,
                    reviewer_name,
                    request.path,
                    f"Reviewed history item {history_id}.",
                ),
            )
            resulting_history_id = result_cur.lastrowid

        if decision == "reject":
            result_cur = conn.execute(
                """
                INSERT INTO catalogue_record_history (
                    record_id, event_type, field_name, raw_value, suggested_value, accepted_value,
                    confidence, reason, reviewer_decision, reviewer_name, source_reference, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    "validation",
                    field_name,
                    target["raw_value"],
                    target["suggested_value"],
                    None,
                    target["confidence"],
                    reason,
                    decision,
                    reviewer_name,
                    request.path,
                    f"Reviewed history item {history_id}.",
                ),
            )
            resulting_history_id = result_cur.lastrowid

        conn.execute(
            """
            INSERT INTO catalogue_history_decisions (
                source_history_id, resulting_history_id, decision, accepted_value, reviewer_name, reason
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                history_id,
                resulting_history_id,
                decision,
                accepted_value if decision in {"accept", "correct"} else None,
                reviewer_name,
                reason,
            ),
        )
        conn.commit()
        return record_id

    @app.post("/history/<int:history_id>/decision")
    def history_decision(history_id: int):
        decision = request.form.get("decision", "").strip()
        reviewer_name = request.form.get("reviewer_name", "").strip() or "anonymous"
        reason = request.form.get("reason", "").strip() or "Archivist review decision"
        reviewed_value = request.form.get("reviewed_value", "").strip() or None
        if decision not in {"accept", "reject", "correct"}:
            abort(400)
        with connect(app.config["DATABASE_PATH"]) as conn:
            record_id = _apply_history_decision(conn, history_id, decision, reviewed_value, reviewer_name, reason)
        return redirect(url_for("record_detail", record_id=record_id))

    @app.get("/review-queue")
    def review_queue():
        with connect(app.config["DATABASE_PATH"]) as conn:
            rows = fetch_all(
                conn,
                """
                SELECT h.*, r.record_slug, r.archive_reference_canonical, r.title, r.object_name
                FROM catalogue_record_history h
                JOIN catalogue_records r ON r.record_id = h.record_id
                WHERE (h.reviewer_decision IS NULL OR h.reviewer_decision = 'defer')
                  AND NOT EXISTS (
                      SELECT 1
                      FROM catalogue_history_decisions d
                      WHERE d.source_history_id = h.history_id
                  )
                ORDER BY h.created_at ASC, h.history_id ASC
                """,
            )
        return render_template("review_queue.html", rows=rows)

    @app.post("/review-queue/<int:history_id>")
    def review_queue_action(history_id: int):
        decision = request.form.get("decision", "").strip()
        reviewer_name = request.form.get("reviewer_name", "").strip() or "anonymous"
        reason = request.form.get("reason", "").strip() or "Queue review decision"
        reviewed_value = request.form.get("reviewed_value", "").strip() or None
        if decision not in {"accept", "reject", "correct"}:
            abort(400)
        with connect(app.config["DATABASE_PATH"]) as conn:
            record_id = _apply_history_decision(conn, history_id, decision, reviewed_value, reviewer_name, reason)
        return redirect(url_for("record_detail", record_id=record_id))

    @app.get("/lexicon")
    def lexicon():
        with connect(app.config["DATABASE_PATH"]) as conn:
            entries = fetch_all(
                conn,
                """
                SELECT e.*,
                       COUNT(v.variant_id) AS variant_count
                FROM lexicon_entries e
                LEFT JOIN lexicon_variants v ON v.lexicon_entry_id = e.lexicon_entry_id
                GROUP BY e.lexicon_entry_id
                ORDER BY e.entry_type, e.canonical_text
                """,
            )
            variants = fetch_all(
                conn,
                """
                SELECT v.*, e.canonical_text, e.entry_type
                FROM lexicon_variants v
                JOIN lexicon_entries e ON e.lexicon_entry_id = v.lexicon_entry_id
                ORDER BY e.entry_type, e.canonical_text, v.variant_text
                """,
            )
            history = fetch_all(
                conn,
                """
                SELECT *
                FROM lexicon_history
                ORDER BY created_at DESC, lexicon_history_id DESC
                """,
            )
        return render_template("lexicon.html", entries=entries, variants=variants, history=history)

    @app.post("/lexicon/entries")
    def lexicon_entry_create():
        canonical_text = request.form.get("canonical_text", "").strip()
        entry_type = request.form.get("entry_type", "").strip()
        reviewer_name = request.form.get("reviewer_name", "").strip() or "anonymous"
        notes = request.form.get("notes", "").strip()
        source_reference = request.form.get("source_reference", "").strip()
        if not canonical_text or not entry_type:
            abort(400)
        with connect(app.config["DATABASE_PATH"]) as conn:
            cur = conn.execute(
                """
                INSERT INTO lexicon_entries (canonical_text, entry_type, status, notes, source_reference)
                VALUES (?, ?, 'manual_confirmed', ?, ?)
                """,
                (canonical_text, entry_type, notes or None, source_reference or None),
            )
            entry_id = cur.lastrowid
            conn.execute(
                """
                INSERT INTO lexicon_history (
                    lexicon_entry_id, event_type, field_name, raw_value, accepted_value,
                    reason, reviewer_decision, reviewer_name, source_reference, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    "create_entry",
                    "canonical_text",
                    canonical_text,
                    canonical_text,
                    "Created via archivist lexicon form.",
                    "accept",
                    reviewer_name,
                    source_reference or request.path,
                    notes or None,
                ),
            )
            conn.commit()
        return redirect(url_for("lexicon"))

    @app.post("/lexicon/variants")
    def lexicon_variant_create():
        lexicon_entry_id = request.form.get("lexicon_entry_id", "").strip()
        variant_text = request.form.get("variant_text", "").strip()
        variant_type = request.form.get("variant_type", "").strip()
        reviewer_name = request.form.get("reviewer_name", "").strip() or "anonymous"
        confidence_text = request.form.get("confidence", "").strip()
        source_reference = request.form.get("source_reference", "").strip()
        notes = request.form.get("notes", "").strip()
        if not lexicon_entry_id or not variant_text or not variant_type:
            abort(400)
        confidence = float(confidence_text) if confidence_text else None
        with connect(app.config["DATABASE_PATH"]) as conn:
            cur = conn.execute(
                """
                INSERT INTO lexicon_variants (
                    lexicon_entry_id, variant_text, variant_type, confidence, source_reference, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(lexicon_entry_id),
                    variant_text,
                    variant_type,
                    confidence,
                    source_reference or None,
                    notes or None,
                ),
            )
            variant_id = cur.lastrowid
            conn.execute(
                """
                INSERT INTO lexicon_history (
                    lexicon_entry_id, variant_id, event_type, field_name, raw_value, accepted_value,
                    confidence, reason, reviewer_decision, reviewer_name, source_reference, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(lexicon_entry_id),
                    variant_id,
                    "create_variant",
                    "variant_text",
                    variant_text,
                    variant_text,
                    confidence,
                    "Added variant via archivist lexicon form.",
                    "accept",
                    reviewer_name,
                    source_reference or request.path,
                    notes or None,
                ),
            )
            conn.commit()
        return redirect(url_for("lexicon"))

    return app
