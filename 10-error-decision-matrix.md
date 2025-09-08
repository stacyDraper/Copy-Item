# 10) Error & Decision Matrix — Copy-Item Flow (MVP)

## Legend

- **Severity**
  - **FATAL** → terminate run; no writes performed (or rollback creation).
  - **ERROR** → skip current item/field step; continue where safe.
  - **WARN** → non-blocking notice in output; run continues.
- **Action**
  - **Fail-fast** → stop the flow before any write.
  - **Skip** → don’t write this thing (field/file); continue.
  - **Retry** → automatic retry policy (429/5xx).
  - **Proceed** → continue as normal.

---

## A. Input & Schema Validation (pre-write)

| Case | Detection | Message (template) | Severity | Action | Output Impact |
|------|-----------|--------------------|----------|--------|---------------|
| Invalid map JSON | Parse failure | Invalid 'map' JSON: <parser message> | FATAL | Fail-fast | errors[+]; no writes |
| Invalid settings JSON | Parse failure | Invalid 'settings' JSON: <parser message> | FATAL | Fail-fast | errors[+] |
| Missing required input | Null/empty field | Missing required input: <name> | FATAL | Fail-fast | errors[+] |
| Unknown operation | Not in `create/update/upsert` | Unsupported operation: <value> | FATAL |  |  |
| Bad URL or list | 404/400 on site/list GET | List not found: <site>/<list> | FATAL | Fail-fast | errors[+] |

Notes: These satisfy FR-2, FR-13.1. No writes should occur.

---

## B. Matching & Operation Semantics

| Case | Detection | Message (template) | Severity | Action | Output Impact |
|------|-----------|--------------------|----------|--------|---------------|
| Update-only, no match | operation=update & matchedCount=0 | No match found for update (criteria: <summary>) | FATAL | Stop, no write | errors[+], matchedCount=0 |
| Upsert, no match | operation=upsert & matchedCount=0 | No match found; creating new item | INFO | Proceed → create | createdIds[1] |
| Multiple matches (non-bulk) | matchedCount>1 & bulk=false | Multiple matches (<n>); updated first, review criteria | WARN | Proceed update first | matchedCount=n, warnings[+] |
| Bulk intended but capped | bulk=true & matchedCount>1000 & guard off | Bulk safety exceeded: <n> items. Set COPYITEM_ALLOW_LARGE_BULK to proceed. | FATAL | Stop | errors[+] |
| Quick-match overridden | Both quick-match + settings.match present | settings.match overrides quick match by design | INFO | Proceed with settings | quickMatch=false |

Notes: Covers FR-3, FR-6, FR-7, FR-10, NFR-L1.

---

## C. Mapping & Field Semantics

| Case | Detection | Message | Severity | Action | Output Impact |
|------|-----------|---------|----------|--------|---------------|
| Dest field missing | destField not in schema | Destination field not found: <dest> | WARN | Skip field | fieldWarnings[+] |
| Dest field read-only/hidden | Schema flags | Field read-only/hidden: <dest> | WARN | Skip | fieldWarnings[+] |
| Type mismatch at transform | Transform can’t coerce | Type mismatch for <dest>: <detail> | WARN | Skip field | fieldWarnings[+] |
| when:"empty" default used | Source empty | Default applied to <dest> | INFO | Proceed | — |
| when:"always" default used | Always | Override applied to <dest> | INFO | Proceed | — |
| Empty after transforms | Value list becomes empty | No valid values after transforms for <dest> | WARN | Skip field | fieldWarnings[+] |

Notes: FR-4, FR-13.2.

---

## D. Transforms

| Transform | Case | Message | Severity | Action |
|-----------|------|---------|----------|--------|
| ensureUser | User not found/disabled | ensureUser failed for <value> | WARN | Skip that identity; if none remain, skip field |
| ensureUser | Partial success (multi) | ensureUser: 1 of <n> users not found | WARN | Write remaining IDs |
| lookupByText | No match | lookupByText: not found '<text>' | WARN | Skip that value |
| lookupByText | Multiple matches | lookupByText: ambiguous '<text>' — using first | WARN | Proceed with first |
| toUTC | Invalid date/time | toUTC: invalid datetime '<value>' | WARN | Skip field |
| toUTC | No timezone in source | toUTC: no offset; wrote as-is (or configured behavior) | WARN | Proceed |
| stripHTML | — | (no error; empty becomes empty) | — | — |

Notes: FR-5, FR-9.

---

## E. Write & API Calls

| Case | Detection | Message | Severity | Action | Output Impact |
|------|-----------|---------|----------|--------|---------------|
| Create failed | non-2xx on POST /items | Create failed: <status> <reason> | ERROR/FATAL* | Retry (429/5xx); else stop this item | errors[+] |
| Update failed (VULI) | non-2xx on validateupdatelistitem | Update failed (VULI): <status> <reason> | ERROR | Skip item; continue others | errors[+] |
| Partial field failures (VULI) | VULI returns field errors | Write error for <field>: <msg> | WARN | Skip those fields | fieldWarnings[+] |
| Concurrency (eTag) | 412 Precondition Failed | Concurrency conflict on item <id> | WARN | Retry once; else skip item | warnings[+] |

---

## F. Attachments

| Case | Detection | Message | Severity | Action | Output Impact |
|------|-----------|---------|----------|--------|---------------|
| No attachments on source | Attachments count 0 | No attachments on source | INFO | Proceed | — |
| Append: duplicate name | Name exists in dest | Attachment exists; skipped: <name> | WARN | Skip that file | attachments.skipped++ |
| Overwrite: delete failed | Recycle returns non-2xx | Overwrite failed to delete: <name> | WARN | Attempt upload anyway or skip | warnings[+] |
| Replace: delete all failed | Some deletions fail | Replace: <k> of <n> deletions failed | WARN | Continue with adds | warnings[+] |
| Upload failed | POST add(binary) non-2xx | Attachment upload failed: <name> <status> | WARN | Skip file | attachments.skipped++ |

Notes: FR-8.

---

## G. Auth & Permissions

| Case | Detection | Message | Severity | Action |
|------|-----------|---------|----------|--------|
| Unauthorized | 401/403 on any SPO call | Unauthorized for <site>/<list>: <status> | FATAL | Fail-fast |
| Insufficient perms for write | 403 on dest write | Insufficient permissions on destination | FATAL | Fail-fast |
| ensureUser blocked | 403 on ensureuser | ensureUser denied for <value> | WARN | Skip that person |

Notes: FR-15.

---

## H. Throttling & Transient Errors

| Case | Detection | Message | Severity | Action |
|------|-----------|---------|----------|--------|
| Throttled | 429 | Throttled (429) on <op>; retrying | INFO | Retry with backoff |
| Server error | 5xx | Server error <status> on <op>; retrying | INFO | Retry with backoff |
| Final retry failed | After attempts | Retries exhausted on <op> | ERROR | Skip item/field; continue |

Notes: NFR-R1.

---

## I. Safety & Limits

| Case | Detection | Message | Severity | Action |
|------|-----------|---------|----------|--------|
| Large bulk blocked | matchedCount>1000 & env not set | Bulk safety exceeded: <n> | FATAL | Stop |
| Attachment cap exceeded | >50 files or >100MB | Attachment cap exceeded; processed first <k> | WARN | Process up to cap; skip rest |
| Map size cap exceeded | map.length>200 | Map size exceeds limit (200) | FATAL | Fail-fast |

Notes: NFR-L1/2/3.

---

## J. Decision Precedence (tie-breakers)

1. Fatal validation (inputs/site/list) → stop before any write.
2. Operation semantics:
   - update: requires match; else FATAL.
   - upsert: 0 → create, ≥1 → update (bulk toggles all vs first).
   - create: skip matching entirely.
3. Matching precedence: settings.match overrides quick match.
4. Bulk precedence: if bulk=true, update all matches (subject to safety cap).
5. Field behavior: per-field failure → skip that field (WARN).

---

## K. Standardized Output Fragments

**Success (update, non-bulk)**

```json
{ "operation": "update", "bulk": false, "matchedCount": 1, "updatedIds": [123], "createdIds": [], "warnings": [], "errors": [] }
```

**Upsert with create**

```json
{ "operation": "upsert", "bulk": false, "matchedCount": 0, "createdIds": [456], "warnings": ["Default applied to Status"], "errors": [] }
```

**Fatal validation error**

```json
{ "operation": "update", "bulk": false, "matchedCount": 0, "createdIds": [], "updatedIds": [], "warnings": [], "errors": ["Missing required input: destListName"] }
```

---

## L. Message Style Guide

- Name the object: list/site/field/file.
- State the action: “skipped”, “updated first”, “creating new”.
- Quantify when possible.
- Avoid jargon; include status where useful.

Examples:
- Destination field not found: Owner
- Multiple matches (3); updated first (Id=42)
- lookupByText: ambiguous 'Vendor A' — using first
- Attachment exists; skipped: spec.pdf

---

## M. Developer Notes

- Centralize `addWarning(field, message)` and `addError(message)` helpers.
- Always include `matchMode` and `matchCriteriaSummary` in output.
- Wrap each write group in a scope so failures don’t affect others in bulk.
- For VULI responses, parse per-field messages to `fieldWarnings[]`.


### Update: Matrix expanded to cover WARN vs FATAL, retries, and attachment caps.
