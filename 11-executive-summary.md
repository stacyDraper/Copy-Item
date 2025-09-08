# Copy-Item Flow — Executive Summary (MVP)

## Purpose
A reusable Power Automate flow that copies a SharePoint list item — fields + optional attachments — between lists/sites in the same tenant. Supports **create**, **update**, and **upsert**.

---

## What Makes This Different
- **Configurable at run time:** Operators choose source/destination, operation, quick match, attachment behavior, and supply a mapping JSON per run.  
  *No redeploys. No code edits.*
- **Dynamic columns (schema-aware):** The flow discovers destination fields at run time and only writes to columns that exist and are editable.  
  *Nothing is hard-coded; works across different lists as long as internal names match your mapping.*

---

## Core Capabilities (MVP)
- **Field mapping (`map` array):** `source` → `dest`, with optional `default`, `when`, `transform`, `typeHint`.
  - **Built-in transforms:** `ensureUser`, `lookupByText`, `toUTC`, `stripHTML` (+ small utilities like `trim`, `split`, `join`).
- **Matching:**
  - **Quick match (no JSON):** `destMatchColumn` + `destMatchValue`.
  - **Advanced match (`settings.match`):** `simple` (JSON → CAML), `odata`, or `caml`.
  - **Modes:** `create`, `update` (fail if no match), `upsert` (create if none).
- **Attachments:** `none` (default), `append`, `overwrite`, `replace`.
- **Field types:** Text, Number, DateTime, Boolean, URL, Choice (single/multi), Lookup (single/multi), Person (single/multi).
- **Output:** Structured JSON with `createdIds`, `updatedIds`, `matchedCount`, attachments summary, warnings, and errors.

---

## Trigger Parameters (UI)

| Param            | Example                                                              | Purpose                                     |
|------------------|----------------------------------------------------------------------|---------------------------------------------|
| sourceSiteUrl    | https://contoso/sites/Source                                         | Source site                                 |
| sourceListName   | Tasks                                                                | Source list                                 |
| destSiteUrl      | https://contoso/sites/Dest                                           | Destination site                            |
| destListName     | TasksArchive                                                         | Destination list                            |
| sourceItemId     | 42                                                                   | Source item (optional; auto from selected)  |
| operation        | create / update / upsert                                             | Write behavior                              |
| destMatchColumn  | Title                                                                | Quick match column (optional)               |
| destMatchValue   | Widget-123                                                           | Quick match value (optional)                |
| map              | `[{"source":"Title","dest":"Title"}]`                                | Field mapping (runtime)                     |
| attachmentMode   | none                                                                 | Attachments behavior                         |
| mapOnly          | true                                                                 | Only write mapped fields                    |
| settings         | `{ "match": { "mode":"odata", "criteria":{ "$filter":"Status eq 'Active'" }}}` | Advanced options (optional)                 |

---

## How the Runtime Config Works (In Practice)
- Operator fills the trigger (no code):
```json
"map": [
  { "source": "Title", "dest": "Title" },
  { "source": "AssignedToEmail", "dest": "Owner", "transform": ["ensureUser"], "typeHint": "User" }
]
```
- Flow reads destination schema at run time; if **Owner** exists and is writeable, it writes.  
  If not, it logs a warning and skips — no crash, no schema bake-in.
- If `destMatchColumn=Title` and `destMatchValue=Widget-123`, the flow auto-builds a simple match; otherwise it uses `settings.match`.

---

## Error Handling & Safety (Highlights)
- Fail fast on bad inputs/sites/lists or update with no match.
- Skip + warn for missing destination fields, transform failures, ambiguous lookups, or duplicate attachments (mode-dependent).
- Retries on 429/5xx (SharePoint throttling).

---

## What’s Not in MVP
- Cross-type copies (e.g., doc library ↔ list).
- Profile/jobs abstraction.
- Fancy report exports.  
  *(All can be added without changing the trigger contract; extensions live in `settings`.)*

---

## Why This Matters
- Teams can run and adapt on the fly — map new columns or change matching without waiting for a new flow version.
- One flow supports many lists because columns are dynamic and validation is schema-aware at run time.


### Update: Added summary of resilience features—retry logic, WARN/FATAL semantics, capped attachments.
