# Copy‑Item Flow — Build Checklist (Stages 1→7)

## Stage 1 — Input Validation & Defaulting
- Trigger (Manual) with friendly labels + hint text (done above).
- Init variables (v_*) from trigger labels (done above).
- Defaults & coercion: operation=upsert, attachmentMode=none, mapOnly=true.
- Parse JSON: v_map and v_settings → objects; on parse failure add to v_errors and Terminate (Failed).
- Required checks: Source Site URL, Source List Name, Destination Site URL, Destination List Name, and non‑empty map. Fail‑fast with field names.
- Resolve v_srcItemId (use selected‑item context if blank).
- Abort on unknown operation/bad choices (guard values).

**Output after Stage 1:** valid v_settings (object), v_map (array), v_srcItemId (int), and early termination paths wired.

## Stage 2 — Source Item Retrieval
- HTTP GET source item /_api/web/lists/getbytitle('{src}')/items({v_srcItemId})?$select=* (+ $expand=AttachmentFiles,FieldValuesAsText when needed). Save to v_srcItem.
- Handle 404/403 as FATAL (missing list/perms).

## Stage 3 — Destination Schema Retrieval
- HTTP GET dest fields: .../fields?$select=InternalName,TypeAsString,ReadOnlyField,Hidden,LookupList,LookupField,AllowMultipleValues. Store filtered editable fields in v_destFields.
- Skip read‑only/hidden; warn per field if mapped.

## Stage 4 — Match Determination
- If Quick Match (Quick Match Column + Value) present, synthesize internal settings.match (simple equality). Else use settings.match. settings.match overrides quick match.
- Execute per mode: simple→CAML, odata→$filter, caml→raw ViewXml; collect v_matchedIds.
- Bulk guard: if bulk=true and matchedCount>1000 without override env → FATAL.

## Stage 5 — Write (Create/Update/Upsert)
- Build formValues[] from v_map + v_srcItem + v_destFields, applying transforms in order (ensureUser, lookupByText, toUTC, stripHTML, etc.).
- Create path: POST /items → Id, then POST validateupdatelistitem with formValues.
- Update/Upsert paths: VULI against each Id (respect bulk). Upsert creates when no match.
- Per‑field failures → fieldWarnings[], continue. Retries on 429/5xx (min 1s, max 30s, 3 attempts).

## Stage 6 — Attachments
- Implement none/append/overwrite/replace against AttachmentFiles endpoints with counts to v_attachmentSummary. Cap: ≤50 files or ≤100 MB per item (warn on excess).
- Log duplicates/failed uploads as WARN, continue.

## Stage 7 — Output Assembly
- Compose final output per Output schema (operation, bulk, quickMatch/destMatch, matchMode, matchCriteriaSummary, matchedCount, createdIds, updatedIds, attachments, fieldWarnings, warnings, errors). Return it.
- Optional: append summary row to COPYITEM_RUNLOG_LIST if env var present.

---

## Mini “Definition of Done”
- All SMK tests pass (SMK‑01…05).
- Core matrix scenarios OP/AM/BK/AT/MP/TF/ER green.
- Output contract exactly matches spec.

If you want, I can drop a Stage 1 “paste pack” next—defaults, JSON parse actions, required checks, and the terminate payload—so you can implement Stage 1 end‑to‑end in one shot.
