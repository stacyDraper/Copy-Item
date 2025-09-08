
# 7) Architecture Spec — Copy-Item Flow (MVP)

## 7.1 High-Level Flow
Trigger (manual or selected item)  
↓  
Input Validation & Defaulting  
↓  
Source Item Retrieval  
↓  
Destination Schema Retrieval  
↓  
Match Determination (quick match or settings.match)  
↓  
Create/Update Item(s)  
↓  
Attachment Handling  
↓  
Output Assembly & Return

## 7.2 Triggers & Entry Points

### Manual Trigger
- Shown in UI with:
  - `sourceSiteUrl`, `sourceListName`, `sourceItemId` (optional)
  - `destSiteUrl`, `destListName`
  - `map` (JSON array)
  - `operation` (create/update/upsert)
  - `destMatchColumn` + `destMatchValue` (optional)
  - `attachmentMode` (choice)
  - `mapOnly` (boolean)
  - `settings` (JSON, optional)

### For a selected item/document
- Context object provides `sourceSiteUrl`, `sourceListName`, `sourceItemId` automatically.

## 7.3 Core Stages & Actions

### Stage 1: Input Validation & Defaulting
- Validate URLs, list names, JSON structure for map and settings.
- Defaults:
  - `operation=upsert`
  - `attachmentMode=none`
  - `mapOnly=true`
- Resolve `sourceItemId` from context if blank.

### Stage 2: Source Item Retrieval
- HTTP GET: `/items({sourceItemId})` with `$select=*` and `$expand=AttachmentFiles,FieldValuesAsText` if attachments may be needed.
- Store as `srcItem`.

### Stage 3: Destination Schema Retrieval
- HTTP GET `/fields?$select=InternalName,TypeAsString,ReadOnlyField,Hidden,LookupList,LookupField,AllowMultipleValues`
- Build a dictionary `destFields` keyed by InternalName → type metadata.

### Stage 4: Match Determination
- If `destMatchColumn` + `destMatchValue` present → build quick `settings.match`.
- Else use provided `settings.match`.
- Execute:
  - simple: CAML query (preferred for large lists).
  - odata: `$filter` directly.
  - caml: raw `<View>` XML.
- Gather `matchedIds` array.

### Stage 5: Operation Handling
- `create`: create new item(s) unconditionally.
- `update`: if `matchedIds` empty → fail with “No match found”.
- `upsert`: update if matches found; else create.

## 7.4 Mapping Engine

**Input:** `map` array (objects with `source`, `dest`, optional `default`, `when`, `transform`, `typeHint`)

**Processing loop:**
1. If `mapOnly=false`, add all dest fields that exist in both lists (except hidden/read-only).
2. For each mapping:
   - Pull `srcValue` from `srcItem`.
   - If `when=empty` and `srcValue` is empty → set `value=default`.
   - If `when=always` → set `value=default` regardless.
   - Apply transforms in sequence:
     - `ensureUser`: POST `/ensureuser` → get ID.
     - `toUTC`: convert to ISO 8601 Z.
     - `stripHTML`: regex/HTML removal.
     - `lookupByText`: resolve against lookup list by display text.
   - Type-cast to SharePoint format:
     - Multi fields → `;#`-delimited strings.
     - Person/Lookup IDs as strings.
   - Skip if dest field doesn’t exist; warn.
3. Output: `formValues[]` array for `ValidateUpdateListItem`.

## 7.5 Write Operations

**Create**
- POST `/items` with minimal body (`{}`) → returns Id.
- Then POST `/items({id})/validateupdatelistitem` with `formValues`.

**Update**
- POST `/items({id})/validateupdatelistitem` for each matched ID.
- If bulk, loop through all `matchedIds`; else use first.

## 7.6 Attachment Handling

Inputs: `attachmentMode`, `srcItem.Attachments`, `destItem.Attachments`

| Mode      | Behavior |
|-----------|----------|
| none      | Skip entirely |
| append    | Add source files not in dest |
| overwrite | Replace same-named dest files |
| replace   | Remove all dest files, then add all source files |

Process:
1. List dest attachments.
2. Compare with source list by filename.
3. Download → upload (binary streams).
4. Errors → warnings array.

## 7.7 Output Assembly

```json
{
  "operation": "upsert",
  "bulk": false,
  "quickMatch": { "column": "Title", "value": "Task-001" },
  "matchedCount": 1,
  "createdIds": [],
  "updatedIds": [42],
  "warnings": ["Owner not found, skipped"],
  "errors": []
}
```

- Return to caller; optionally append to `COPYITEM_RUNLOG_LIST` if set.

## 7.8 Error Handling Flow
- Fatal errors: Invalid JSON, missing list, no permission → terminate.
- Non-fatal warnings: Missing fields, failed transforms, skipped attachments → log and continue.
- Retries: Automatic on HTTP 429/5xx with exponential backoff.

## 7.9 Security & Auth
- All HTTP calls use connection reference.
- Service account principle of least privilege.
- No sensitive tokens/headers written to logs.

## 7.10 Extensibility Hooks
- Transforms: Centralized switch block; new ones can be added without breaking mapping.
- Settings schema: Versioned; extra keys ignored by MVP.
- Operations: Adding new ops (e.g., “delete”) fits in stage 5 with minimal change.
